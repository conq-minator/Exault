import os
import json
from pathlib import Path
from flask import Blueprint, jsonify, request
import config

notes_bp = Blueprint("notes_bp", __name__)

@notes_bp.route("/api/notes", methods=["GET"])
def list_notes():
    """List all saved notes."""
    try:
        notes = []
        if config.NOTES_DIR.exists():
            for f in config.NOTES_DIR.glob("*.txt"):
                notes.append({"name": f.stem, "filename": f.name})
        return jsonify(notes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notes_bp.route("/api/notes/<note_name>", methods=["GET"])
def get_note(note_name: str):
    """Get content of a specific note."""
    try:
        file_path = config.NOTES_DIR / f"{note_name}.txt"
        if not file_path.exists():
            return jsonify({"error": "Note not found"}), 404
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return jsonify({"name": note_name, "content": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notes_bp.route("/api/notes/<note_name>", methods=["POST"])
def save_note(note_name: str):
    """Save content to a specific note."""
    try:
        data = request.json
        if not data or "content" not in data:
            return jsonify({"error": "Missing content"}), 400
            
        file_path = config.NOTES_DIR / f"{note_name}.txt"
        
        # Check if exists and not overwriting
        overwrite = data.get("overwrite", False)
        if file_path.exists() and not overwrite:
            return jsonify({"error": "Note already exists"}), 409
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data["content"])
            
        return jsonify({"success": True, "name": note_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notes_bp.route("/api/notes/<note_name>", methods=["DELETE"])
def delete_note(note_name: str):
    """Delete a specific note."""
    try:
        file_path = config.NOTES_DIR / f"{note_name}.txt"
        if file_path.exists():
            file_path.unlink()
            return jsonify({"success": True}), 200
        return jsonify({"error": "Note not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
