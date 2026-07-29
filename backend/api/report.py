"""
ExcelPlorer — Report API Routes

Retrieves and formats validation reports.
"""

import json
import logging
from flask import Blueprint, jsonify, request, Response

import config
from backend.core.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

report_bp = Blueprint("report", __name__, url_prefix="/api")


@report_bp.route("/report/<session_id>", methods=["GET"])
def get_report(session_id: str):
    """
    Get the validation report for a session.
    
    Query params:
        format (str): 'json' (default), 'txt', or 'html'.
        
    Status Codes:
        200: Successfully returned report.
        400: Invalid format requested.
        404: Session or report not found.
        500: Internal error.
    """
    session_dir = config.SESSIONS_DIR / session_id
    if not session_dir.exists():
        return jsonify({"error": "Session not found"}), 404
        
    report_path = session_dir / "report.json"
    if not report_path.exists():
        return jsonify({"error": "Report not found. Please run validation first."}), 404
        
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
            
        fmt = request.args.get("format", "json").lower()
        
        if fmt == "json":
            return jsonify(payload), 200
            
        elif fmt == "txt":
            content = ReportGenerator.generate_txt(payload)
            return Response(content, mimetype="text/plain")
            
        elif fmt == "html":
            content = ReportGenerator.generate_html(payload)
            return Response(content, mimetype="text/html")
            
        else:
            return jsonify({"error": f"Invalid format '{fmt}'. Use 'json', 'txt', or 'html'."}), 400
            
    except Exception as e:
        logger.error(f"Error serving report for session {session_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error retrieving report."}), 500
