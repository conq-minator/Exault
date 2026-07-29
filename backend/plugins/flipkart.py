"""
ExcelPlorer — Flipkart Plugin

Implements marketplace-specific rules and AI instructions for Flipkart templates.
"""

from typing import Any, Callable
from backend.plugins.base import MarketplacePlugin
from backend.core.schema import WorkbookSchema
from backend.core.validator import ValidationIssue


class FlipkartPlugin(MarketplacePlugin):
    
    @property
    def name(self) -> str:
        return "Flipkart"
        
    def detect(self, schema: WorkbookSchema) -> float:
        """
        Detect if this is a Flipkart template.
        Typically, Flipkart templates have sheets named 'Vertical_Name' or contain
        columns like 'FSN', 'SuperCom Net', etc.
        """
        score = 0.0
        
        # Check filename
        if "flipkart" in schema.filename.lower():
            score += 0.3
            
        # Check column names
        all_cols = schema.get_all_columns()
        col_names = [c.name.lower() for c in all_cols]
        
        flipkart_keywords = [
            "brand", "brand approval", "fsn", "supercom net", 
            "hsn", "tax code", "mrp", "selling price"
        ]
        
        matches = sum(1 for k in flipkart_keywords if k in col_names)
        if matches > 3:
            score += 0.5
            
        return min(1.0, score)

    def get_prompt_additions(self, schema: WorkbookSchema) -> str:
        """
        Extra instructions for the AI when generating Flipkart JSON.
        """
        return (
            "FLIPKART SPECIFIC INSTRUCTIONS:\n"
            "- If 'Brand Approval' requires a value, and the brand is not generic, set it to 'Yes'.\n"
            "- Ensure that 'MRP' is strictly greater than 'Selling Price'.\n"
            "- Flipkart expects text in Sentence case for descriptions.\n"
        )

    def get_validation_rules(self, schema: WorkbookSchema) -> list[Callable[[dict, int], list[ValidationIssue]]]:
        """
        Flipkart specific validation rules.
        """
        def rule_brand_approval(row: dict, index: int) -> list[ValidationIssue]:
            issues = []
            # Find the actual keys matching our concepts (case-insensitive)
            brand_key = next((k for k in row.keys() if k.lower() == "brand"), None)
            approval_key = next((k for k in row.keys() if "brand approval" in k.lower()), None)
            
            if brand_key and approval_key:
                brand_val = str(row.get(brand_key, "")).strip().lower()
                approval_val = str(row.get(approval_key, "")).strip().lower()
                
                if brand_val and brand_val != "generic":
                    # If there's a specific brand, approval should be 'yes' or similar
                    if approval_val not in ("yes", "y", "true"):
                        issues.append(ValidationIssue(
                            severity="WARNING",
                            item_index=index,
                            field=approval_key,
                            message=f"Brand '{row[brand_key]}' usually requires Brand Approval to be 'Yes'."
                        ))
            return issues
            
        def rule_mrp_vs_sp(row: dict, index: int) -> list[ValidationIssue]:
            issues = []
            mrp_key = next((k for k in row.keys() if "mrp" in k.lower()), None)
            sp_key = next((k for k in row.keys() if "selling price" in k.lower()), None)
            
            if mrp_key and sp_key:
                try:
                    mrp = float(row.get(mrp_key, 0))
                    sp = float(row.get(sp_key, 0))
                    if mrp < sp:
                        issues.append(ValidationIssue(
                            severity="ERROR",
                            item_index=index,
                            field=mrp_key,
                            message=f"MRP ({mrp}) cannot be less than Selling Price ({sp})."
                        ))
                except (ValueError, TypeError):
                    pass # Handled by core type validation
            return issues
            
        return [rule_brand_approval, rule_mrp_vs_sp]

    def apply_auto_corrections(self, item: dict[str, Any], schema: WorkbookSchema) -> list[ValidationIssue]:
        """
        Apply Flipkart specific corrections.
        """
        issues = []
        # Example: Flipkart often expects 'SuperCom Net' to be trimmed or formatted specifically,
        # but for this demo, we'll force 'Brand' to Title Case if it exists and isn't 'generic'
        brand_key = next((k for k in item.keys() if k.lower() == "brand"), None)
        if brand_key:
            val = str(item.get(brand_key, ""))
            if val and val.lower() != "generic" and val != val.title():
                item[brand_key] = val.title()
                issues.append(ValidationIssue(
                    severity="INFO",
                    item_index=0, # Will be set by validator engine
                    field=brand_key,
                    message="Converted brand name to Title Case per Flipkart conventions."
                ))
                
        return issues
