"""
Exault — Application Entry Point

Starts the Flask server and opens the browser.

Usage:
    python run.py
"""

import webbrowser
import threading
import sys

import config
from backend.app import create_app
from backend.utils.logging_config import setup_logging


def open_browser(host: str, port: int) -> None:
    """Open the default browser to the application URL after a short delay."""
    import time
    time.sleep(1.5)  # Wait for server to start
    url = f"http://{host}:{port}"
    print(f"\n  -> Opening browser: {url}\n")
    webbrowser.open(url)


def main() -> None:
    """Initialize and start the Exault application."""
    # Ensure required directories exist
    config.ensure_directories()

    # Set up logging
    logger = setup_logging()
    logger.info("Starting Exault v1.0.0")

    # Create Flask application
    app = create_app()

    # Auto-open browser in a background thread
    if config.AUTO_OPEN_BROWSER:
        import os
        # If in debug mode, only open browser in the reloader child process to avoid duplicate tabs
        if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            threading.Thread(
                target=open_browser,
                args=(config.HOST, config.PORT),
                daemon=True
            ).start()

    # Print startup banner
    print("\n" + "=" * 60)
    print("  Exault — AI Spreadsheet Mapping Framework")
    print("=" * 60)
    print(f"  Server:  http://{config.HOST}:{config.PORT}")
    print(f"  Debug:   {config.DEBUG}")
    print(f"  Data:    {config.DATA_DIR}")
    print("=" * 60)
    print("  Press Ctrl+C to stop the server.\n")

    # Start Flask server
    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            use_reloader=config.DEBUG
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
        print("\n  Server stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
