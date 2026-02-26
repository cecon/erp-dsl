"""Application port re-exporting the domain FiscalRuleRepository Protocol."""

from src.domain.repositories.fiscal_rule_repository import FiscalRuleRepository

# Re-export for use-case imports
FiscalRuleRepositoryPort = FiscalRuleRepository

__all__ = ["FiscalRuleRepositoryPort"]
