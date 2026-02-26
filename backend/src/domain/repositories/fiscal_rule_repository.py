"""Abstract repository interface for Fiscal Rules (domain Protocol)."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.entities.fiscal_rule import FiscalRule


class FiscalRuleRepository(Protocol):
    """Port for persisting and querying fiscal rules."""

    def get_by_id(self, rule_id: str, tenant_id: str) -> Optional[FiscalRule]: ...

    def list_all(
        self, tenant_id: str, limit: int = 50, offset: int = 0
    ) -> list[FiscalRule]: ...

    def save(self, rule: FiscalRule) -> FiscalRule: ...

    def update(self, rule: FiscalRule) -> FiscalRule: ...

    def delete(self, rule_id: str, tenant_id: str) -> bool: ...
