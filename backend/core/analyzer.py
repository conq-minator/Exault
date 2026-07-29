"""
ExcelPlorer — Workbook Analyzer

Core analysis engine that reads Excel workbooks and produces a
complete WorkbookSchema. Implements all FR-02 requirements.

Usage:
    analyzer = WorkbookAnalyzer()
    result = analyzer.analyze(Path("template.xlsx"))
    schema_dict = result.to_dict()

Design Principles:
    - Never hardcode field names — everything is discovered dynamically
    - Works with any Excel template from any marketplace
    - Handles both .xlsx (openpyxl) and .xls (xlrd) formats
    - All column names, types, and constraints come from the file itself
"""

import logging
import time
from pathlib import Path
from typing import Any, Optional

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.datavalidation import DataValidation

import config
from backend.core.schema import (
    AnalysisResult,
    ColumnSchema,
    MergedRange,
    SheetSchema,
    ValidationRule,
    WorkbookSchema,
)
from backend.plugins.registry import PluginRegistry
from backend.utils.excel_utils import (
    column_letter_to_index,
    detect_data_type,
    get_fill_color_hex,
    get_merged_cell_value,
    index_to_column_letter,
    parse_formula_reference,
    resolve_formula_reference,
)

logger = logging.getLogger(__name__)


# ─── Custom Exceptions ─────────────────────────────────────────────────────


class AnalysisError(Exception):
    """Raised when workbook analysis fails."""
    pass


# ─── Workbook Analyzer ─────────────────────────────────────────────────────


class WorkbookAnalyzer:
    """
    Analyzes Excel workbooks and produces a complete WorkbookSchema.

    Supports .xlsx files via openpyxl and .xls files via xlrd.
    Detects headers, columns, data validations, merged cells,
    hidden elements, formulas, named ranges, and comments.
    """

    def __init__(self):
        """Initialize the analyzer."""
        self._workbook = None
        self._warnings: list[str] = []

    def analyze(self, file_path: Path) -> AnalysisResult:
        """
        Analyze an Excel workbook and return a complete schema.

        Args:
            file_path: Path to the Excel file (.xlsx or .xls).

        Returns:
            AnalysisResult containing the WorkbookSchema and metadata.

        Raises:
            AnalysisError: If the file cannot be opened or analyzed.
            FileNotFoundError: If the file does not exist.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        start_time = time.perf_counter()
        self._warnings = []

        extension = file_path.suffix.lower()
        logger.info(f"Starting analysis of '{file_path.name}' ({extension})")

        try:
            if extension == ".xlsx":
                schema = self._analyze_xlsx(file_path)
            elif extension == ".xls":
                schema = self._analyze_xls(file_path)
            else:
                raise AnalysisError(
                    f"Unsupported file format: {extension}. "
                    "Only .xlsx and .xls files are supported."
                )
        except AnalysisError:
            raise
        except Exception as e:
            logger.error(f"Analysis failed for '{file_path.name}': {e}", exc_info=True)
            raise AnalysisError(f"Failed to analyze workbook: {e}") from e

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Populate file metadata
        schema.filename = file_path.name
        schema.file_size = file_path.stat().st_size
        schema.file_extension = extension
        
        # Detect Marketplace via Plugin Registry
        plugin = PluginRegistry.detect_marketplace(schema)
        if plugin:
            schema.detected_marketplace = plugin.name

        result = AnalysisResult(
            schema=schema,
            duration_ms=duration_ms,
            warnings=self._warnings,
        )

        logger.info(
            f"Analysis complete: {schema.sheet_count} sheets, "
            f"{sum(len(s.columns) for s in schema.sheets)} columns, "
            f"{duration_ms:.1f}ms"
        )

        return result

    # ─── .xlsx Analysis ─────────────────────────────────────────────────

    def _analyze_xlsx(self, file_path: Path) -> WorkbookSchema:
        """Analyze a .xlsx file using openpyxl."""
        try:
            # data_only=False to preserve formulas
            self._workbook = openpyxl.load_workbook(
                str(file_path),
                data_only=False,
                keep_links=False,
            )
        except Exception as e:
            raise AnalysisError(f"Cannot open .xlsx file: {e}") from e

        wb = self._workbook
        schema = WorkbookSchema(
            sheet_count=len(wb.sheetnames),
        )

        # Extract workbook-level named ranges
        schema.named_ranges = self._extract_named_ranges_xlsx(wb)

        # Analyze each sheet
        for idx, sheet_name in enumerate(wb.sheetnames):
            ws = wb[sheet_name]
            logger.debug(f"Analyzing sheet '{sheet_name}' ({idx + 1}/{len(wb.sheetnames)})")

            sheet_schema = self._analyze_sheet_xlsx(ws, idx)
            schema.sheets.append(sheet_schema)

            # Extract global rules from index sheets
            if not sheet_schema.is_data_sheet:
                name_lower = sheet_schema.name.lower()
                if any(x in name_lower for x in ["index", "instruction", "rule", "guideline"]):
                    texts = []
                    # Read column by column for better readability of rule tables
                    for col in ws.iter_cols(values_only=True):
                        col_vals = [str(c).strip() for c in col if c is not None and str(c).strip()]
                        if col_vals:
                            texts.append(" | ".join(col_vals))
                    if texts:
                        if schema.global_rules:
                            schema.global_rules += f"\n\n--- Sheet: {sheet_schema.name} ---\n" + "\n".join(texts)
                        else:
                            schema.global_rules = f"--- Sheet: {sheet_schema.name} ---\n" + "\n".join(texts)

        wb.close()
        self._workbook = None

        return schema

    def _analyze_sheet_xlsx(self, ws: Worksheet, index: int) -> SheetSchema:
        """Analyze a single .xlsx worksheet."""
        sheet = SheetSchema(
            name=ws.title,
            index=index,
            is_visible=(ws.sheet_state == "visible"),
            row_count=ws.max_row or 0,
            col_count=ws.max_column or 0,
        )

        # Detect merged cells
        sheet.merged_ranges = self._detect_merged_cells_xlsx(ws)

        # Detect header row
        header_row = self._detect_header_row(ws)
        sheet.header_row = header_row

        # Determine if this is a data sheet
        sheet.is_data_sheet = self._is_data_sheet(ws, header_row)

        if not sheet.is_data_sheet:
            logger.debug(f"Sheet '{ws.title}' classified as non-data sheet, skipping column extraction.")
            return sheet

        # Build a validation map for quick lookup: col_index → DataValidation
        validation_map = self._build_validation_map(ws, header_row)

        # Extract columns from the header row
        for col_idx in range(1, (ws.max_column or 0) + 1):
            header_cell = ws.cell(row=header_row, column=col_idx)
            header_value = header_cell.value

            # Skip columns with no header
            if header_value is None or str(header_value).strip() == "":
                continue

            column = self._extract_column_schema(
                ws=ws,
                col_idx=col_idx,
                header_cell=header_cell,
                header_row=header_row,
                validation_map=validation_map,
            )
            sheet.columns.append(column)

        # Extract formulas
        sheet.formulas = self._extract_formulas_xlsx(ws, header_row)

        return sheet

    # ─── Header Detection ───────────────────────────────────────────────

    def _detect_header_row(self, ws: Worksheet) -> int:
        """
        Detect the header row in a worksheet.

        Strategy:
        1. Scan the first 20 rows
        2. For each row, count the number of non-empty string cells
        3. The row with the most non-empty string cells is likely the header
        4. Tie-break: prefer the earlier row

        Args:
            ws: openpyxl Worksheet.

        Returns:
            1-indexed row number of the detected header row.
        """
        max_cols = ws.max_column or 1
        scan_rows = min(20, ws.max_row or 1)

        best_row = 1
        best_score = 0

        for row in range(1, scan_rows + 1):
            score = 0
            for col in range(1, max_cols + 1):
                cell = ws.cell(row=row, column=col)
                value = cell.value
                if value is not None and isinstance(value, str) and value.strip():
                    score += 1
                elif value is not None and not isinstance(value, str):
                    # Non-string non-empty (numbers in headers are less common)
                    score += 0.3

            if score > best_score:
                best_score = score
                best_row = row

        logger.debug(
            f"Header row detected at row {best_row} "
            f"(score: {best_score:.1f}) in sheet '{ws.title}'"
        )
        return best_row

    # ─── Data Sheet Detection ───────────────────────────────────────────

    def _is_data_sheet(self, ws: Worksheet, header_row: int) -> bool:
        """
        Determine if a sheet is a data entry sheet vs. instructions/reference.

        A data sheet typically has:
        - Multiple columns with headers
        - At least 3 column headers
        - Not named like "Instructions", "ReadMe", "Summary", etc.

        Args:
            ws: openpyxl Worksheet.
            header_row: Detected header row number.

        Returns:
            True if this appears to be a data entry sheet.
        """
        # Check sheet name for non-data indicators
        name_lower = ws.title.lower().strip()
        non_data_names = {
            "instructions", "readme", "read me", "summary", "info",
            "help", "notes", "guide", "about", "index", "toc",
            "table of contents", "changelog", "version",
            "summary sheet", "listing faq sheet", "image guidelines",
            "matchingattributes", "variantattributes",
            "template_version", "parent variant products",
        }
        if name_lower in non_data_names:
            return False

        # Partial-match exclusion for dropdown/reference sheets
        non_data_prefixes = (
            "dropdown", "faq", "image guide", "listing faq",
        )
        if any(name_lower.startswith(prefix) for prefix in non_data_prefixes):
            return False

        # Count non-empty header cells
        header_count = 0
        for col in range(1, (ws.max_column or 0) + 1):
            value = ws.cell(row=header_row, column=col).value
            if value is not None and str(value).strip():
                header_count += 1

        # Need at least 3 columns to be a data sheet
        return header_count >= 3

    # ─── Column Extraction ──────────────────────────────────────────────

    def _extract_column_schema(
        self,
        ws: Worksheet,
        col_idx: int,
        header_cell,
        header_row: int,
        validation_map: dict[int, list[DataValidation]],
    ) -> ColumnSchema:
        """Extract complete metadata for a single column."""
        header_value = str(header_cell.value).strip()

        column = ColumnSchema(
            name=header_value,
            index=col_idx,
            letter=index_to_column_letter(col_idx),
        )

        # Check if column is hidden
        col_letter = index_to_column_letter(col_idx)
        try:
            col_dim = ws.column_dimensions.get(col_letter)
            if col_dim and col_dim.hidden:
                column.is_hidden = True
        except (AttributeError, KeyError):
            pass

        # Extract fill color from header
        column.fill_color = get_fill_color_hex(header_cell)

        # Extract comment
        if header_cell.comment:
            column.comment = str(header_cell.comment.text).strip()

        # Extract instructions (rows up to 5 below header)
        instructions = []
        for i in range(1, 6):
            instr_row = header_row + i
            if instr_row > ws.max_row:
                break
            instr_val = ws.cell(row=instr_row, column=col_idx).value
            if instr_val is not None and str(instr_val).strip():
                instructions.append(str(instr_val).strip())
        if instructions:
            column.instructions = instructions

        # Sample data values
        column.sample_values = self._sample_column_data(
            ws, col_idx, header_row
        )

        # Read data validations for this column
        validations = validation_map.get(col_idx, [])
        for dv in validations:
            rule = self._parse_data_validation(dv, ws)
            column.validation_rules.append(rule)

            # Merge allowed values from all validation rules
            if rule.allowed_values:
                # Use the first non-empty allowed values list
                if not column.allowed_values:
                    column.allowed_values = rule.allowed_values

        # Infer data type from samples and validation
        column.data_type = self._infer_column_type(column)

        # Detect required status
        column.is_required = self._detect_required_status(
            column, header_cell, ws, header_row
        )

        # Detect max length
        column.max_length = self._detect_max_length(column)

        # Check for formulas in data cells
        column.has_formula = self._check_column_has_formula(
            ws, col_idx, header_row
        )

        return column

    # ─── Data Validation ────────────────────────────────────────────────

    def _build_validation_map(
        self, ws: Worksheet, header_row: int
    ) -> dict[int, list[DataValidation]]:
        """
        Build a mapping of column indices to their data validations.

        Args:
            ws: openpyxl Worksheet.
            header_row: Header row number (validations below this are data).

        Returns:
            Dict mapping column index → list of DataValidation objects.
        """
        validation_map: dict[int, list[DataValidation]] = {}

        for dv in ws.data_validations.dataValidation:
            # A single DataValidation can cover multiple cell ranges
            for cell_range in dv.sqref.ranges:
                for col in range(cell_range.min_col, cell_range.max_col + 1):
                    if col not in validation_map:
                        validation_map[col] = []
                    # Avoid duplicates
                    if dv not in validation_map[col]:
                        validation_map[col].append(dv)

        return validation_map

    def _parse_data_validation(
        self, dv: DataValidation, ws: Worksheet
    ) -> ValidationRule:
        """
        Convert an openpyxl DataValidation to our ValidationRule model.

        Handles both inline lists ("A,B,C") and formula references
        (=Sheet2!$A$1:$A$10) by resolving them to actual values.
        """
        rule = ValidationRule(
            type=dv.type or "none",
            operator=dv.operator,
            formula1=str(dv.formula1) if dv.formula1 else None,
            formula2=str(dv.formula2) if dv.formula2 else None,
            allow_blank=dv.allow_blank if dv.allow_blank is not None else True,
            show_error=bool(dv.showErrorMessage),
            error_title=dv.errorTitle,
            error_message=dv.error,
        )

        # Resolve allowed values for list-type validations
        if dv.type == "list" and dv.formula1:
            formula_str = str(dv.formula1)

            if "!" in formula_str or formula_str.startswith("="):
                # Formula reference — resolve from another sheet
                if self._workbook:
                    values = resolve_formula_reference(
                        formula_str, self._workbook
                    )
                    rule.allowed_values = values
            else:
                # Inline comma-separated list: "A,B,C" or '"A","B","C"'
                raw = formula_str.strip('"').strip("'")
                values = [v.strip().strip('"').strip("'") for v in raw.split(",")]
                rule.allowed_values = [v for v in values if v]

        return rule

    # ─── Sample Data ────────────────────────────────────────────────────

    def _sample_column_data(
        self, ws: Worksheet, col_idx: int, header_row: int
    ) -> list[Any]:
        """
        Collect sample non-empty values from a column.

        Reads rows below the header and collects the first N
        non-empty values (configured by MAX_SAMPLE_VALUES).

        Args:
            ws: openpyxl Worksheet.
            col_idx: Column index (1-indexed).
            header_row: Header row number.

        Returns:
            List of sample values (up to MAX_SAMPLE_VALUES).
        """
        samples = []
        max_samples = config.MAX_SAMPLE_VALUES
        max_scan = min((ws.max_row or header_row) + 1, header_row + 100)

        for row in range(header_row + 1, max_scan):
            value = ws.cell(row=row, column=col_idx).value
            if value is not None and str(value).strip():
                samples.append(value)
                if len(samples) >= max_samples:
                    break

        return samples

    # ─── Type Inference ─────────────────────────────────────────────────

    def _infer_column_type(self, column: ColumnSchema) -> str:
        """
        Infer the column data type from validation rules and sample data.

        Priority: validation rules > sample data inference.
        """
        # Check validation rules first
        for rule in column.validation_rules:
            if rule.type == "list":
                return "string"  # Dropdown = string
            elif rule.type == "whole":
                return "integer"
            elif rule.type == "decimal":
                return "float"
            elif rule.type == "date":
                return "date"
            elif rule.type == "textLength":
                return "string"

        # Fall back to sample-based detection
        if column.sample_values:
            return detect_data_type(column.sample_values)

        return "string"  # Default

    # ─── Required Detection ─────────────────────────────────────────────

    def _detect_required_status(
        self,
        column: ColumnSchema,
        header_cell,
        ws: Worksheet,
        header_row: int,
    ) -> bool:
        """
        Detect whether a column is required.

        Checks multiple signals:
        1. Asterisk (*) in column header name
        2. Data validation with allow_blank=False
        3. Red/yellow/orange fill color on header (common marketplace convention)
        4. Header text containing "required", "mandatory", "(required)"

        Args:
            column: The column being analyzed.
            header_cell: The header cell object.
            ws: The worksheet.
            header_row: Header row number.

        Returns:
            True if the column appears to be required.
        """
        name = column.name
        name_lower = name.lower()

        # Check 0: Explicit overrides (fields that should always be optional)
        optional_keywords = [
            "url", 
            "link", 
            "product data status", 
            "disapproval reason", 
            "qc status", 
            "qc failed reason"
        ]
        if any(kw in name_lower for kw in optional_keywords):
            return False

        # Check 1: Asterisk in header
        if "*" in name:
            return True

        # Check 2: Header text contains "required" or "mandatory"
        if any(kw in name_lower for kw in ("required", "mandatory", "(required)")):
            return True

        # Check 3: Validation rule with allow_blank=False
        for rule in column.validation_rules:
            if not rule.allow_blank:
                return True
                
        # Check 3b: Explicit fallback for core e-commerce identifiers
        if name_lower in ("seller sku id", "sku", "item_sku", "mrp (inr)", "your selling price (inr)"):
            return True

        # Check 4: Red/yellow/orange/blue fill color
        if column.fill_color:
            color = column.fill_color.upper()
            # Common "required" colors (without alpha prefix)
            required_colors = {
                "FF0000",  # Red
                "FF4444",  # Light red
                "FFFF00",  # Yellow
                "FFD700",  # Gold
                "FFA500",  # Orange
                "FF6347",  # Tomato
                "FF8C00",  # Dark orange
                "FFCC00",  # Amber
                "8DB4E2",  # Flipkart Required Blue
                "CC99FF",  # Flipkart Logistics Required Purple
            }
            if color in required_colors:
                return True

        return False

    # ─── Max Length Detection ───────────────────────────────────────────

    def _detect_max_length(self, column: ColumnSchema) -> Optional[int]:
        """
        Detect the maximum allowed field length.

        Sources:
        1. Data validation rules (textLength type)
        2. Observed maximum from sample values
        """
        # Check validation rules
        for rule in column.validation_rules:
            if rule.type == "textLength" and rule.formula1:
                try:
                    # formula1 is the max length for "lessThanOrEqual" operator
                    return int(rule.formula1)
                except (ValueError, TypeError):
                    pass

        return None

    # ─── Merged Cells ───────────────────────────────────────────────────

    def _detect_merged_cells_xlsx(self, ws: Worksheet) -> list[MergedRange]:
        """Detect all merged cell ranges in a worksheet."""
        merged = []
        for merge_range in ws.merged_cells.ranges:
            value = ws.cell(
                row=merge_range.min_row,
                column=merge_range.min_col
            ).value

            merged.append(MergedRange(
                start_row=merge_range.min_row,
                start_col=merge_range.min_col,
                end_row=merge_range.max_row,
                end_col=merge_range.max_col,
                value=value,
                range_string=str(merge_range),
            ))

        if merged:
            logger.debug(
                f"Found {len(merged)} merged ranges in sheet '{ws.title}'"
            )

        return merged

    # ─── Formula Detection ──────────────────────────────────────────────

    def _extract_formulas_xlsx(
        self, ws: Worksheet, header_row: int
    ) -> list[dict[str, str]]:
        """Extract cells containing formulas (outside the header row)."""
        formulas = []
        max_formulas = 50  # Cap to prevent huge outputs

        for row in ws.iter_rows(
            min_row=1,
            max_row=ws.max_row or 1,
            max_col=ws.max_column or 1,
        ):
            for cell in row:
                if (cell.value and isinstance(cell.value, str) and
                        cell.value.startswith("=")):
                    formulas.append({
                        "cell": f"{index_to_column_letter(cell.column)}{cell.row}",
                        "formula": cell.value,
                    })
                    if len(formulas) >= max_formulas:
                        self._warnings.append(
                            f"Formula extraction capped at {max_formulas} "
                            f"in sheet '{ws.title}'."
                        )
                        return formulas

        return formulas

    def _check_column_has_formula(
        self, ws: Worksheet, col_idx: int, header_row: int
    ) -> bool:
        """Check if any data cell in this column contains a formula."""
        max_check = min((ws.max_row or header_row) + 1, header_row + 20)
        for row in range(header_row + 1, max_check):
            value = ws.cell(row=row, column=col_idx).value
            if value and isinstance(value, str) and value.startswith("="):
                return True
        return False

    # ─── Named Ranges ───────────────────────────────────────────────────

    def _extract_named_ranges_xlsx(self, wb) -> list[dict[str, str]]:
        """Extract all defined names (named ranges) from the workbook."""
        named_ranges = []

        # openpyxl 3.1+: defined_names is a DefinedNameDict, iterable via .values()
        for defined_name in wb.defined_names.values():
            try:
                name_entry = {
                    "name": defined_name.name,
                    "value": str(defined_name.attr_text) if defined_name.attr_text else "",
                }
                # Determine scope
                if defined_name.localSheetId is not None:
                    idx = defined_name.localSheetId
                    if idx < len(wb.sheetnames):
                        name_entry["scope"] = wb.sheetnames[idx]
                    else:
                        name_entry["scope"] = f"sheet_index_{idx}"
                else:
                    name_entry["scope"] = "workbook"

                named_ranges.append(name_entry)
            except Exception as e:
                logger.debug(f"Skipping named range: {e}")

        if named_ranges:
            logger.debug(f"Found {len(named_ranges)} named ranges.")

        return named_ranges

    # ─── Hidden State Detection ─────────────────────────────────────────
    # (Sheet visibility is handled in _analyze_sheet_xlsx via sheet_state)
    # (Column visibility is handled in _extract_column_schema via column_dimensions)

    # ─── .xls Analysis (xlrd) ───────────────────────────────────────────

    def _analyze_xls(self, file_path: Path) -> WorkbookSchema:
        """
        Analyze a .xls file using xlrd.

        Since xlrd cannot write and has a different API, we convert
        the data to our schema model directly.
        """
        try:
            import xlrd
        except ImportError:
            raise AnalysisError(
                "xlrd is required to read .xls files. "
                "Install it with: pip install xlrd"
            )

        try:
            wb = xlrd.open_workbook(str(file_path), formatting_info=True)
        except Exception as e:
            raise AnalysisError(f"Cannot open .xls file: {e}") from e

        schema = WorkbookSchema(
            sheet_count=wb.nsheets,
        )

        for idx in range(wb.nsheets):
            ws = wb.sheet_by_index(idx)
            sheet_schema = self._analyze_sheet_xls(ws, idx, wb)
            schema.sheets.append(sheet_schema)
            
            # Extract global rules from index sheets
            if not sheet_schema.is_data_sheet:
                name_lower = sheet_schema.name.lower()
                if any(x in name_lower for x in ["index", "instruction", "rule", "guideline"]):
                    texts = []
                    import xlrd
                    # Read column by column for better readability of rule tables
                    for colx in range(ws.ncols):
                        col_vals = []
                        for rowx in range(ws.nrows):
                            cell = ws.cell(rowx, colx)
                            if cell.ctype not in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK) and str(cell.value).strip():
                                col_vals.append(str(cell.value).strip())
                        if col_vals:
                            texts.append(" | ".join(col_vals))
                    if texts:
                        if schema.global_rules:
                            schema.global_rules += f"\n\n--- Sheet: {sheet_schema.name} ---\n" + "\n".join(texts)
                        else:
                            schema.global_rules = f"--- Sheet: {sheet_schema.name} ---\n" + "\n".join(texts)

        return schema

    def _analyze_sheet_xls(self, ws, index: int, wb) -> SheetSchema:
        """Analyze a single .xls worksheet."""
        import xlrd

        sheet = SheetSchema(
            name=ws.name,
            index=index,
            is_visible=(ws.visibility == 0),  # 0 = visible
            row_count=ws.nrows,
            col_count=ws.ncols,
        )

        # Detect header row (scan first 20 rows)
        header_row = 0  # xlrd is 0-indexed
        best_score = 0

        for row in range(min(20, ws.nrows)):
            score = 0
            for col in range(ws.ncols):
                cell = ws.cell(row, col)
                if cell.ctype == xlrd.XL_CELL_TEXT and cell.value.strip():
                    score += 1
                elif cell.ctype not in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                    score += 0.3
            if score > best_score:
                best_score = score
                header_row = row

        sheet.header_row = header_row + 1  # Convert to 1-indexed

        # Check if data sheet
        name_lower = ws.name.lower().strip()
        non_data_names = {
            "instructions", "readme", "read me", "summary", "info",
            "help", "notes", "guide", "about", "index", "toc",
            "table of contents", "changelog", "version",
            "summary sheet", "listing faq sheet", "image guidelines",
            "matchingattributes", "variantattributes",
            "template_version", "parent variant products",
        }
        non_data_prefixes = (
            "dropdown", "faq", "image guide", "listing faq",
        )
        header_count = sum(
            1 for col in range(ws.ncols)
            if ws.cell(header_row, col).ctype == xlrd.XL_CELL_TEXT
            and ws.cell(header_row, col).value.strip()
        )

        if (name_lower in non_data_names
            or any(name_lower.startswith(p) for p in non_data_prefixes)
            or header_count < 3):
            sheet.is_data_sheet = False
            return sheet

        # Extract columns
        for col_idx in range(ws.ncols):
            cell = ws.cell(header_row, col_idx)
            if cell.ctype != xlrd.XL_CELL_TEXT or not cell.value.strip():
                continue

            column = ColumnSchema(
                name=cell.value.strip(),
                index=col_idx + 1,  # Convert to 1-indexed
                letter=index_to_column_letter(col_idx + 1),
            )

            # Try to extract fill color for heuristics
            if wb.formatting_info:
                try:
                    xf = wb.xf_list[cell.xf_index]
                    bg_idx = xf.background.pattern_colour_index
                    rgb = wb.colour_map.get(bg_idx)
                    if rgb and len(rgb) == 3:
                        column.fill_color = f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
                except Exception:
                    pass

            # Sample data
            samples = []
            for row in range(header_row + 1, min(ws.nrows, header_row + 100)):
                val = ws.cell(row, col_idx).value
                if val is not None and str(val).strip():
                    samples.append(val)
                    if len(samples) >= config.MAX_SAMPLE_VALUES:
                        break
            column.sample_values = samples

            # Infer type from samples
            column.data_type = detect_data_type(samples)

            # Check required status using keyword and heuristic fallback
            column.is_required = self._detect_required_status(
                column, None, None, header_row
            )

            # Extract instructions (rows below header)
            instructions = []
            import xlrd
            for instr_row in range(header_row + 1, min(header_row + 6, ws.nrows)):
                instr_cell = ws.cell(instr_row, col_idx)
                if instr_cell.ctype not in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK) and str(instr_cell.value).strip():
                    instructions.append(str(instr_cell.value).strip())
            if instructions:
                column.instructions = instructions

            column.data_type = self._infer_column_type(column)

            sheet.columns.append(column)

        self._warnings.append(
            f"Sheet '{ws.name}' is .xls format — data validation "
            "and formatting details are limited."
        )

        return sheet
