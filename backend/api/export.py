"""
ExcelPlorer — Export API Routes

Handles generating the final Excel file from validated data
and serving it to the client as a download.
"""

import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, send_file, request

import config
from backend.core.writer import ExcelWriter, WriterError, MissingSkuError
from backend.api.prompt import _dict_to_workbook_schema

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__, url_prefix="/api")


@export_bp.route("/export/<session_id>", methods=["GET"])
def export_file(session_id: str):
    """
    Generate and download the final filled Excel template.
    
    Status Codes:
        200: Successfully generated, returns file stream.
        400: Session data incomplete (no template, schema, or input data).
        404: Session not found.
        500: Internal server error during writing.
    """
    session_dir = config.SESSIONS_DIR / session_id
    
    if not session_dir.exists():
        return jsonify({"error": "Session not found"}), 404
        
    template_path = session_dir / "template.xlsx"
    if not template_path.exists():
        template_path = session_dir / "template.xls"
        
    schema_path = session_dir / "schema.json"
    input_path = session_dir / "input.json"
    output_path = session_dir / f"output{template_path.suffix}"
    
    # 1. Verify required files exist
    if not template_path.exists():
        return jsonify({"error": "Original template is missing from session."}), 400
    if not schema_path.exists():
        return jsonify({"error": "Workbook schema is missing. Analysis incomplete."}), 400
    if not input_path.exists():
        return jsonify({"error": "Validated data is missing. Please complete validation first."}), 400
        
    # 2. Generate the file if it doesn't exist (or if we want to force re-generation)
    # For now, we will always regenerate to ensure we have the latest input.json
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        report_path = session_dir / "report.json"
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
                item_statuses = report_data.get("report", {}).get("item_statuses", [])
                
                # Filter out items that are marked as invalid
                valid_data = []
                for i, item in enumerate(data):
                    if i < len(item_statuses) and item_statuses[i].get("is_valid", False):
                        valid_data.append(item)
                    elif i >= len(item_statuses):
                        # Fallback if status missing, assume valid to be safe
                        valid_data.append(item)
                
                if not valid_data and data:
                    return jsonify({"error": "No valid products to export. Please fix validation errors."}), 400
                    
                data = valid_data
            
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_dict = json.load(f)
            schema = _dict_to_workbook_schema(schema_dict)
        skip_missing = request.args.get("skip_missing", "false").lower() == "true"
            
        writer = ExcelWriter()
        writer.write(template_path, output_path, data, schema, skip_missing_skus=skip_missing)
        
    except MissingSkuError as e:
        logger.warning(f"Missing SKUs on export for session {session_id}: {e.missing_skus}")
        return jsonify({
            "error": "Missing SKUs",
            "message": "Some SKUs in the input data were not found in the original template.",
            "missing_skus": e.missing_skus
        }), 409
    except WriterError as e:
        logger.error(f"Writer error for session {session_id}: {e}")
        return jsonify({"error": "Failed to generate Excel file", "details": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error generating file for session {session_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal error generating file."}), 500
        
    # 3. Serve the file
    # We construct a friendly filename
    download_name = schema.filename
    
    return send_file(
        output_path, 
        as_attachment=True, 
        download_name=download_name
    )
