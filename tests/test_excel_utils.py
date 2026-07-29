"""
ExcelPlorer — Tests for Excel Utility Functions

Tests for backend/utils/excel_utils.py.
"""

import pytest
from datetime import datetime, date

from backend.utils.excel_utils import (
    column_letter_to_index,
    index_to_column_letter,
    parse_cell_range,
    parse_formula_reference,
    detect_data_type,
    is_date_value,
    sanitize_sheet_name,
)


# ─── Column Letter ↔ Index ──────────────────────────────────────────────────


class TestColumnLetterToIndex:
    """Tests for column_letter_to_index()."""

    def test_single_letters(self):
        assert column_letter_to_index("A") == 1
        assert column_letter_to_index("B") == 2
        assert column_letter_to_index("Z") == 26

    def test_double_letters(self):
        assert column_letter_to_index("AA") == 27
        assert column_letter_to_index("AB") == 28
        assert column_letter_to_index("AZ") == 52

    def test_triple_letters(self):
        assert column_letter_to_index("AAA") == 703

    def test_case_insensitive(self):
        assert column_letter_to_index("a") == 1
        assert column_letter_to_index("aa") == 27

    def test_with_whitespace(self):
        assert column_letter_to_index("  A  ") == 1


class TestIndexToColumnLetter:
    """Tests for index_to_column_letter()."""

    def test_single_letters(self):
        assert index_to_column_letter(1) == "A"
        assert index_to_column_letter(2) == "B"
        assert index_to_column_letter(26) == "Z"

    def test_double_letters(self):
        assert index_to_column_letter(27) == "AA"
        assert index_to_column_letter(28) == "AB"
        assert index_to_column_letter(52) == "AZ"

    def test_triple_letters(self):
        assert index_to_column_letter(703) == "AAA"

    def test_roundtrip(self):
        """Verify letter → index → letter roundtrip."""
        for i in range(1, 100):
            assert column_letter_to_index(index_to_column_letter(i)) == i


# ─── Cell Range Parsing ─────────────────────────────────────────────────────


class TestParseCellRange:
    """Tests for parse_cell_range()."""

    def test_range(self):
        assert parse_cell_range("A1:C10") == (1, 1, 10, 3)

    def test_single_cell(self):
        assert parse_cell_range("B3") == (3, 2, 3, 2)

    def test_absolute_references(self):
        assert parse_cell_range("$A$1:$C$10") == (1, 1, 10, 3)

    def test_mixed_references(self):
        assert parse_cell_range("$A1:C$10") == (1, 1, 10, 3)

    def test_large_range(self):
        result = parse_cell_range("A1:ZZ1000")
        assert result[0] == 1  # min_row
        assert result[2] == 1000  # max_row

    def test_invalid_range(self):
        with pytest.raises(ValueError):
            parse_cell_range("not_a_range")

    def test_invalid_multi_colon(self):
        with pytest.raises(ValueError):
            parse_cell_range("A1:B2:C3")


# ─── Formula Reference Parsing ──────────────────────────────────────────────


class TestParseFormulaReference:
    """Tests for parse_formula_reference()."""

    def test_simple_reference(self):
        result = parse_formula_reference("=Sheet2!$A$1:$A$10")
        assert result == {"sheet_name": "Sheet2", "range": "A1:A10"}

    def test_quoted_sheet_name(self):
        result = parse_formula_reference("='My Sheet'!$B$1:$B$50")
        assert result == {"sheet_name": "My Sheet", "range": "B1:B50"}

    def test_without_equals(self):
        result = parse_formula_reference("Sheet1!A1:A10")
        assert result == {"sheet_name": "Sheet1", "range": "A1:A10"}

    def test_no_sheet_reference(self):
        result = parse_formula_reference("A1:A10")
        assert result is None

    def test_empty_formula(self):
        result = parse_formula_reference("")
        assert result is None

    def test_none_formula(self):
        result = parse_formula_reference(None)
        assert result is None


# ─── Data Type Detection ───────────────────────────────────────────────────


class TestDetectDataType:
    """Tests for detect_data_type()."""

    def test_integers(self):
        assert detect_data_type([1, 2, 3, 4]) == "integer"
        assert detect_data_type(["1", "2", "3"]) == "integer"

    def test_floats(self):
        assert detect_data_type([1.5, 2.7, 3.14]) == "float"
        assert detect_data_type(["1.5", "2.7"]) == "float"

    def test_strings(self):
        assert detect_data_type(["hello", "world", "foo"]) == "string"

    def test_booleans(self):
        assert detect_data_type([True, False, True]) == "boolean"
        assert detect_data_type(["Yes", "No", "Yes"]) == "boolean"

    def test_urls(self):
        assert detect_data_type([
            "https://example.com/img1.jpg",
            "http://example.com/img2.png",
        ]) == "url"

    def test_emails(self):
        assert detect_data_type([
            "user@example.com",
            "admin@test.org",
        ]) == "email"

    def test_dates(self):
        assert detect_data_type([
            datetime(2024, 1, 15),
            datetime(2024, 2, 20),
        ]) == "date"

    def test_empty_list(self):
        assert detect_data_type([]) == "unknown"

    def test_all_none(self):
        assert detect_data_type([None, None, None]) == "unknown"

    def test_mixed_defaults_to_string(self):
        # Mixed types where no majority → string
        result = detect_data_type(["hello", 42, True, "2024-01-01"])
        assert result == "string"


# ─── Date Detection ─────────────────────────────────────────────────────────


class TestIsDateValue:
    """Tests for is_date_value()."""

    def test_datetime_object(self):
        assert is_date_value(datetime(2024, 1, 15)) is True

    def test_date_object(self):
        assert is_date_value(date(2024, 1, 15)) is True

    def test_date_string(self):
        assert is_date_value("2024-01-15") is True
        assert is_date_value("15/01/2024") is True
        assert is_date_value("Jan 15, 2024") is True

    def test_not_date_number(self):
        assert is_date_value("42") is False
        assert is_date_value("3.14") is False

    def test_not_date_short(self):
        assert is_date_value("hi") is False

    def test_not_date_plain_word(self):
        assert is_date_value("hello") is False


# ─── Sheet Name Sanitization ────────────────────────────────────────────────


class TestSanitizeSheetName:
    """Tests for sanitize_sheet_name()."""

    def test_clean_name(self):
        assert sanitize_sheet_name("Sheet1") == "Sheet1"

    def test_spaces(self):
        assert sanitize_sheet_name("My Sheet") == "My_Sheet"

    def test_special_chars(self):
        assert sanitize_sheet_name("Sheet (v2)") == "Sheet_v2"

    def test_multiple_underscores(self):
        result = sanitize_sheet_name("A___B   C")
        assert "__" not in result
