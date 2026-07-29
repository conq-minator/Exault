"""
ExcelPlorer — Schema Models

All dataclass models used throughout the application.
These are the single source of truth for data shapes.

Classes:
    ValidationRule — A single data validation rule on a column
    MergedRange    — A merged cell range with its resolved value
    ColumnSchema   — Full metadata for a single column
    SheetSchema    — Full metadata for a single worksheet
    WorkbookSchema — Top-level schema for an entire workbook
    AnalysisResult — Wraps WorkbookSchema with analysis metadata
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# ─── Validation Rule ────────────────────────────────────────────────────────


@dataclass
class ValidationRule:
    """
    Represents a data validation rule applied to a column.

    Attributes:
        type: Validation type — 'list', 'whole', 'decimal', 'date',
              'time', 'textLength', 'custom', or 'none'.
        operator: Comparison operator — 'between', 'equal', 'lessThan', etc.
        formula1: First formula/value (e.g., list reference or min value).
        formula2: Second formula/value (e.g., max value for 'between').
        allowed_values: Resolved list of allowed values (for 'list' type).
        allow_blank: Whether blank values are permitted.
        show_error: Whether an error alert is shown on invalid input.
        error_title: Title of the error alert.
        error_message: Body of the error alert.
    """
    type: str = "none"
    operator: Optional[str] = None
    formula1: Optional[str] = None
    formula2: Optional[str] = None
    allowed_values: list[str] = field(default_factory=list)
    allow_blank: bool = True
    show_error: bool = False
    error_title: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result = {"type": self.type}
        if self.operator:
            result["operator"] = self.operator
        if self.formula1:
            result["formula1"] = self.formula1
        if self.formula2:
            result["formula2"] = self.formula2
        if self.allowed_values:
            result["allowed_values"] = self.allowed_values
        result["allow_blank"] = self.allow_blank
        if self.show_error:
            result["show_error"] = True
            if self.error_title:
                result["error_title"] = self.error_title
            if self.error_message:
                result["error_message"] = self.error_message
        return result


# ─── Merged Range ───────────────────────────────────────────────────────────


@dataclass
class MergedRange:
    """
    Represents a merged cell range.

    Attributes:
        start_row: Top row of the merge (1-indexed).
        start_col: Left column of the merge (1-indexed).
        end_row: Bottom row of the merge (1-indexed).
        end_col: Right column of the merge (1-indexed).
        value: The value held in the top-left cell.
        range_string: Original range string, e.g., "A1:C3".
    """
    start_row: int = 0
    start_col: int = 0
    end_row: int = 0
    end_col: int = 0
    value: Any = None
    range_string: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "start_row": self.start_row,
            "start_col": self.start_col,
            "end_row": self.end_row,
            "end_col": self.end_col,
            "value": self.value,
            "range_string": self.range_string,
        }


# ─── Column Schema ──────────────────────────────────────────────────────────


@dataclass
class ColumnSchema:
    """
    Full metadata for a single column in a worksheet.

    Attributes:
        name: Column header text (exactly as it appears in the template).
        index: Column index (1-indexed, matching openpyxl convention).
        letter: Column letter (A, B, C, ..., AA, AB, ...).
        data_type: Inferred data type — 'string', 'integer', 'float',
                   'date', 'boolean', 'url', 'email', or 'unknown'.
        is_required: Whether this column is mandatory.
        is_hidden: Whether the column is hidden in the template.
        allowed_values: Resolved dropdown values (empty if no list validation).
        max_length: Maximum allowed field length (None if no limit).
        sample_values: Sample data values from existing rows.
        validation_rules: List of validation rules applied to this column.
        has_formula: Whether cells in this column contain formulas.
        comment: Cell comment/note on the header cell (if any).
        fill_color: Header cell fill color (hex, for required-field detection).
    """
    name: str = ""
    index: int = 0
    letter: str = ""
    data_type: str = "string"
    is_required: bool = False
    is_hidden: bool = False
    allowed_values: list[str] = field(default_factory=list)
    max_length: Optional[int] = None
    sample_values: list[Any] = field(default_factory=list)
    validation_rules: list[ValidationRule] = field(default_factory=list)
    has_formula: bool = False
    comment: Optional[str] = None
    fill_color: Optional[str] = None
    instructions: list[str] = field(default_factory=list)
    comment: Optional[str] = None
    fill_color: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result: dict[str, Any] = {
            "name": self.name,
            "index": self.index,
            "letter": self.letter,
            "data_type": self.data_type,
            "is_required": self.is_required,
        }
        if self.is_hidden:
            result["is_hidden"] = True
        if self.allowed_values:
            result["allowed_values"] = self.allowed_values
        if self.max_length is not None:
            result["max_length"] = self.max_length
        if self.sample_values:
            # Convert non-serializable values to strings
            result["sample_values"] = [
                str(v) if not isinstance(v, (str, int, float, bool, type(None)))
                else v
                for v in self.sample_values
            ]
        if self.validation_rules:
            result["validation_rules"] = [r.to_dict() for r in self.validation_rules]
        if self.has_formula:
            result["has_formula"] = True
        if self.comment:
            result["comment"] = self.comment
        if self.fill_color:
            result["fill_color"] = self.fill_color
        if self.instructions:
            result["instructions"] = self.instructions
        return result


# ─── Sheet Schema ───────────────────────────────────────────────────────────


@dataclass
class SheetSchema:
    """
    Full metadata for a single worksheet.

    Attributes:
        name: Sheet name (exactly as it appears in the workbook).
        index: Sheet index (0-based).
        is_visible: Whether the sheet is visible (not hidden).
        is_data_sheet: Whether this sheet contains data entry columns
                       (vs. instructions/reference sheets).
        header_row: The 1-indexed row number containing column headers.
        columns: List of ColumnSchema objects for each detected column.
        merged_ranges: List of merged cell ranges in this sheet.
        named_ranges: Named ranges scoped to this sheet.
        formulas: List of cells containing formulas (as {"cell": "A1", "formula": "=..."}).
        row_count: Total number of rows with data.
        col_count: Total number of columns with data.
    """
    name: str = ""
    index: int = 0
    is_visible: bool = True
    is_data_sheet: bool = True
    header_row: int = 1
    columns: list[ColumnSchema] = field(default_factory=list)
    merged_ranges: list[MergedRange] = field(default_factory=list)
    named_ranges: list[dict[str, str]] = field(default_factory=list)
    formulas: list[dict[str, str]] = field(default_factory=list)
    row_count: int = 0
    col_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result: dict[str, Any] = {
            "name": self.name,
            "index": self.index,
            "is_visible": self.is_visible,
            "is_data_sheet": self.is_data_sheet,
            "header_row": self.header_row,
            "columns": [c.to_dict() for c in self.columns],
            "row_count": self.row_count,
            "col_count": self.col_count,
        }
        if self.merged_ranges:
            result["merged_ranges"] = [m.to_dict() for m in self.merged_ranges]
        if self.named_ranges:
            result["named_ranges"] = self.named_ranges
        if self.formulas:
            result["formulas"] = self.formulas
        return result


# ─── Workbook Schema ────────────────────────────────────────────────────────


@dataclass
class WorkbookSchema:
    """
    Top-level schema for an entire workbook.

    This is the primary data structure passed between all pipeline stages.

    Attributes:
        filename: Original uploaded filename.
        file_size: File size in bytes.
        file_extension: File extension (.xlsx or .xls).
        sheet_count: Total number of sheets.
        sheets: List of SheetSchema objects.
        named_ranges: Workbook-scoped named ranges.
        detected_marketplace: Name of the detected marketplace plugin (if any).
        analysis_timestamp: When the analysis was performed.
    """
    filename: str = ""
    file_size: int = 0
    file_extension: str = ".xlsx"
    sheet_count: int = 0
    sheets: list[SheetSchema] = field(default_factory=list)
    global_rules: str = ""
    named_ranges: list[dict[str, str]] = field(default_factory=list)
    detected_marketplace: Optional[str] = None
    analysis_timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        result: dict[str, Any] = {
            "filename": self.filename,
            "file_size": self.file_size,
            "file_extension": self.file_extension,
            "sheet_count": self.sheet_count,
            "sheets": [s.to_dict() for s in self.sheets],
            "named_ranges": self.named_ranges,
            "analysis_timestamp": self.analysis_timestamp,
        }
        if self.detected_marketplace:
            result["detected_marketplace"] = self.detected_marketplace
        if self.global_rules:
            result["global_rules"] = self.global_rules
        return result

    def get_data_sheets(self) -> list["SheetSchema"]:
        """Return only sheets marked as data entry sheets."""
        return [s for s in self.sheets if s.is_data_sheet and s.is_visible]

    def get_all_columns(self) -> list["ColumnSchema"]:
        """Return all columns across all data sheets."""
        columns = []
        for sheet in self.get_data_sheets():
            columns.extend(sheet.columns)
        return columns


# ─── Analysis Result ────────────────────────────────────────────────────────


@dataclass
class AnalysisResult:
    """
    Wraps a WorkbookSchema with analysis metadata.

    Attributes:
        schema: The complete workbook schema.
        duration_ms: How long the analysis took in milliseconds.
        warnings: Non-fatal warnings encountered during analysis.
        detected_plugin: Name of the matched marketplace plugin (if any).
        plugin_confidence: Confidence score of plugin detection (0.0–1.0).
    """
    schema: WorkbookSchema = field(default_factory=WorkbookSchema)
    duration_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)
    detected_plugin: Optional[str] = None
    plugin_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "schema": self.schema.to_dict(),
            "duration_ms": round(self.duration_ms, 2),
            "warnings": self.warnings,
            "detected_plugin": self.detected_plugin,
            "plugin_confidence": round(self.plugin_confidence, 3),
        }
