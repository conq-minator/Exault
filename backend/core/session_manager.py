"""
ExcelPlorer — Session Manager

SQLite-backed session manager for persisting session metadata.
"""

import sqlite3
import datetime
import shutil
import logging
from typing import List, Dict, Optional
from pathlib import Path

import config

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages session lifecycle and persistence."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = config.SESSIONS_DIR / "sessions.db"
        else:
            self.db_path = db_path
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection with row factory set."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initialize the database schema."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL
                )
            """)
            conn.commit()

    def create_session(self, session_id: str, original_filename: str, file_size: int) -> None:
        """Create a new session record."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO sessions (session_id, original_filename, file_size, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, original_filename, file_size, now, now))
            conn.commit()
        logger.info(f"Created session record for {session_id}")

    def list_sessions(self) -> List[Dict]:
        """List all sessions ordered by creation time descending."""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get details for a specific session."""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            
            if row:
                # Update last accessed
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                conn.execute("UPDATE sessions SET last_accessed = ? WHERE session_id = ?", (now, session_id))
                conn.commit()
                return dict(row)
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session from the DB and remove its files."""
        # Remove from DB
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return False
        
        # Remove files
        session_dir = config.SESSIONS_DIR / session_id
        if session_dir.exists():
            try:
                shutil.rmtree(session_dir)
                logger.info(f"Deleted files for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to delete directory {session_dir}: {e}")
        
        return True

# Global instance for use in routes
session_manager = SessionManager()
