"""
ExcelPlorer — Tests for Plugin System

Tests for backend/plugins/.
"""

import pytest
from backend.core.schema import WorkbookSchema, SheetSchema, ColumnSchema
from backend.plugins.registry import PluginRegistry
from backend.plugins.flipkart import FlipkartPlugin


def test_registry_initialization():
    PluginRegistry.initialize()
    
    flipkart = PluginRegistry.get_plugin("flipkart")
    amazon = PluginRegistry.get_plugin("amazon")
    meesho = PluginRegistry.get_plugin("meesho")
    
    assert flipkart is not None
    assert flipkart.name == "Flipkart"
    
    assert amazon is not None
    assert meesho is not None


def test_flipkart_detection():
    plugin = FlipkartPlugin()
    
    # 1. Match filename
    schema_file = WorkbookSchema(filename="Flipkart_listing.xlsx")
    assert plugin.detect(schema_file) == 0.3
    
    # 2. Match columns
    schema_cols = WorkbookSchema(filename="template.xlsx")
    sheet = SheetSchema(name="Data")
    sheet.columns.extend([
        ColumnSchema(name="FSN"),
        ColumnSchema(name="Brand"),
        ColumnSchema(name="Brand Approval"),
        ColumnSchema(name="MRP")
    ])
    schema_cols.sheets.append(sheet)
    
    assert plugin.detect(schema_cols) == 0.5
    
    # 3. Match both
    schema_both = WorkbookSchema(filename="flipkart.xlsx")
    schema_both.sheets.append(sheet)
    
    assert plugin.detect(schema_both) == 0.8


def test_flipkart_validation_rules():
    plugin = FlipkartPlugin()
    schema = WorkbookSchema()
    
    rules = plugin.get_validation_rules(schema)
    assert len(rules) == 2
    
    rule_brand_approval, rule_mrp = rules
    
    # Test Brand Approval Rule
    issues = rule_brand_approval({"Brand": "Nike", "Brand Approval": "No"}, 0)
    assert len(issues) == 1
    assert issues[0].field == "Brand Approval"
    
    issues = rule_brand_approval({"Brand": "Nike", "Brand Approval": "Yes"}, 0)
    assert len(issues) == 0
    
    issues = rule_brand_approval({"Brand": "Generic", "Brand Approval": "No"}, 0)
    assert len(issues) == 0
    
    # Test MRP vs SP Rule
    issues = rule_mrp({"MRP": "100", "Selling Price": "120"}, 0)
    assert len(issues) == 1
    assert issues[0].field == "MRP"
    
    issues = rule_mrp({"MRP": "150", "Selling Price": "120"}, 0)
    assert len(issues) == 0


def test_flipkart_auto_corrections():
    plugin = FlipkartPlugin()
    schema = WorkbookSchema()
    
    item = {"Brand": "nike"}
    issues = plugin.apply_auto_corrections(item, schema)
    
    assert len(issues) == 1
    assert item["Brand"] == "Nike"
    assert issues[0].message == "Converted brand name to Title Case per Flipkart conventions."
    
    # Generic shouldn't be touched
    item = {"Brand": "generic"}
    issues = plugin.apply_auto_corrections(item, schema)
    
    assert len(issues) == 0
    assert item["Brand"] == "generic"
