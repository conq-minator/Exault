"""
ExcelPlorer — Upload API Routes

Handles file upload for marketplace Excel templates.
Creates a session, saves the file, and triggers automatic analysis.
"""

import json
import logging
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request

import config
from backend.core.analyzer import WorkbookAnalyzer, AnalysisError
from backend.core.session_manager import session_manager

logger = logging.getLogger(__name__)

upload_bp = Blueprint("upload", __name__, url_prefix="/api")


@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Upload a marketplace Excel template.

    Accepts: multipart/form-data with a .xlsx or .xls file
             in the 'file' field.

    Returns:
        JSON with session_id, file_info, and analysis result.

    Status Codes:
        200: Upload successful, analysis complete.
        400: No file provided or invalid file type.
        500: Analysis failed.
    """
    # ─── Validate request ────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({
            "error": "No file provided",
            "message": "Please upload an Excel file (.xlsx or .xls).",
        }), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({
            "error": "No file selected",
            "message": "The uploaded file has no filename.",
        }), 400

    # ─── Validate file extension ─────────────────────────────────────
    filename = file.filename
    extension = Path(filename).suffix.lower()

    if extension not in config.ALLOWED_EXTENSIONS:
        return jsonify({
            "error": "Invalid file type",
            "message": (
                f"File type '{extension}' is not supported. "
                f"Allowed types: {', '.join(sorted(config.ALLOWED_EXTENSIONS))}"
            ),
        }), 400

    # ─── Create session ──────────────────────────────────────────────
    session_id = str(uuid.uuid4())
    session_dir = config.SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Save the uploaded file
    saved_filename = f"template{extension}"
    saved_path = session_dir / saved_filename

    try:
        file.save(str(saved_path))
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
        return jsonify({
            "error": "Upload failed",
            "message": "Could not save the uploaded file.",
        }), 500

    file_size = saved_path.stat().st_size
    
    # Save to SQLite
    session_manager.create_session(session_id, filename, file_size)
    
    logger.info(
        f"File uploaded: '{filename}' ({file_size} bytes) → "
        f"session {session_id}"
    )

    # ─── Build file info ─────────────────────────────────────────────
    file_info = {
        "original_name": filename,
        "saved_name": saved_filename,
        "extension": extension,
        "size": file_size,
        "size_display": _format_file_size(file_size),
    }

    # ─── Run analysis ────────────────────────────────────────────────
    try:
        analyzer = WorkbookAnalyzer()
        result = analyzer.analyze(saved_path)

        # Cache the schema to disk
        schema_path = session_dir / "schema.json"
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(
            f"Analysis cached for session {session_id}: "
            f"{result.schema.sheet_count} sheets, "
            f"{sum(len(s.columns) for s in result.schema.sheets)} columns, "
            f"{result.duration_ms:.1f}ms"
        )

        return jsonify({
            "session_id": session_id,
            "file_info": file_info,
            "analysis": result.to_dict(),
        }), 200

    except AnalysisError as e:
        logger.error(f"Analysis failed for session {session_id}: {e}")
        # Still return the session — analysis can be retried
        return jsonify({
            "session_id": session_id,
            "file_info": file_info,
            "analysis": None,
            "error": "Analysis failed",
            "message": str(e),
        }), 200

    except Exception as e:
        logger.error(
            f"Unexpected error during upload/analysis: {e}", exc_info=True
        )
        return jsonify({
            "error": "Internal error",
            "message": "An unexpected error occurred during file processing.",
        }), 500


def _format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
