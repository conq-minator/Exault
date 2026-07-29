"""
ExcelPlorer — Amazon Plugin (Stub)
"""

from typing import Any, Callable
from backend.plugins.base import MarketplacePlugin
from backend.core.schema import WorkbookSchema
from backend.core.validator import ValidationIssue


class AmazonPlugin(MarketplacePlugin):
    
    @property
    def name(self) -> str:
        return "Amazon"
        
    def detect(self, schema: WorkbookSchema) -> float:
        """Detect Amazon templates (often contain 'TemplateType=Home', 'Version=', etc.)"""
        score = 0.0
        if "amazon" in schema.filename.lower():
            score += 0.3
        
        col_names = [c.name.lower() for c in schema.get_all_columns()]
        if "feed_product_type" in col_names or "item_sku" in col_names:
            score += 0.5
            
        return min(1.0, score)

    def get_prompt_additions(self, schema: WorkbookSchema) -> str:
        return "AMAZON SPECIFIC INSTRUCTIONS:\n- Follow Amazon's style guidelines strictly.\n"
