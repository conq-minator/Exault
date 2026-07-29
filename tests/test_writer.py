"""
ExcelPlorer — Tests for Excel Writer

Tests for backend/core/writer.py.
"""

import os
from pathlib import Path
import pytest
import openpyxl

from backend.core.schema import WorkbookSchema, SheetSchema, ColumnSchema
from backend.core.writer import ExcelWriter, WriterError, MissingSkuError


@pytest.fixture
def mock_template_path(tmp_path):
    """Creates a basic Excel template for testing."""
    path = tmp_path / "template.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data Entry"
    
    # Setup headers on row 1
    ws["A1"] = "SKU"
    ws["B1"] = "Price"
    ws["C1"] = "Color"
    
    # Pre-fill rows with SKUs to test the matching logic
    # Note: start_scan logic skips to header_row + 2. If header is 0 (row 1), it scans from row 2
    ws["A2"] = "123"
    ws["B2"] = ""
    ws["C2"] = ""
    
    ws["A3"] = "456"
    ws["B3"] = ""
    ws["C3"] = ""
    
    # Set a background color for the header to verify style isn't destroyed
    # But since we just want to ensure we write to correct cells, this is fine.
    
    wb.save(path)
    return path


@pytest.fixture
def test_schema():
    """Provides a WorkbookSchema matching the mock template."""
    wb = WorkbookSchema(filename="template.xlsx")
    sheet = SheetSchema(name="Data Entry", is_data_sheet=True, header_row=1)
    
    sheet.columns.extend([
        ColumnSchema(name="SKU", index=1),
        ColumnSchema(name="Price", index=2),
        ColumnSchema(name="Color", index=3),
    ])
    
    wb.sheets.append(sheet)
    return wb


class TestExcelWriter:

    def test_write_success(self, tmp_path, mock_template_path, test_schema):
        output_path = tmp_path / "output.xlsx"
        
        # The mock template has SKUs "123" and "456" in rows 2 and 3.
        data = [
            {"SKU": "123", "Price": 10.99, "Color": "Red"},
            {"SKU": "456", "Price": 20.00, "Color": "Blue"},
        ]
        
        writer = ExcelWriter()
        writer.write(mock_template_path, output_path, data, test_schema)
        
        assert output_path.exists()
        
        # Verify content
        wb = openpyxl.load_workbook(output_path)
        ws = wb["Data Entry"]
        
        # Headers should be untouched
        assert ws["A1"].value == "SKU"
        assert ws["B1"].value == "Price"
        
        # Data starts on row 2, and should be updated by SKU
        assert str(ws["A2"].value) == "123"
        assert ws["B2"].value == 10.99
        assert ws["C2"].value == "Red"
        
        assert str(ws["A3"].value) == "456"
        assert ws["B3"].value == 20.0
        assert ws["C3"].value == "Blue"

    def test_write_sku_not_found(self, tmp_path, mock_template_path, test_schema):
        output_path = tmp_path / "output.xlsx"
        
        # This SKU does not exist in the mock template
        data = [
            {"SKU": "999", "Price": 10.99, "Color": "Red"}
        ]
        
        writer = ExcelWriter()
        with pytest.raises(MissingSkuError, match="SKUs not found in document: 999"):
            writer.write(mock_template_path, output_path, data, test_schema)

    def test_missing_template(self, tmp_path, test_schema):
        bad_path = tmp_path / "does_not_exist.xlsx"
        output_path = tmp_path / "output.xlsx"
        
        writer = ExcelWriter()
        with pytest.raises(WriterError, match="Template not found"):
            writer.write(bad_path, output_path, [], test_schema)

    def test_missing_sheet(self, tmp_path, mock_template_path):
        output_path = tmp_path / "output.xlsx"
        
        # Schema expects a sheet that doesn't exist in the mock template
        bad_schema = WorkbookSchema()
        sheet = SheetSchema(name="Wrong Sheet Name", is_data_sheet=True)
        sheet.columns.append(ColumnSchema(name="SKU", index=1))
        bad_schema.sheets.append(sheet)
        
        writer = ExcelWriter()
        with pytest.raises(WriterError, match="not found in workbook"):
            writer.write(mock_template_path, output_path, [], bad_schema)

    def test_no_data_sheets(self, tmp_path, mock_template_path):
        output_path = tmp_path / "output.xlsx"
        
        # Schema has no data sheets
        bad_schema = WorkbookSchema()
        bad_schema.sheets.append(SheetSchema(name="Instructions", is_data_sheet=False))
        
        writer = ExcelWriter()
        with pytest.raises(WriterError, match="No data entry sheets found"):
            writer.write(mock_template_path, output_path, [], bad_schema)
