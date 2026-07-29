"""
ExcelPlorer — Validation API Routes

Handles the intake, syntax validation, and semantic validation
of AI-generated JSON against the WorkbookSchema.
"""

import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, request

import config
from backend.utils.json_utils import parse_json_with_errors
from backend.core.validator import ValidationEngine
from backend.api.prompt import _dict_to_workbook_schema

logger = logging.getLogger(__name__)

validate_bp = Blueprint("validate", __name__, url_prefix="/api")


@validate_bp.route("/validate/<session_id>", methods=["POST"])
def validate_json(session_id: str):
    """
    Validate pasted JSON syntax and semantics against the schema.

    Accepts:
        JSON body containing {"raw_json": "..."}
        OR raw text/plain body.
        
    Returns:
        JSON with valid_syntax flag, is_valid (semantic) flag, 
        and ValidationReport details.

    Status Codes:
        200: Successfully parsed syntax (even if semantic validation fails).
             Returns the ValidationReport.
        400: Bad request (no data) or schema missing.
        404: Session not found.
        500: Internal server error.
    """
    # ─── Validate session exists ─────────────────────────────────────
    session_dir = config.SESSIONS_DIR / session_id
    if not session_dir.exists():
        return jsonify({
            "error": "Session not found",
            "message": f"No session found with ID: {session_id}",
        }), 404

    # ─── Ensure schema exists ────────────────────────────────────────
    schema_path = session_dir / "schema.json"
    if not schema_path.exists():
        return jsonify({
            "error": "Schema not found",
            "message": "Cannot validate without an analyzed template.",
        }), 400

    # ─── Extract payload ─────────────────────────────────────────────
    raw_json_str = ""
    
    if request.is_json:
        data = request.get_json()
        if not data or "raw_json" not in data:
            return jsonify({
                "error": "Invalid payload",
                "message": "JSON body must contain a 'raw_json' field.",
            }), 400
        raw_json_str = data["raw_json"]
    else:
        # Fallback for raw text/plain
        raw_json_str = request.get_data(as_text=True)

    if not raw_json_str.strip():
        return jsonify({
            "error": "Empty payload",
            "message": "No JSON content provided to validate.",
        }), 400

    # ─── Phase 4: Syntax Validation ──────────────────────────────────
    try:
        syntax_result = parse_json_with_errors(raw_json_str)
        
        if not syntax_result["valid_syntax"]:
            logger.warning(
                f"Syntax error for session {session_id} at line {syntax_result['line']}: {syntax_result['error']}"
            )
            return jsonify({
                "valid_syntax": False,
                "is_valid": False,
                "error": syntax_result["error"],
                "line": syntax_result["line"],
                "column": syntax_result["column"],
            }), 200

        parsed_data = syntax_result["parsed_data"]
        
        # Ensure it's a list (as our prompts instruct)
        if not isinstance(parsed_data, list):
            parsed_data = [parsed_data]

        # ─── Phase 5: Semantic Validation & Auto-Correction ──────────
        
        # Load schema
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_dict = json.load(f)
        schema = _dict_to_workbook_schema(schema_dict)

        engine = ValidationEngine()
        report = engine.validate(parsed_data, schema)
        
        response_payload = {
            "valid_syntax": True,
            "is_valid": report.is_valid,
            "report": report.to_dict(),
            "item_count": len(parsed_data)
        }
        
        # Save the report to session
        report_path = session_dir / "report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(response_payload, f, indent=2, ensure_ascii=False)
        
        # Always save the *corrected* data to input.json
        input_path = session_dir / "input.json"
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(report.corrected_data, f, indent=2, ensure_ascii=False)
            
        if report.is_valid:
            logger.info(f"Saved valid & corrected JSON for session {session_id}.")
            response_payload["message"] = "All items are completely valid."
        else:
            logger.warning(f"Semantic validation failed for some items in session {session_id}.")
            response_payload["message"] = "Some items contain validation errors."

        return jsonify(response_payload), 200

    except Exception as e:
        logger.error(
            f"Unexpected error validating JSON for session {session_id}: {e}",
            exc_info=True,
        )
        return jsonify({
            "error": "Internal error",
            "message": "An unexpected error occurred during validation.",
        }), 500
