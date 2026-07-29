"""
ExcelPlorer — Products API Routes

Manages the local product library, allowing users to save, load, and delete
product JSONs indexed by SKU ID.
"""

import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, request

import config

logger = logging.getLogger(__name__)

products_bp = Blueprint("products", __name__, url_prefix="/api/products")


@products_bp.route("", methods=["GET"])
def list_products():
    """List all stored products."""
    products_dir = config.PRODUCTS_DIR
    
    if not products_dir.exists():
        return jsonify([]), 200
        
    skus = []
    for file_path in products_dir.glob("*.json"):
        sku = file_path.stem
        
        # Read the file to get a title or metadata if needed, but for now just sku
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Optional: try to extract a meaningful title for display
            title = sku
            if isinstance(data, dict):
                title = data.get("Product Title", data.get("Title", sku))
                
            skus.append({
                "sku": sku,
                "title": title
            })
        except Exception:
            # If a file is corrupted, still list it by SKU
            skus.append({"sku": sku, "title": sku})
            
    # Sort by SKU
    skus.sort(key=lambda x: str(x["sku"]).lower())
    return jsonify(skus), 200


@products_bp.route("/<sku>", methods=["GET"])
def get_product(sku: str):
    """Retrieve a specific product JSON."""
    file_path = config.PRODUCTS_DIR / f"{sku}.json"
    
    if not file_path.exists():
        return jsonify({"error": "Product not found"}), 404
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Failed to read product {sku}: {e}")
        return jsonify({"error": "Failed to read product file"}), 500


@products_bp.route("/<sku>", methods=["POST"])
def save_product(sku: str):
    """
    Save or update a product JSON.
    Query params:
        overwrite (bool): If false, returns 409 Conflict if product exists.
    """
    file_path = config.PRODUCTS_DIR / f"{sku}.json"
    overwrite = request.args.get("overwrite", "false").lower() == "true"
    
    if file_path.exists() and not overwrite:
        return jsonify({
            "error": "Conflict",
            "message": f"Product with SKU '{sku}' already exists in the library."
        }), 409
        
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    try:
        config.PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "success", "sku": sku}), 200
    except Exception as e:
        logger.error(f"Failed to save product {sku}: {e}")
        return jsonify({"error": "Failed to save product"}), 500




@products_bp.route("/<sku>", methods=["DELETE"])
def delete_product(sku: str):
    """Delete a specific product."""
    file_path = config.PRODUCTS_DIR / f"{sku}.json"
    
    if not file_path.exists():
        return jsonify({"error": "Product not found"}), 404
        
    try:
        file_path.unlink()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Failed to delete product {sku}: {e}")
        return jsonify({"error": "Failed to delete product"}), 500
