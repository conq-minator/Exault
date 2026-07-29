"""
ExcelPlorer — JSON Utilities

Helper functions for parsing and cleaning AI-generated JSON.
"""

import json
import re


def strip_markdown(text: str) -> str:
    """
    Remove markdown code block formatting if present.
    AI models often wrap JSON in ```json ... ``` despite instructions.
    
    Args:
        text: The raw text string.
        
    Returns:
        The cleaned string, ideally containing only JSON.
    """
    text = text.strip()
    
    # Check for ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
        
    return text


def parse_json_with_errors(json_string: str) -> dict:
    """
    Attempt to parse JSON, returning structured error data if it fails.
    
    Args:
        json_string: The raw JSON string to parse.
        
    Returns:
        A dictionary indicating success or failure.
        If valid: {"valid_syntax": True, "parsed_data": dict | list}
        If invalid: {"valid_syntax": False, "error": str, "line": int, "column": int, "parsed_data": None}
    """
    cleaned_string = strip_markdown(json_string)
    
    if not cleaned_string:
        return {
            "valid_syntax": False,
            "error": "No JSON content provided.",
            "line": 1,
            "column": 1,
            "parsed_data": None
        }

    try:
        data = json.loads(cleaned_string)
        return {
            "valid_syntax": True,
            "parsed_data": data
        }
    except json.JSONDecodeError as e:
        return {
            "valid_syntax": False,
            "error": e.msg,
            "line": e.lineno,
            "column": e.colno,
            "parsed_data": None
        }
