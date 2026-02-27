"""Unit tests for DSL validators."""

from __future__ import annotations

import pytest

from src.application.dsl_functions.validators import ValidationError, validate_data


# ── Test schema fixture ──────────────────────────────────────────────

SCHEMA = {
    "dataSource": {
        "fields": [
            {"id": "name", "required": True},
            {"id": "code", "validations": [
                {"rule": "pattern", "value": "^[A-Z]{3}$", "message": "Must be 3 uppercase letters"},
            ]},
            {"id": "uf", "validations": [
                {"rule": "minLength", "value": 2},
                {"rule": "maxLength", "value": 2},
            ]},
            {"id": "rate", "validations": [
                {"rule": "min", "value": 0},
                {"rule": "max", "value": 100},
            ]},
            {"id": "optional_field"},
        ],
    },
}


# ── required ─────────────────────────────────────────────────────────


class TestRequired:
    def test_create_missing_required_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_data({}, SCHEMA, context="create")
        errors = exc_info.value.errors
        assert any(e["field"] == "name" and e["rule"] == "required" for e in errors)

    def test_create_empty_string_required_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_data({"name": ""}, SCHEMA, context="create")
        errors = exc_info.value.errors
        assert any(e["field"] == "name" for e in errors)

    def test_create_with_required_passes(self):
        validate_data({"name": "Test"}, SCHEMA, context="create")

    def test_update_missing_required_passes(self):
        """In UPDATE context, missing required fields are OK (partial update)."""
        validate_data({"code": "ABC"}, SCHEMA, context="update")

    def test_update_present_but_empty_required_raises(self):
        """If required field IS present but empty in update, still reject."""
        with pytest.raises(ValidationError):
            validate_data({"name": "  "}, SCHEMA, context="update")


# ── pattern ──────────────────────────────────────────────────────────


class TestPattern:
    def test_valid_pattern_passes(self):
        validate_data({"name": "T", "code": "ABC"}, SCHEMA, context="create")

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_data({"name": "T", "code": "abc"}, SCHEMA, context="create")
        err = exc_info.value.errors[0]
        assert err["rule"] == "pattern"
        assert "3 uppercase" in err["message"]

    def test_pattern_skipped_if_field_absent_in_update(self):
        validate_data({"name": "T"}, SCHEMA, context="update")


# ── minLength / maxLength ────────────────────────────────────────────


class TestLength:
    def test_valid_length_passes(self):
        validate_data({"name": "T", "uf": "SP"}, SCHEMA, context="create")

    def test_too_short_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_data({"name": "T", "uf": "S"}, SCHEMA, context="create")
        assert exc_info.value.errors[0]["rule"] == "minLength"

    def test_too_long_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_data({"name": "T", "uf": "SPX"}, SCHEMA, context="create")
        assert exc_info.value.errors[0]["rule"] == "maxLength"


# ── min / max ────────────────────────────────────────────────────────


class TestNumericRange:
    def test_valid_range_passes(self):
        validate_data({"name": "T", "rate": 50}, SCHEMA, context="create")

    def test_below_min_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_data({"name": "T", "rate": -1}, SCHEMA, context="create")
        assert exc_info.value.errors[0]["rule"] == "min"

    def test_above_max_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_data({"name": "T", "rate": 101}, SCHEMA, context="create")
        assert exc_info.value.errors[0]["rule"] == "max"

    def test_boundary_values_pass(self):
        validate_data({"name": "T", "rate": 0}, SCHEMA, context="create")
        validate_data({"name": "T", "rate": 100}, SCHEMA, context="create")


# ── Multiple errors ──────────────────────────────────────────────────


class TestMultipleErrors:
    def test_collects_all_errors(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_data(
                {"code": "abc", "uf": "SPX", "rate": 200},
                SCHEMA,
                context="create",
            )
        errors = exc_info.value.errors
        fields = {e["field"] for e in errors}
        assert "name" in fields      # required
        assert "code" in fields      # pattern
        assert "uf" in fields        # maxLength
        assert "rate" in fields      # max
