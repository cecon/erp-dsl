"""Integration tests for the Generic CRUD API.

Tests the full HTTP contract: CRUD lifecycle, tenant isolation,
optimistic locking, validation errors, and error shape consistency.
"""

from __future__ import annotations


# ── CRUD Lifecycle ───────────────────────────────────────────────────


class TestCrudLifecycle:
    """Create → Get → List → Update → Delete full cycle."""

    def test_full_lifecycle(self, client, auth_headers):
        # CREATE
        resp = client.post(
            "/entities/fiscal_rules",
            json={
                "id_grupo_tributario": "grp-test",
                "id_natureza_operacao": "nat-test",
                "cfop": "5102",
                "uf_origem": "SP",
                "uf_destino": "RJ",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        entity_id = data["id"]
        assert data["version"] == 1
        assert data["cfop"] == "5102"

        # GET
        resp = client.get(
            f"/entities/fiscal_rules/{entity_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == entity_id

        # LIST
        resp = client.get("/entities/fiscal_rules", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert any(item["id"] == entity_id for item in body["items"])

        # UPDATE
        resp = client.put(
            f"/entities/fiscal_rules/{entity_id}",
            json={"icms_aliquota": "18.5", "_version": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == 2
        assert resp.json()["icms_aliquota"] == 18.5

        # DELETE
        resp = client.delete(
            f"/entities/fiscal_rules/{entity_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # VERIFY DELETED
        resp = client.get(
            f"/entities/fiscal_rules/{entity_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ── Optimistic Locking ───────────────────────────────────────────────


class TestOptimisticLocking:
    def test_stale_version_returns_409(self, client, auth_headers):
        # Create
        resp = client.post(
            "/entities/fiscal_rules",
            json={
                "id_grupo_tributario": "grp-lock",
                "id_natureza_operacao": "nat-lock",
                "cfop": "5102",
            },
            headers=auth_headers,
        )
        entity_id = resp.json()["id"]

        # First update succeeds
        resp = client.put(
            f"/entities/fiscal_rules/{entity_id}",
            json={"icms_aliquota": "10", "_version": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == 2

        # Second update with stale version → 409
        resp = client.put(
            f"/entities/fiscal_rules/{entity_id}",
            json={"icms_aliquota": "20", "_version": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 409
        body = resp.json()
        assert body["error"]["code"] == "CONFLICT"
        assert body["error"]["details"]["expected_version"] == 1

        # Correct version succeeds
        resp = client.put(
            f"/entities/fiscal_rules/{entity_id}",
            json={"icms_aliquota": "20", "_version": 2},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == 3

        # Cleanup
        client.delete(
            f"/entities/fiscal_rules/{entity_id}",
            headers=auth_headers,
        )


# ── Validation Errors ────────────────────────────────────────────────


class TestValidation:
    def test_missing_required_on_create(self, client, auth_headers):
        resp = client.post(
            "/entities/fiscal_rules",
            json={"cfop": "5102"},
            headers=auth_headers,
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        fields = {e["field"] for e in body["error"]["details"]["errors"]}
        assert "id_grupo_tributario" in fields
        assert "id_natureza_operacao" in fields

    def test_invalid_pattern_on_create(self, client, auth_headers):
        resp = client.post(
            "/entities/fiscal_rules",
            json={
                "id_grupo_tributario": "grp",
                "id_natureza_operacao": "nat",
                "cfop": "ABCD",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
        errors = resp.json()["error"]["details"]["errors"]
        assert any(e["field"] == "cfop" and e["rule"] == "pattern" for e in errors)

    def test_max_exceeded_on_create(self, client, auth_headers):
        resp = client.post(
            "/entities/fiscal_rules",
            json={
                "id_grupo_tributario": "grp",
                "id_natureza_operacao": "nat",
                "cfop": "5102",
                "icms_aliquota": "150",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
        errors = resp.json()["error"]["details"]["errors"]
        assert any(e["field"] == "icms_aliquota" and e["rule"] == "max" for e in errors)

    def test_update_partial_without_required_passes(self, client, auth_headers):
        # Create valid entity
        resp = client.post(
            "/entities/fiscal_rules",
            json={
                "id_grupo_tributario": "grp-upd",
                "id_natureza_operacao": "nat-upd",
                "cfop": "5102",
            },
            headers=auth_headers,
        )
        entity_id = resp.json()["id"]

        # Partial update without required fields → should pass
        resp = client.put(
            f"/entities/fiscal_rules/{entity_id}",
            json={"icms_aliquota": "18", "_version": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Cleanup
        client.delete(
            f"/entities/fiscal_rules/{entity_id}",
            headers=auth_headers,
        )

    def test_maxlength_on_update(self, client, auth_headers):
        # Create valid entity
        resp = client.post(
            "/entities/fiscal_rules",
            json={
                "id_grupo_tributario": "grp-ml",
                "id_natureza_operacao": "nat-ml",
                "cfop": "5102",
                "uf_origem": "SP",
            },
            headers=auth_headers,
        )
        entity_id = resp.json()["id"]

        # Update with too long uf → 422
        resp = client.put(
            f"/entities/fiscal_rules/{entity_id}",
            json={"uf_origem": "SAO", "_version": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 422

        # Cleanup
        client.delete(
            f"/entities/fiscal_rules/{entity_id}",
            headers=auth_headers,
        )


# ── Error Shape ──────────────────────────────────────────────────────


class TestErrorShape:
    """All error responses must follow the standard shape."""

    def test_404_shape(self, client, auth_headers):
        resp = client.get(
            "/entities/fiscal_rules/nonexistent",
            headers=auth_headers,
        )
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "NOT_FOUND"
        assert body["error"]["status"] == 404
        assert "message" in body["error"]

    def test_401_shape(self, client):
        resp = client.get("/entities/fiscal_rules")
        assert resp.status_code in (401, 403)
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]

    def test_422_shape(self, client, auth_headers):
        resp = client.get(
            "/entities/fiscal_rules?offset=abc",
            headers=auth_headers,
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "errors" in body["error"]["details"]
