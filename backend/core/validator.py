"""
ExcelPlorer — Validation Engine

Validates AI-generated JSON data against the rules and constraints
extracted in the WorkbookSchema. Attempts auto-corrections where possible.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.core.schema import WorkbookSchema, ColumnSchema

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a single validation error or auto-correction."""
    severity: str  # "ERROR", "WARNING", or "INFO"
    item_index: int  # The index of the item in the JSON array (0-based)
    field: str
    message: str


@dataclass
class ValidationReport:
    """The complete result of a validation run."""
    is_valid: bool = False
    corrected_data: list[dict[str, Any]] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    item_statuses: list[dict[str, bool]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "corrected_data": self.corrected_data,
            "item_statuses": self.item_statuses,
            "issues": [
                {
                    "severity": i.severity,
                    "item_index": i.item_index,
                    "field": i.field,
                    "message": i.message
                }
                for i in self.issues
            ]
        }


class ValidationEngine:
    """
    Validates and auto-corrects parsed JSON data against a WorkbookSchema.
    """

    def validate(self, data: list[dict[str, Any]], schema: WorkbookSchema) -> ValidationReport:
        """
        Run the validation and auto-correction pipeline.
        
        Args:
            data: List of dictionaries (parsed JSON).
            schema: The WorkbookSchema to validate against.
            
        Returns:
            A ValidationReport with the corrected data and issues found.
        """
        report = ValidationReport(corrected_data=[])
        
        columns = schema.get_all_columns()
        col_map = {c.name: c for c in columns if not c.is_hidden}

        has_errors = False
        
        # Load plugin if marketplace detected
        plugin = None
        if schema.detected_marketplace:
            from backend.plugins.registry import PluginRegistry
            plugin = PluginRegistry.get_plugin(schema.detected_marketplace)

        for idx, item in enumerate(data):
            corrected_item = {}
            item_has_errors = False
            
            # Plugin auto-corrections (runs before individual field checks)
            if plugin:
                plugin_issues = plugin.apply_auto_corrections(item, schema)
                for issue in plugin_issues:
                    issue.item_index = idx
                    report.issues.append(issue)
            
            # 1. Check for unknown fields
            for key in item.keys():
                if key not in col_map:
                    report.issues.append(ValidationIssue(
                        severity="WARNING",
                        item_index=idx,
                        field=key,
                        message=f"Unknown field '{key}' is not in the schema and will be ignored."
                    ))

            # 2. Process schema fields
            for col_name, col_schema in col_map.items():
                val = item.get(col_name)

                # Skip empty/missing values unless required
                if val is None or str(val).strip() == "":
                    if col_schema.is_required:
                        report.issues.append(ValidationIssue(
                            severity="ERROR",
                            item_index=idx,
                            field=col_name,
                            message=f"Missing required field."
                        ))
                        has_errors = True
                        item_has_errors = True
                    # Fill with empty string for structure consistency
                    corrected_item[col_name] = ""
                    continue

                # Auto-correct and validate
                val = self._auto_correct(val, col_schema, idx, report)
                is_valid = self._validate_constraints(val, col_schema, idx, report)
                
                if not is_valid:
                    has_errors = True
                    item_has_errors = True
                    
                corrected_item[col_name] = val
                
            # Plugin specific validation rules
            if plugin:
                rules = plugin.get_validation_rules(schema)
                for rule_func in rules:
                    issues = rule_func(corrected_item, idx)
                    if issues:
                        report.issues.extend(issues)
                        for issue in issues:
                            if issue.severity == "ERROR":
                                has_errors = True
                                item_has_errors = True

            report.corrected_data.append(corrected_item)
            report.item_statuses.append({"is_valid": not item_has_errors})

        report.is_valid = not has_errors
        return report

    def _auto_correct(self, value: Any, col: ColumnSchema, idx: int, report: ValidationReport) -> Any:
        """Apply auto-corrections like trimming, case normalization, and type casting."""
        orig_value = value

        # 1. String trimming
        if isinstance(value, str):
            value = value.strip()
            if value != orig_value:
                # We don't spam INFO logs for basic whitespace trimming to keep reports clean
                pass

        # 2. Boolean normalization
        if col.data_type == "boolean":
            if str(value).lower() in ("true", "yes", "1", "y"):
                value = "Yes"
            elif str(value).lower() in ("false", "no", "0", "n"):
                value = "No"
                
            if value != orig_value:
                report.issues.append(ValidationIssue(
                    severity="INFO", item_index=idx, field=col.name,
                    message=f"Normalized boolean from '{orig_value}' to '{value}'."
                ))

        # 3. Numeric casting
        if col.data_type in ("integer", "float") and isinstance(value, str):
            try:
                if col.data_type == "integer":
                    value = int(float(value))  # Handle "42.0" -> 42
                else:
                    value = float(value)
                report.issues.append(ValidationIssue(
                    severity="INFO", item_index=idx, field=col.name,
                    message=f"Cast string '{orig_value}' to number."
                ))
            except ValueError:
                pass # Will be caught by constraints validation

        # 4. Dropdown case-insensitive normalization
        if col.allowed_values and isinstance(value, str):
            # Strict match first
            if value not in col.allowed_values:
                # Case-insensitive match
                lower_map = {v.lower(): v for v in col.allowed_values}
                if value.lower() in lower_map:
                    value = lower_map[value.lower()]
                    report.issues.append(ValidationIssue(
                        severity="INFO", item_index=idx, field=col.name,
                        message=f"Corrected case from '{orig_value}' to '{value}'."
                    ))

        return value

    def _validate_constraints(self, value: Any, col: ColumnSchema, idx: int, report: ValidationReport) -> bool:
        """Check values against length limits, types, and allowed values."""
        is_valid = True

        # 1. Allowed values (Dropdown)
        if col.allowed_values:
            if str(value) not in col.allowed_values:
                report.issues.append(ValidationIssue(
                    severity="ERROR", item_index=idx, field=col.name,
                    message=f"Value '{value}' is not in the allowed list."
                ))
                is_valid = False

        # 2. Max length
        if col.max_length and isinstance(value, str):
            if len(value) > col.max_length:
                report.issues.append(ValidationIssue(
                    severity="ERROR", item_index=idx, field=col.name,
                    message=f"Exceeds max length of {col.max_length} characters (currently {len(value)})."
                ))
                is_valid = False

        # 3. Type checks (basic)
        if col.data_type == "integer" and not isinstance(value, int):
            report.issues.append(ValidationIssue(
                severity="ERROR", item_index=idx, field=col.name,
                message=f"Expected an integer, got {type(value).__name__}."
            ))
            is_valid = False
            
        elif col.data_type == "float" and not isinstance(value, (int, float)):
            report.issues.append(ValidationIssue(
                severity="ERROR", item_index=idx, field=col.name,
                message=f"Expected a number, got {type(value).__name__}."
            ))
            is_valid = False

        return is_valid
