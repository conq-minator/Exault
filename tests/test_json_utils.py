"""
ExcelPlorer — Tests for JSON Utilities

Tests for backend/utils/json_utils.py.
"""

from backend.utils.json_utils import strip_markdown, parse_json_with_errors


class TestStripMarkdown:
    
    def test_strip_markdown_json_block(self):
        text = "```json\n{\n  \"key\": \"value\"\n}\n```"
        expected = "{\n  \"key\": \"value\"\n}"
        assert strip_markdown(text) == expected

    def test_strip_markdown_generic_block(self):
        text = "```\n[\n  1, 2, 3\n]\n```"
        expected = "[\n  1, 2, 3\n]"
        assert strip_markdown(text) == expected

    def test_strip_markdown_no_block(self):
        text = '{"key": "value"}'
        assert strip_markdown(text) == text

    def test_strip_markdown_with_surrounding_text(self):
        text = "Here is your JSON:\n```json\n[1, 2]\n```\nHave a good day!"
        expected = "[1, 2]"
        assert strip_markdown(text) == expected

    def test_strip_markdown_whitespace_handling(self):
        text = "   ```json   \n  {\"a\": 1}  \n   ```   "
        expected = '{"a": 1}'
        assert strip_markdown(text) == expected


class TestParseJsonWithErrors:

    def test_parse_valid_json_object(self):
        raw = '{"name": "test", "value": 42}'
        result = parse_json_with_errors(raw)
        
        assert result["valid_syntax"] is True
        assert result["parsed_data"] == {"name": "test", "value": 42}
        assert "error" not in result

    def test_parse_valid_json_array(self):
        raw = '[{"id": 1}, {"id": 2}]'
        result = parse_json_with_errors(raw)
        
        assert result["valid_syntax"] is True
        assert len(result["parsed_data"]) == 2
        
    def test_parse_markdown_wrapped_json(self):
        raw = '```json\n{"valid": true}\n```'
        result = parse_json_with_errors(raw)
        
        assert result["valid_syntax"] is True
        assert result["parsed_data"] == {"valid": True}

    def test_parse_missing_comma(self):
        raw = '{\n  "a": 1\n  "b": 2\n}'
        result = parse_json_with_errors(raw)
        
        assert result["valid_syntax"] is False
        assert result["line"] == 3
        # col differs slightly by python version, but it should be present
        assert result["column"] > 0
        assert "Expecting ',' delimiter" in result["error"] or "Expecting property name" in result["error"]

    def test_parse_trailing_comma(self):
        raw = '{\n  "a": 1,\n}'
        result = parse_json_with_errors(raw)
        
        assert result["valid_syntax"] is False
        assert result["line"] in (2, 3)  # Python 3.12+ might point to 2, older to 3
        assert "Expecting property name" in result["error"] or "Illegal trailing comma" in result["error"]

    def test_parse_missing_quote(self):
        raw = '{\n  "a": 1,\n  "b: 2\n}'
        result = parse_json_with_errors(raw)
        
        assert result["valid_syntax"] is False
        assert result["line"] == 3
        assert result["column"] > 0
        assert "Unterminated string" in result["error"] or "Invalid control character" in result["error"]

    def test_parse_empty_string(self):
        raw = "   \n   "
        result = parse_json_with_errors(raw)
        
        assert result["valid_syntax"] is False
        assert result["error"] == "No JSON content provided."
        assert result["line"] == 1
        assert result["column"] == 1
