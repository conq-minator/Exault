# ExcelPlorer Plugin Guide

ExcelPlorer uses a dynamic plugin architecture to adapt its behavior to specific e-commerce marketplaces (like Flipkart, Amazon, Meesho).

## Creating a Marketplace Plugin

1. Create a new Python file in `backend/plugins/` (e.g., `etsy.py`).
2. Import `MarketplacePlugin` from `backend.plugins.base`.
3. Create a class that inherits from `MarketplacePlugin`.
4. Implement the required methods.

```python
from backend.plugins.base import MarketplacePlugin
from backend.core.schema import WorkbookSchema
from backend.core.validator import ValidationIssue

class EtsyPlugin(MarketplacePlugin):
    @property
    def name(self) -> str:
        return "Etsy"
        
    def detect(self, schema: WorkbookSchema) -> float:
        # Return a confidence score between 0.0 and 1.0
        # Check schema.filename or schema.get_all_columns() for Etsy-specific patterns
        if "etsy" in schema.filename.lower():
            return 1.0
        return 0.0

    def get_prompt_additions(self, schema: WorkbookSchema) -> str:
        # Return string of extra instructions for the AI
        return "ETSY SPECIFIC: All titles must be under 140 chars."

    def get_validation_rules(self, schema: WorkbookSchema) -> list:
        # Return a list of custom validation functions
        def rule_etsy_title(row_data: dict, index: int):
            issues = []
            title_key = next((k for k in row_data.keys() if "title" in k.lower()), None)
            if title_key and len(str(row_data[title_key])) > 140:
                issues.append(ValidationIssue(
                    severity="ERROR", item_index=index, field=title_key,
                    message="Etsy titles cannot exceed 140 characters."
                ))
            return issues
        return [rule_etsy_title]

    def apply_auto_corrections(self, item: dict, schema: WorkbookSchema) -> list:
        # Apply corrections and return INFO ValidationIssues
        issues = []
        if "Tags" in item:
            val = str(item["Tags"])
            if "," in val:
                item["Tags"] = val.replace(",", " ")
                issues.append(ValidationIssue(
                    severity="INFO", item_index=0, field="Tags",
                    message="Replaced commas with spaces in Tags."
                ))
        return issues
```

## Creating an AI Adapter

To add support for a new AI provider (e.g., Anthropic Claude):

1. Create a new file in `backend/ai/` (e.g., `claude_adapter.py`).
2. Inherit from `AIAdapter` in `backend.ai.base`.
3. Implement `generate_json(self, prompt: str) -> str`.
