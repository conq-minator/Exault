"""
ExcelPlorer — Tests for Products API
"""

import json
import pytest
from flask import Flask

import config
from backend.app import create_app


@pytest.fixture
def app(tmp_path):
    """Create and configure a new app instance for each test."""
    # Override config paths for testing
    config.DATA_DIR = tmp_path
    config.PRODUCTS_DIR = tmp_path / "products"
    
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    
    # Create products dir
    config.PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    
    yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def sample_product():
    return {
        "Seller SKU ID": "TEST-123",
        "Product Title": "Test Product",
        "Price": 100
    }


def test_list_products_empty(client):
    response = client.get("/api/products")
    assert response.status_code == 200
    assert response.json == []


def test_save_and_list_product(client, sample_product):
    # Save product
    response = client.post(
        "/api/products/TEST-123",
        json=sample_product
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"
    
    # List products
    response = client.get("/api/products")
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["sku"] == "TEST-123"
    assert response.json[0]["title"] == "Test Product"


def test_get_product(client, sample_product):
    client.post("/api/products/TEST-123", json=sample_product)
    
    response = client.get("/api/products/TEST-123")
    assert response.status_code == 200
    assert response.json["Seller SKU ID"] == "TEST-123"


def test_get_product_not_found(client):
    response = client.get("/api/products/MISSING-999")
    assert response.status_code == 404


def test_save_product_conflict(client, sample_product):
    # First save
    client.post("/api/products/TEST-123", json=sample_product)
    
    # Second save without overwrite
    response = client.post("/api/products/TEST-123", json=sample_product)
    assert response.status_code == 409
    assert "already exists" in response.json["message"]
    
    # Second save WITH overwrite
    response = client.post("/api/products/TEST-123?overwrite=true", json=sample_product)
    assert response.status_code == 200


def test_delete_product(client, sample_product):
    client.post("/api/products/TEST-123", json=sample_product)
    
    # Delete it
    response = client.delete("/api/products/TEST-123")
    assert response.status_code == 200
    
    # Verify it's gone
    response = client.get("/api/products/TEST-123")
    assert response.status_code == 404
