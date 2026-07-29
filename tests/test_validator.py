"""
ExcelPlorer — Tests for Validation Engine

Tests for backend/core/validator.py.
"""

import pytest

from backend.core.schema import WorkbookSchema, SheetSchema, ColumnSchema
from backend.core.validator import ValidationEngine


@pytest.fixture
def test_schema():
    """Provides a WorkbookSchema for validation testing."""
    wb = WorkbookSchema()
    sheet = SheetSchema(name="Data", is_data_sheet=True)
    
    sheet.columns.extend([
        ColumnSchema(name="Title", data_type="string", is_required=True, max_length=10),
        ColumnSchema(name="Price", data_type="float", is_required=True),
        ColumnSchema(name="Stock", data_type="integer", is_required=False),
        ColumnSchema(name="Is Active", data_type="boolean", is_required=False),
        ColumnSchema(name="Color", data_type="string", is_required=False, allowed_values=["Red", "Blue", "Green"]),
    ])
    
    wb.sheets.append(sheet)
    return wb


@pytest.fixture
def validator():
    return ValidationEngine()


class TestValidationEngine:

    def test_valid_data(self, validator, test_schema):
        data = [{
            "Title": "Widget",
            "Price": 9.99,
            "Stock": 100,
            "Is Active": "Yes",
            "Color": "Red"
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is True
        assert len(report.issues) == 0
        assert report.corrected_data == data

    def test_missing_required_field(self, validator, test_schema):
        data = [{
            "Title": "Widget",
            # Missing Price
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is False
        assert len(report.issues) == 1
        
        issue = report.issues[0]
        assert issue.severity == "ERROR"
        assert issue.field == "Price"
        assert "Missing required" in issue.message

    def test_empty_required_field(self, validator, test_schema):
        data = [{
            "Title": "   ", # effectively empty
            "Price": 9.99
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is False
        
        issue = next(i for i in report.issues if i.field == "Title")
        assert issue.severity == "ERROR"
        assert "Missing required" in issue.message

    def test_unknown_field_warning(self, validator, test_schema):
        data = [{
            "Title": "Widget",
            "Price": 9.99,
            "FakeField": "Ignore Me"
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is True # Unknown fields are WARNINGs, not ERRORs
        assert len(report.issues) == 1
        
        issue = report.issues[0]
        assert issue.severity == "WARNING"
        assert issue.field == "FakeField"
        assert "Unknown field" in issue.message

    def test_multi_item_independent_validation(self, validator, test_schema):
        data = [
            {
                "Title": "Widget 1",
                "Price": 9.99
            },
            {
                "Title": "Widget 2",
                # Missing Price -> ERROR
            },
            {
                "Title": "Widget 3",
                "Price": 14.99
            }
        ]
        
        report = validator.validate(data, test_schema)
        
        # Batch is technically not perfectly valid
        assert report.is_valid is False
        
        # But item statuses should show independent tracking
        assert len(report.item_statuses) == 3
        assert report.item_statuses[0]["is_valid"] is True
        assert report.item_statuses[1]["is_valid"] is False
        assert report.item_statuses[2]["is_valid"] is True
        
        # 1 error issue for item 1
        errors = [i for i in report.issues if i.severity == "ERROR"]
        assert len(errors) == 1
        assert errors[0].item_index == 1

    def test_max_length_violation(self, validator, test_schema):
        data = [{
            "Title": "This Title Is Way Too Long", # max 10
            "Price": 9.99
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is False
        
        issue = report.issues[0]
        assert issue.severity == "ERROR"
        assert issue.field == "Title"
        assert "Exceeds max length" in issue.message

    def test_invalid_type(self, validator, test_schema):
        data = [{
            "Title": "Widget",
            "Price": "not_a_number" # Will fail float cast
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is False
        
        issue = report.issues[0]
        assert issue.severity == "ERROR"
        assert issue.field == "Price"
        assert "Expected a number" in issue.message

    def test_invalid_allowed_value(self, validator, test_schema):
        data = [{
            "Title": "Widget",
            "Price": 9.99,
            "Color": "Yellow" # Not in Red, Blue, Green
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is False
        
        issue = report.issues[0]
        assert issue.severity == "ERROR"
        assert issue.field == "Color"
        assert "not in the allowed list" in issue.message


class TestAutoCorrector:

    def test_whitespace_trimming(self, validator, test_schema):
        data = [{
            "Title": "  Widget  ",
            "Price": 9.99
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is True
        assert report.corrected_data[0]["Title"] == "Widget"
        # Trimming doesn't emit an INFO issue to avoid noise

    def test_numeric_casting(self, validator, test_schema):
        data = [{
            "Title": "Widget",
            "Price": "9.99", # string
            "Stock": "42.0"  # float string to int
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is True
        assert report.corrected_data[0]["Price"] == 9.99
        assert isinstance(report.corrected_data[0]["Price"], float)
        
        assert report.corrected_data[0]["Stock"] == 42
        assert isinstance(report.corrected_data[0]["Stock"], int)
        
        issues = [i for i in report.issues if i.severity == "INFO"]
        assert len(issues) == 2
        assert "Cast string" in issues[0].message

    def test_boolean_normalization(self, validator, test_schema):
        data = [{
            "Title": "Widget",
            "Price": 9.99,
            "Is Active": "true" # Should become "Yes"
        }, {
            "Title": "Widget 2",
            "Price": 9.99,
            "Is Active": "0" # Should become "No"
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is True
        assert report.corrected_data[0]["Is Active"] == "Yes"
        assert report.corrected_data[1]["Is Active"] == "No"
        
        issues = [i for i in report.issues if i.severity == "INFO"]
        assert len(issues) == 2
        assert "Normalized boolean" in issues[0].message

    def test_case_insensitive_dropdown_normalization(self, validator, test_schema):
        data = [{
            "Title": "Widget",
            "Price": 9.99,
            "Color": " rEd " # Should become "Red" after trim and case check
        }]
        
        report = validator.validate(data, test_schema)
        
        assert report.is_valid is True
        assert report.corrected_data[0]["Color"] == "Red"
        
        issues = [i for i in report.issues if i.severity == "INFO"]
        assert len(issues) == 1
        assert "Corrected case" in issues[0].message
