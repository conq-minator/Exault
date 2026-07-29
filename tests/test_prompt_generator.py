"""
ExcelPlorer — Tests for Prompt Generator Engine

Tests for backend/core/prompt_generator.py.
"""

import pytest

from backend.core.prompt_generator import PromptGenerator
from backend.core.schema import WorkbookSchema, SheetSchema, ColumnSchema


@pytest.fixture
def empty_schema():
    """Provides a WorkbookSchema with no data columns."""
    wb = WorkbookSchema(filename="empty.xlsx")
    sheet = SheetSchema(name="Instructions", is_data_sheet=False)
    wb.sheets.append(sheet)
    return wb


@pytest.fixture
def mock_schema():
    """Provides a populated WorkbookSchema for prompt testing."""
    wb = WorkbookSchema(
        filename="test_template.xlsx",
        detected_marketplace="Flipkart"
    )
    
    sheet = SheetSchema(name="Data", is_data_sheet=True)
    
    # Required string column with length limit
    col1 = ColumnSchema(
        name="SKU ID",
        data_type="string",
        is_required=True,
        max_length=50
    )
    
    # Optional dropdown column
    col2 = ColumnSchema(
        name="Category",
        data_type="string",
        is_required=False,
        allowed_values=["Electronics", "Clothing", "Home"]
    )
    
    # Numeric column
    col3 = ColumnSchema(
        name="Price",
        data_type="float",
        is_required=True
    )
    
    # Hidden column (should be ignored)
    col4 = ColumnSchema(
        name="Internal ID",
        is_hidden=True
    )
    
    sheet.columns.extend([col1, col2, col3, col4])
    wb.sheets.append(sheet)
    return wb


@pytest.fixture
def prompt_generator():
    return PromptGenerator()


class TestPromptGenerator:

    def test_generate_empty_schema(self, prompt_generator, empty_schema):
        """Test behavior when no data columns exist."""
        result = prompt_generator.generate(empty_schema)
        
        assert "prompt" in result
        assert "No data entry columns" in result["prompt"]
        assert result["char_count"] == 0
        assert result["word_count"] == 0
        assert result["token_count"] == 0

    def test_generate_populated_schema(self, prompt_generator, mock_schema):
        """Test full prompt generation structure."""
        result = prompt_generator.generate(mock_schema)
        prompt = result["prompt"]
        
        # Check header elements
        assert "CRITICAL INSTRUCTIONS:" in prompt
        assert "Output ONLY valid, parseable JSON" in prompt
        
        # Check plugin additions
        assert "MARKETPLACE RULES (Flipkart)" in prompt
        
        # Check fields section
        assert "ABSOLUTELY REQUIRED FIELDS" in prompt
        assert "OPTIONAL DETAILS" in prompt
        
        # Check field inclusion
        assert '"SKU ID": Type: string' in prompt
        assert '"Price": Type: float' in prompt
        
        # Check limits
        assert "Max length: 50 chars" in prompt
        assert "[Allowed values: 'Electronics', 'Clothing', 'Home']" in prompt
        
        # Check hidden column exclusion
        assert "Internal ID" not in prompt
        
        # Check examples
        assert "EXPECTED JSON STRUCTURE:" in prompt
        assert "SKU ID" in prompt
        assert "Category" in prompt
        
        # Ensure stats are populated
        assert result["char_count"] > 0
        
        # Check stats
        assert result["char_count"] > 100
        assert result["word_count"] > 20
        assert result["token_count"] > 20

    def test_build_example_json_defaults(self, prompt_generator, mock_schema):
        """Test that default values are correctly assigned in example JSON."""
        json_str = prompt_generator._build_example_json(mock_schema.get_all_columns())
        
        # Price should default to 0.0
        assert '"Price": 0.0' in json_str
        
        # Category should default to first allowed value
        assert '"Category": "Electronics"' in json_str

    def test_allowed_values_truncation(self, prompt_generator):
        """Test that extremely long dropdown lists are truncated."""
        wb = WorkbookSchema()
        sheet = SheetSchema(name="Data", is_data_sheet=True)
        col = ColumnSchema(
            name="Huge Dropdown",
            allowed_values=[f"Val{i}" for i in range(100)]
        )
        sheet.columns.append(col)
        wb.sheets.append(sheet)
        
        result = prompt_generator.generate(wb)
        prompt = result["prompt"]
        
        # Check that it truncated
        assert "... (and more)" in prompt
        # Ensure not all 100 values are printed
        assert "'Val99'" not in prompt
