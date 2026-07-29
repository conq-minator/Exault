"""
ExcelPlorer — Analysis API Routes

Returns workbook analysis results for a given session.
Supports cached results and re-analysis.
"""

import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, request

import config
from backend.core.analyzer import WorkbookAnalyzer, AnalysisError

logger = logging.getLogger(__name__)

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api")


@analysis_bp.route("/analysis/<session_id>", methods=["GET"])
def get_analysis(session_id: str):
    """
    Get the full workbook analysis for a session.

    Loads the cached schema.json if available, otherwise re-analyzes
    the template file.

    Query params:
        refresh (bool): If true, force re-analysis even if cached.

    Returns:
        Complete AnalysisResult as JSON.

    Status Codes:
        200: Analysis returned successfully.
        404: Session not found.
        500: Analysis failed.
    """
    # ─── Validate session exists ─────────────────────────────────────
    session_dir = config.SESSIONS_DIR / session_id
    if not session_dir.exists():
        return jsonify({
            "error": "Session not found",
            "message": f"No session found with ID: {session_id}",
        }), 404

    # ─── Check for cached schema ────────────────────────────────────
    schema_path = session_dir / "schema.json"
    force_refresh = request.args.get("refresh", "").lower() in ("true", "1", "yes")

    if schema_path.exists() and not force_refresh:
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            logger.debug(f"Returning cached analysis for session {session_id}")
            return jsonify(cached), 200
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(
                f"Cached schema corrupted for session {session_id}: {e}. "
                "Re-analyzing."
            )

    # ─── Find the template file ──────────────────────────────────────
    template_path = _find_template(session_dir)
    if template_path is None:
        return jsonify({
            "error": "Template not found",
            "message": (
                f"No Excel template found in session {session_id}. "
                "The file may have been deleted."
            ),
        }), 404

    # ─── Run analysis ────────────────────────────────────────────────
    try:
        analyzer = WorkbookAnalyzer()
        result = analyzer.analyze(template_path)

        # Cache the result
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(
            f"Re-analyzed session {session_id}: "
            f"{result.schema.sheet_count} sheets, "
            f"{result.duration_ms:.1f}ms"
        )

        return jsonify(result.to_dict()), 200

    except AnalysisError as e:
        logger.error(f"Analysis failed for session {session_id}: {e}")
        return jsonify({
            "error": "Analysis failed",
            "message": str(e),
        }), 500

    except Exception as e:
        logger.error(
            f"Unexpected error analyzing session {session_id}: {e}",
            exc_info=True,
        )
        return jsonify({
            "error": "Internal error",
            "message": "An unexpected error occurred during analysis.",
        }), 500


def _find_template(session_dir: Path) -> Path | None:
    """
    Find the template file in a session directory.

    Looks for template.xlsx or template.xls.

    Args:
        session_dir: Path to the session directory.

    Returns:
        Path to the template file, or None if not found.
    """
    for ext in (".xlsx", ".xls"):
        path = session_dir / f"template{ext}"
        if path.exists():
            return path
    return None
