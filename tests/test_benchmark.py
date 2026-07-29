import time
import pytest
from backend.core.schema import WorkbookSchema, SheetSchema, ColumnSchema
from backend.core.validator import ValidationEngine

def test_performance_100_products():
    """
    NFR-01.1: Excel processing (100 products) < 5 seconds
    NFR-01.3: JSON validation (100 products) < 1 second
    """
    # Create mock schema
    schema = WorkbookSchema(
        filename="benchmark.xlsx",
        file_size=1024,
        sheet_count=1,
        sheets=[
            SheetSchema(
                name="Data",
                is_data_sheet=True,
                columns=[
                    ColumnSchema(name=f"Col_{i}", letter=chr(65+i), index=i+1, data_type="Text", is_required=True)
                    for i in range(20) # 20 columns
                ]
            )
        ]
    )
    
    # Create mock data (100 rows)
    mock_data = []
    for i in range(100):
        row = {f"Col_{j}": f"Value {i}-{j}" for j in range(20)}
        mock_data.append(row)
    
    engine = ValidationEngine()
    
    # Measure validation time
    start_time = time.time()
    report = engine.validate(mock_data, schema)
    end_time = time.time()
    
    duration = end_time - start_time
    
    # NFR-01.3 states JSON validation for 100 products < 1 second
    assert duration < 1.0, f"Validation took too long: {duration:.2f}s (must be < 1.0s)"
