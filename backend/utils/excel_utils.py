"""
ExcelPlorer — Excel Utility Functions

Stateless helper functions for Excel cell/range operations,
data type detection, and format conversions.

All functions are pure — no side effects, no state.
"""

import logging
import re
from datetime import datetime, date, time
from typing import Any, Optional

from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


# ─── Column Letter ↔ Index Conversion ───────────────────────────────────────


def column_letter_to_index(letter: str) -> int:
    """
    Convert a column letter to a 1-based index.

    Args:
        letter: Column letter string, e.g., "A", "Z", "AA", "AZ".

    Returns:
        1-based column index (A=1, B=2, ..., Z=26, AA=27, ...).

    Examples:
        >>> column_letter_to_index("A")
        1
        >>> column_letter_to_index("Z")
        26
        >>> column_letter_to_index("AA")
        27
    """
    letter = letter.upper().strip()
    result = 0
    for char in letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result


def index_to_column_letter(index: int) -> str:
    """
    Convert a 1-based column index to a column letter.

    Args:
        index: 1-based column index.

    Returns:
        Column letter string (1="A", 26="Z", 27="AA", ...).

    Examples:
        >>> index_to_column_letter(1)
        'A'
        >>> index_to_column_letter(26)
        'Z'
        >>> index_to_column_letter(27)
        'AA'
    """
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord('A') + remainder) + result
    return result


# ─── Cell Range Parsing ─────────────────────────────────────────────────────


def parse_cell_range(range_str: str) -> tuple[int, int, int, int]:
    """
    Parse a cell range string into (min_row, min_col, max_row, max_col).

    Handles both absolute ($A$1) and relative (A1) references.

    Args:
        range_str: Cell range, e.g., "A1:C10", "$A$1:$C$10", "B3".

    Returns:
        Tuple of (min_row, min_col, max_row, max_col), all 1-indexed.

    Raises:
        ValueError: If the range string cannot be parsed.

    Examples:
        >>> parse_cell_range("A1:C10")
        (1, 1, 10, 3)
        >>> parse_cell_range("B3")
        (3, 2, 3, 2)
    """
    # Remove absolute reference markers
    clean = range_str.replace("$", "").strip()

    # Split on ':'
    parts = clean.split(":")
    if len(parts) == 1:
        # Single cell reference
        row, col = _parse_single_cell(parts[0])
        return (row, col, row, col)
    elif len(parts) == 2:
        row1, col1 = _parse_single_cell(parts[0])
        row2, col2 = _parse_single_cell(parts[1])
        return (
            min(row1, row2),
            min(col1, col2),
            max(row1, row2),
            max(col1, col2),
        )
    else:
        raise ValueError(f"Invalid cell range: {range_str}")


def _parse_single_cell(cell_ref: str) -> tuple[int, int]:
    """
    Parse a single cell reference like 'A1' into (row, col).

    Args:
        cell_ref: Cell reference string, e.g., "A1", "BC123".

    Returns:
        Tuple of (row, column), both 1-indexed.
    """
    match = re.match(r'^([A-Za-z]+)(\d+)$', cell_ref.strip())
    if not match:
        raise ValueError(f"Invalid cell reference: {cell_ref}")
    col_letter = match.group(1)
    row_number = int(match.group(2))
    return (row_number, column_letter_to_index(col_letter))


# ─── Formula Reference Resolution ──────────────────────────────────────────


def parse_formula_reference(formula: str) -> Optional[dict[str, str]]:
    """
    Parse a formula reference like '=Sheet2!$A$1:$A$10' or 'Sheet2!A1:A10'.

    Args:
        formula: Formula string from a data validation rule.

    Returns:
        Dictionary with 'sheet_name' and 'range' keys, or None if not parseable.

    Examples:
        >>> parse_formula_reference("=Sheet2!$A$1:$A$10")
        {'sheet_name': 'Sheet2', 'range': 'A1:A10'}
        >>> parse_formula_reference("'My Sheet'!$B$1:$B$50")
        {'sheet_name': 'My Sheet', 'range': 'B1:B50'}
    """
    if not formula:
        return None

    # Strip leading '='
    clean = formula.lstrip("=").strip()

    # Check for sheet reference (contains '!')
    if "!" not in clean:
        return None

    # Split on '!' — handle quoted sheet names
    if clean.startswith("'"):
        # Quoted sheet name: 'Sheet Name'!A1:A10
        end_quote = clean.index("'", 1)
        sheet_name = clean[1:end_quote]
        cell_range = clean[end_quote + 2:]  # Skip '!
    else:
        parts = clean.split("!", 1)
        sheet_name = parts[0]
        cell_range = parts[1]

    # Clean up absolute references
    cell_range = cell_range.replace("$", "").strip()

    return {
        "sheet_name": sheet_name,
        "range": cell_range,
    }


def resolve_formula_reference(formula: str, workbook) -> list[Any]:
    """
    Resolve a formula reference to actual cell values.

    Opens the referenced sheet and reads the values from the specified range.

    Args:
        formula: Formula string (e.g., "=Sheet2!$A$1:$A$10").
        workbook: An openpyxl Workbook object.

    Returns:
        List of non-None values from the referenced cells.
    """
    ref = parse_formula_reference(formula)
    if not ref:
        logger.debug(f"Could not parse formula reference: {formula}")
        return []

    sheet_name = ref["sheet_name"]
    cell_range = ref["range"]

    # Check if sheet exists
    if sheet_name not in workbook.sheetnames:
        logger.warning(f"Referenced sheet '{sheet_name}' not found in workbook.")
        return []

    sheet = workbook[sheet_name]
    values = []

    try:
        min_row, min_col, max_row, max_col = parse_cell_range(cell_range)
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                cell_value = sheet.cell(row=row, column=col).value
                if cell_value is not None and str(cell_value).strip():
                    values.append(str(cell_value).strip())
    except (ValueError, IndexError) as e:
        logger.warning(f"Error resolving formula '{formula}': {e}")

    return values


# ─── Data Type Detection ───────────────────────────────────────────────────


def detect_data_type(values: list[Any]) -> str:
    """
    Infer the predominant data type from a list of sample values.

    Args:
        values: List of sample values from a column.

    Returns:
        One of: 'string', 'integer', 'float', 'date', 'boolean',
                'url', 'email', or 'unknown'.
    """
    if not values:
        return "unknown"

    # Filter out None and empty strings
    non_empty = [v for v in values if v is not None and str(v).strip()]
    if not non_empty:
        return "unknown"

    type_counts: dict[str, int] = {
        "integer": 0,
        "float": 0,
        "boolean": 0,
        "date": 0,
        "url": 0,
        "email": 0,
        "string": 0,
    }

    for val in non_empty:
        detected = _detect_single_type(val)
        type_counts[detected] = type_counts.get(detected, 0) + 1

    # Return the most common type — break ties toward more specific types
    priority = ["date", "email", "url", "boolean", "integer", "float", "string"]
    best_type = "string"
    best_count = 0

    for dtype in priority:
        count = type_counts.get(dtype, 0)
        if count > best_count:
            best_count = count
            best_type = dtype

    # Only return the type if a majority of values match
    threshold = len(non_empty) / 2
    if best_count >= threshold:
        return best_type

    return "string"


def _detect_single_type(value: Any) -> str:
    """Detect the type of a single value."""
    # Already typed from openpyxl
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, (datetime, date, time)):
        return "date"

    # String-based detection
    s = str(value).strip()
    if not s:
        return "string"

    # Boolean
    if s.lower() in ("true", "false", "yes", "no", "y", "n"):
        return "boolean"

    # Integer
    try:
        int(s)
        return "integer"
    except (ValueError, OverflowError):
        pass

    # Float
    try:
        float(s)
        return "float"
    except (ValueError, OverflowError):
        pass

    # URL
    if re.match(r'^https?://', s, re.IGNORECASE):
        return "url"

    # Email
    if re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', s):
        return "email"

    # Date — use dateutil parser with strict=True to avoid false positives
    if is_date_value(s):
        return "date"

    return "string"


def is_date_value(value: Any) -> bool:
    """
    Check if a value looks like a date.

    Uses python-dateutil for flexible parsing but avoids false positives
    by rejecting pure numbers, single words, and very short strings.

    Args:
        value: Value to check.

    Returns:
        True if the value is likely a date.
    """
    if isinstance(value, (datetime, date)):
        return True

    s = str(value).strip()

    # Too short or just a number — not a date
    if len(s) < 6:
        return False
    try:
        float(s)
        return False  # Pure numbers are not dates
    except (ValueError, OverflowError):
        pass

    # Must contain at least one separator to be a date
    if not re.search(r'[/\-., ]', s):
        return False

    try:
        date_parser.parse(s, fuzzy=False)
        return True
    except (ValueError, OverflowError):
        return False


# ─── Merged Cell Helpers ────────────────────────────────────────────────────


def get_merged_cell_value(sheet, row: int, col: int) -> Any:
    """
    Get the value of a cell that may be part of a merged range.

    If the cell is in a merged range, returns the value from the
    top-left cell of that range. Otherwise returns the cell's own value.

    Args:
        sheet: An openpyxl Worksheet object.
        row: Row number (1-indexed).
        col: Column number (1-indexed).

    Returns:
        The cell value (or the merged range's top-left value).
    """
    for merged_range in sheet.merged_cells.ranges:
        if (merged_range.min_row <= row <= merged_range.max_row and
                merged_range.min_col <= col <= merged_range.max_col):
            # Return the top-left cell's value
            return sheet.cell(
                row=merged_range.min_row,
                column=merged_range.min_col
            ).value

    # Not merged — return normal value
    return sheet.cell(row=row, column=col).value


# ─── Sheet Name Helpers ─────────────────────────────────────────────────────


def sanitize_sheet_name(name: str) -> str:
    """
    Clean a sheet name for use as a safe identifier.

    Removes characters that are problematic in JSON keys or filenames.

    Args:
        name: Original sheet name.

    Returns:
        Sanitized name with special characters replaced by underscores.
    """
    # Replace any non-alphanumeric (except spaces and hyphens) with underscore
    clean = re.sub(r'[^\w\s\-]', '_', name)
    # Collapse multiple underscores/spaces
    clean = re.sub(r'[\s_]+', '_', clean)
    return clean.strip('_')


# ─── Color Helpers ──────────────────────────────────────────────────────────


def get_fill_color_hex(cell) -> Optional[str]:
    """
    Extract the fill color of a cell as a hex string.

    Args:
        cell: An openpyxl Cell object.

    Returns:
        Hex color string (e.g., "FF0000") or None if no fill.
    """
    try:
        fill = cell.fill
        if fill and fill.fgColor and fill.fgColor.rgb:
            color = str(fill.fgColor.rgb)
            # openpyxl sometimes returns "00000000" for no fill
            if color and color != "00000000" and len(color) >= 6:
                # Strip alpha channel if present (AARRGGBB → RRGGBB)
                if len(color) == 8:
                    return color[2:]
                return color
    except (AttributeError, TypeError):
        pass
    return None
