"""
ExcelPlorer — Meesho Plugin (Stub)
"""

from typing import Any, Callable
from backend.plugins.base import MarketplacePlugin
from backend.core.schema import WorkbookSchema
from backend.core.validator import ValidationIssue


class MeeshoPlugin(MarketplacePlugin):
    
    @property
    def name(self) -> str:
        return "Meesho"
        
    def detect(self, schema: WorkbookSchema) -> float:
        """Detect Meesho templates."""
        score = 0.0
        if "meesho" in schema.filename.lower():
            score += 0.3
        return score
