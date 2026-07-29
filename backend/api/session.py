"""
ExcelPlorer — Session API Routes

CRUD operations for session history.
"""

import logging
from flask import Blueprint, jsonify
from backend.core.session_manager import session_manager

logger = logging.getLogger(__name__)

session_bp = Blueprint("session", __name__, url_prefix="/api")


@session_bp.route("/sessions", methods=["GET"])
def list_sessions():
    """
    List all sessions with metadata.

    Returns: Array of session summaries.
    """
    sessions = session_manager.list_sessions()
    return jsonify({
        "sessions": sessions
    }), 200


@session_bp.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id: str):
    """
    Get full details for a specific session.

    Returns: Complete session data.
    """
    session = session_manager.get_session(session_id)
    if session:
        return jsonify(session), 200
    
    return jsonify({
        "error": "Not Found",
        "message": "Session not found."
    }), 404


@session_bp.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id: str):
    """
    Delete a session and its associated files.

    Returns: Success confirmation.
    """
    success = session_manager.delete_session(session_id)
    if success:
        return jsonify({"message": "Session deleted successfully."}), 200
    
    return jsonify({
        "error": "Not Found",
        "message": "Session not found."
    }), 404
