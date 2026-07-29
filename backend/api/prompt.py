"""
ExcelPlorer — Prompt API Routes

Returns the generated AI prompt for a session.
Supports generating on-the-fly or returning a cached version.
"""

import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, request

import config
from backend.core.prompt_generator import PromptGenerator
from backend.core.schema import WorkbookSchema

logger = logging.getLogger(__name__)

prompt_bp = Blueprint("prompt", __name__, url_prefix="/api")


@prompt_bp.route("/prompt/<session_id>", methods=["GET"])
def get_prompt(session_id: str):
    """
    Get the generated AI prompt for a session.

    Loads the cached prompt.json if available, otherwise generates it
    from the session's schema.json.

    Query params:
        refresh (bool): If true, force re-generation even if cached.

    Returns:
        JSON with prompt text and statistics (char/word/token counts).

    Status Codes:
        200: Prompt returned successfully.
        404: Session or schema not found.
        500: Generation failed.
    """
    # ─── Validate session exists ─────────────────────────────────────
    session_dir = config.SESSIONS_DIR / session_id
    if not session_dir.exists():
        return jsonify({
            "error": "Session not found",
            "message": f"No session found with ID: {session_id}",
        }), 404

    # ─── Check for cached prompt ─────────────────────────────────────
    prompt_path = session_dir / "prompt.json"
    force_refresh = request.args.get("refresh", "").lower() in ("true", "1", "yes")

    if prompt_path.exists() and not force_refresh:
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            logger.debug(f"Returning cached prompt for session {session_id}")
            return jsonify(cached), 200
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(
                f"Cached prompt corrupted for session {session_id}: {e}. "
                "Re-generating."
            )

    # ─── Find the schema ─────────────────────────────────────────────
    schema_path = session_dir / "schema.json"
    if not schema_path.exists():
        return jsonify({
            "error": "Schema not found",
            "message": (
                f"No analysis schema found for session {session_id}. "
                "Please ensure the file was successfully analyzed first."
            ),
        }), 404

    # ─── Generate prompt ─────────────────────────────────────────────
    try:
        # Load schema dict and convert to WorkbookSchema object
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_dict = json.load(f)
        
        # We need to manually reconstruct the WorkbookSchema object from dict
        schema = _dict_to_workbook_schema(schema_dict)

        # Generate prompt
        generator = PromptGenerator()
        prompt_data = generator.generate(schema)

        # Cache the result
        with open(prompt_path, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Generated prompt for session {session_id}: "
            f"{prompt_data['token_count']} tokens"
        )

        return jsonify(prompt_data), 200

    except Exception as e:
        logger.error(
            f"Unexpected error generating prompt for session {session_id}: {e}",
            exc_info=True,
        )
        return jsonify({
            "error": "Internal error",
            "message": "An unexpected error occurred during prompt generation.",
        }), 500


def _dict_to_workbook_schema(data: dict) -> WorkbookSchema:
    """
    Convert a nested dictionary (from JSON) back to a WorkbookSchema object.
    Required for the PromptGenerator to use its methods like get_all_columns().
    """
    from backend.core.schema import SheetSchema, ColumnSchema
    
    # We're extracting from an AnalysisResult payload
    if "schema" in data:
        schema_data = data["schema"]
    else:
        schema_data = data
        
    wb = WorkbookSchema(
        filename=schema_data.get("filename", ""),
        file_size=schema_data.get("file_size", 0),
        file_extension=schema_data.get("file_extension", ""),
        sheet_count=schema_data.get("sheet_count", 0),
        detected_marketplace=schema_data.get("detected_marketplace"),
        global_rules=schema_data.get("global_rules", "")
    )
    
    for sheet_dict in schema_data.get("sheets", []):
        sheet = SheetSchema(
            name=sheet_dict.get("name", ""),
            index=sheet_dict.get("index", 0),
            is_visible=sheet_dict.get("is_visible", True),
            is_data_sheet=sheet_dict.get("is_data_sheet", True),
            header_row=sheet_dict.get("header_row", 1)
        )
        
        for col_dict in sheet_dict.get("columns", []):
            col = ColumnSchema(
                name=col_dict.get("name", ""),
                index=col_dict.get("index", 0),
                letter=col_dict.get("letter", ""),
                data_type=col_dict.get("data_type", "string"),
                is_required=col_dict.get("is_required", False),
                is_hidden=col_dict.get("is_hidden", False),
                allowed_values=col_dict.get("allowed_values", []),
                max_length=col_dict.get("max_length"),
                fill_color=col_dict.get("fill_color"),
                instructions=col_dict.get("instructions", [])
            )
            sheet.columns.append(col)
            
        wb.sheets.append(sheet)
        
    return wb
