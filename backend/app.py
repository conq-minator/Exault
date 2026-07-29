"""
ExcelPlorer — Flask Application Factory

Creates and configures the Flask application instance.
Registers all API blueprints and sets up middleware.
"""

import logging
import mimetypes
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

import config

# Fix for Windows mimetypes registry bug
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)
    
    # ─── Configuration ──────────────────────────────────────────────────
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE
    app.config["SECRET_KEY"] = "excelplorer-local-dev-key"

    # ─── CORS ────────────────────────────────────────────────────────────
    CORS(app)

    # ─── Register Blueprints ─────────────────────────────────────────────
    _register_blueprints(app)

    # ─── Error Handlers ──────────────────────────────────────────────────
    _register_error_handlers(app)

    # ─── Root & Static Routes ────────────────────────────────────────────
    @app.route("/")
    def index():
        """Serve the main SPA page."""
        return send_from_directory(str(config.FRONTEND_DIR), "index.html")
        
    @app.route("/<path:path>")
    def serve_static(path):
        """Serve static files (css, js, etc.) or fallback to index.html for SPA routing."""
        import os
        # Check if file exists in frontend dir
        full_path = config.FRONTEND_DIR / path
        if full_path.is_file():
            return send_from_directory(str(config.FRONTEND_DIR), path)
            
        # If it's an API route that wasn't caught, return 404
        if path.startswith("api/"):
            from flask import abort
            abort(404)
            
        # Otherwise fallback to index.html for client-side routing
        return send_from_directory(str(config.FRONTEND_DIR), "index.html")

    logger.info("Flask application created successfully.")
    return app


def _register_blueprints(app: Flask) -> None:
    """Register all API route blueprints."""
    from backend.api.upload import upload_bp
    from backend.api.analysis import analysis_bp
    from backend.api.prompt import prompt_bp
    from backend.api.validate import validate_bp
    from backend.api.preview import preview_bp
    from backend.api.export import export_bp
    from backend.api.report import report_bp
    from backend.api.session import session_bp
    from backend.api.products import products_bp

    blueprints = [
        upload_bp,
        analysis_bp,
        prompt_bp,
        validate_bp,
        preview_bp,
        export_bp,
        report_bp,
        session_bp,
        products_bp,
    ]

    for bp in blueprints:
        app.register_blueprint(bp)
        logger.debug(f"Registered blueprint: {bp.name}")


def _register_error_handlers(app: Flask) -> None:
    """Register global error handlers for consistent JSON error responses."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "Bad Request",
            "message": str(error.description),
            "status": 400
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found.",
            "status": 404
        }), 404

    @app.errorhandler(413)
    def file_too_large(error):
        max_mb = config.MAX_UPLOAD_SIZE / (1024 * 1024)
        return jsonify({
            "error": "File Too Large",
            "message": f"File exceeds maximum upload size of {max_mb:.0f} MB.",
            "status": 413
        }), 413

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Check the server logs.",
            "status": 500
        }), 500
