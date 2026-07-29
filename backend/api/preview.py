"""
ExcelPlorer — Preview API Routes

Returns data preview and handles manual cell edits.
"""

import json
import logging
from flask import Blueprint, jsonify, request
import config

logger = logging.getLogger(__name__)

preview_bp = Blueprint("preview", __name__, url_prefix="/api")


@preview_bp.route("/preview/<session_id>", methods=["GET"])
def get_preview(session_id: str):
    """
    Get the data preview for a session.
    Reads input.json which contains the corrected data from validation.
    """
    session_dir = config.SESSIONS_DIR / session_id
    input_path = session_dir / "input.json"
    
    if not input_path.exists():
        return jsonify({
            "error": "Not Found",
            "message": "No preview data available. Please validate JSON first."
        }), 404
        
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error reading preview data for session {session_id}: {e}")
        return jsonify({
            "error": "Internal Error",
            "message": "Could not read preview data."
        }), 500


@preview_bp.route("/preview/<session_id>/row/<int:row_index>", methods=["PUT"])
def edit_row(session_id: str, row_index: int):
    """
    Update a full row in the preview data.
    """
    session_dir = config.SESSIONS_DIR / session_id
    input_path = session_dir / "input.json"
    
    if not input_path.exists():
        return jsonify({"error": "Not Found", "message": "No data available."}), 404
        
    if not request.is_json:
        return jsonify({"error": "Bad Request", "message": "Expected JSON payload."}), 400
        
    row_data = request.get_json()
    
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if row_index < 0 or row_index >= len(data):
            return jsonify({"error": "Bad Request", "message": "Invalid row index."}), 400
            
        # Update row
        data[row_index] = row_data
        
        # Save back
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return jsonify({"message": "Row updated successfully."}), 200
    except Exception as e:
        logger.error(f"Error updating row {row_index} for session {session_id}: {e}")
        return jsonify({"error": "Internal Error", "message": "Could not update row."}), 500
