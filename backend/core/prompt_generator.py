"""
ExcelPlorer — Prompt Generator Engine

Translates a WorkbookSchema into an optimized AI prompt
that instructs language models to generate perfectly formatted JSON.
"""

import json
import logging
from typing import Any

import config
from backend.core.schema import WorkbookSchema, ColumnSchema

logger = logging.getLogger(__name__)


class PromptGenerator:
    """
    Generates dynamic AI prompts from a WorkbookSchema.
    
    Produces strict instructions, field definitions, and mock JSON
    examples to ensure the AI's output exactly matches the Excel template.
    """

    def generate(self, schema: WorkbookSchema) -> dict[str, Any]:
        """
        Generate the prompt and calculate its statistics.

        Args:
            schema: The parsed WorkbookSchema.

        Returns:
            Dictionary containing 'prompt', 'char_count', 'word_count', 
            and 'token_count'.
        """
        logger.info(f"Generating prompt for '{schema.filename}'")

        # 1. Gather all data columns
        columns = schema.get_all_columns()
        
        if not columns:
            logger.warning("No data columns found in schema. Prompt will be empty.")
            return {
                "prompt": "No data entry columns were found in the uploaded template.",
                "rules_prompt": "No template rules found.",
                "char_count": 0, "word_count": 0, "token_count": 0,
                "rules_char_count": 0, "rules_word_count": 0, "rules_token_count": 0
            }

        # Data Prompt
        data_sections = [
            self._build_header(),
            self._build_fields_section(columns),
            self._build_example_json(columns),
            self._build_footer()
        ]
        data_prompt_text = "\n\n".join(filter(bool, data_sections))
        data_stats = self._calculate_stats(data_prompt_text)
        
        # Rules Prompt
        rules_prompt_text = self._build_rules_prompt(schema, columns)
        rules_stats = self._calculate_stats(rules_prompt_text)
        
        return {
            "prompt": data_prompt_text,
            "rules_prompt": rules_prompt_text,
            "char_count": data_stats["char_count"],
            "word_count": data_stats["word_count"],
            "token_count": data_stats["token_count"],
            "rules_char_count": rules_stats["char_count"],
            "rules_word_count": rules_stats["word_count"],
            "rules_token_count": rules_stats["token_count"]
        }

    def _build_rules_prompt(self, schema: WorkbookSchema, columns: list[ColumnSchema]) -> str:
        """Build the rules prompt from global rules and instructions."""
        sections = [
            "You are an AI generating e-commerce product listings. Here are the strict rules and instructions extracted directly from the platform's template:"
        ]
        
        # 1. Global Rules
        if getattr(schema, "global_rules", None):
            sections.append("--- GLOBAL PLATFORM RULES & INDEX ---")
            sections.append(schema.global_rules)
            
        # 2. Field-Specific Rules
        sections.append("--- FIELD-SPECIFIC INSTRUCTIONS ---")
        field_rules = []
        for col in columns:
            if getattr(col, "instructions", None):
                instr_text = " | ".join(col.instructions)
                field_rules.append(f"- **{col.name}**: {instr_text}")
        
        if field_rules:
            sections.append("\n".join(field_rules))
        else:
            sections.append("No specific field instructions found.")
            
        # 3. Plugin additions
        additions = self._build_plugin_additions(schema)
        if additions:
            sections.append(additions)
            
        return "\n\n".join(sections)

    def _build_header(self) -> str:
        """Build the strict instructional header."""
        return (
            "You are an expert e-commerce data assistant. I will provide you with product images, titles, "
            "or descriptions. Your task is to extract and infer the product attributes to fill out a bulk "
            "listing template.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Output ONLY valid, parseable JSON. Do not include markdown code blocks (```json ... ```). "
            "Do not include any conversational text, greetings, or explanations before or after the JSON.\n"
            "2. Use EXACTLY the field names provided below. Do not alter casing, spacing, or punctuation.\n"
            "3. **ABSOLUTELY REQUIRED FIELDS**: These fields are non-negotiable. If you cannot confidently deduce "
            "the value for ANY of these fields from the user's input, YOU MUST NOT OUTPUT JSON. Instead, output a "
            "direct question asking the user to provide the missing required details.\n"
            "4. For fields with [Allowed values], you must choose EXACTLY one of those values.\n"
            "5. For OPTIONAL fields, if you do not know the value, omit the key or set its value to an empty string \"\". However, just because they are marked optional does NOT mean you should ignore them! If a highly important detail is missing that corresponds to an optional field, DO NOT skip it. You must ask the user to provide that detail. Even optional details can be necessary for a complete listing.\n"
            "6. You must support returning multiple products if I provide multiple items. The output must ALWAYS be a JSON array of objects.\n"
            "7. Never make up SKUs, IDs, or identifiers if they are not provided by the user or deducible."
        )

    def _build_plugin_additions(self, schema: WorkbookSchema) -> str:
        """
        Inject marketplace-specific rules if a plugin was detected.
        """
        if schema.detected_marketplace:
            from backend.plugins.registry import PluginRegistry
            plugin = PluginRegistry.get_plugin(schema.detected_marketplace)
            if plugin:
                additions = plugin.get_prompt_additions(schema)
                if additions:
                    return f"MARKETPLACE RULES ({schema.detected_marketplace}):\n{additions}"
        return ""

    # Colors that indicate a system-filled column (seller should NOT fill these)
    SYSTEM_FILL_COLORS = {"C0C0C0"}  # Gray = Flipkart-filled (system columns)

    def _is_system_column(self, col: ColumnSchema) -> bool:
        """Check if a column is system-filled (gray) and should be excluded from prompts."""
        if col.fill_color and col.fill_color.upper() in self.SYSTEM_FILL_COLORS:
            return True
        return False

    def _build_fields_section(self, columns: list[ColumnSchema]) -> str:
        """Build the detailed listing of every field and its constraints."""
        required_lines = []
        optional_lines = []
        
        for col in columns:
            if col.is_hidden:
                continue  # Don't ask AI to generate hidden columns
            if self._is_system_column(col):
                continue  # Don't ask AI to generate system-filled columns
                
            # Start field line
            line = f"- \"{col.name}\": Type: {col.data_type}."
            
            # Add constraints
            if col.max_length:
                line += f" Max length: {col.max_length} chars."
                
            if col.allowed_values:
                # Truncate long lists to avoid huge prompts
                display_vals = col.allowed_values
                if len(display_vals) > 30:
                    display_vals = display_vals[:30] + ["... (and more)"]
                
                vals_str = ", ".join(f"'{v}'" for v in display_vals)
                line += f" [Allowed values: {vals_str}]"
                
            if col.is_required:
                required_lines.append(line)
            else:
                optional_lines.append(line)
                
        lines = ["--- ABSOLUTELY REQUIRED FIELDS ---"]
        lines.append("If you lack information for ANY of these, STOP and ask the user for them.")
        lines.extend(required_lines if required_lines else ["None"])
        lines.append("\n--- OPTIONAL DETAILS ---")
        lines.append("Provide these if known, otherwise leave them empty.")
        lines.extend(optional_lines if optional_lines else ["None"])
            
        return "\n".join(lines)

    def _build_example_json(self, columns: list[ColumnSchema]) -> str:
        """Generate a mock JSON array structure showing expected output."""
        example_obj = {}
        
        for col in columns:
            if col.is_hidden:
                continue
            if self._is_system_column(col):
                continue
                
            # Pick a smart default value based on type
            val: Any = ""
            if col.allowed_values:
                val = col.allowed_values[0]
            elif col.data_type == "integer":
                val = 0
            elif col.data_type == "float":
                val = 0.0
            elif col.data_type == "boolean":
                val = "Yes" # Excel templates usually prefer string Yes/No
            elif col.data_type == "date":
                val = "2024-01-01"
            elif col.data_type == "url":
                val = "https://example.com/image.jpg"
            else:
                val = "..."
                
            example_obj[col.name] = val

        # Format nicely
        json_str = json.dumps([example_obj, example_obj], indent=2)
        
        return f"EXPECTED JSON STRUCTURE:\n{json_str}"

    def _build_footer(self) -> str:
        """Final strict reminder."""
        return (
            "Remember: If you have all required info, output NOTHING but the JSON array. "
            "If you are missing required info, output NOTHING but your question asking for it."
        )

    def _calculate_stats(self, text: str) -> dict[str, int]:
        """Calculate length metrics for the prompt."""
        char_count = len(text)
        words = text.split()
        word_count = len(words)
        # Use config.TOKENS_PER_WORD for a rough token estimate
        token_count = int(word_count * getattr(config, "TOKENS_PER_WORD", 1.33))
        
        return {
            "char_count": char_count,
            "word_count": word_count,
            "token_count": token_count
        }
