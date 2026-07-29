"""
ExcelPlorer — Tests for Report Generator

Tests for backend/core/report_generator.py.
"""

from backend.core.report_generator import ReportGenerator


def test_generate_txt():
    payload = {
        "is_valid": False,
        "item_count": 5,
        "report": {
            "issues": [
                {"severity": "ERROR", "item_index": 0, "field": "Price", "message": "Missing required field."},
                {"severity": "WARNING", "item_index": 1, "field": "FakeCol", "message": "Unknown field."},
                {"severity": "INFO", "item_index": 2, "field": "IsActive", "message": "Normalized boolean."}
            ]
        }
    }
    
    txt = ReportGenerator.generate_txt(payload)
    
    assert "Status:      FAILED" in txt
    assert "Total Rows:  5" in txt
    assert "Errors:      1" in txt
    assert "Warnings:    1" in txt
    assert "Corrections: 1" in txt
    
    assert "[Row 1] Price: Missing required field." in txt
    assert "[Row 2] FakeCol: Unknown field." in txt
    assert "[Row 3] IsActive: Normalized boolean." in txt


def test_generate_html():
    payload = {
        "is_valid": True,
        "item_count": 2,
        "report": {
            "issues": [
                {"severity": "INFO", "item_index": 0, "field": "Price", "message": "Cast string to number."}
            ]
        }
    }
    
    html = ReportGenerator.generate_html(payload)
    
    assert "<title>ExcelPlorer Validation Report</title>" in html
    assert "Status: <span class='status'>PASSED</span>" in html
    assert "Total Rows: <strong>2</strong>" in html
    assert "Errors: <strong>0</strong>" in html
    assert "Warnings: <strong>0</strong>" in html
    assert "Auto-Corrections: <strong>1</strong>" in html
    
    assert "<td>1</td><td>Price</td><td>Cast string to number.</td>" in html
