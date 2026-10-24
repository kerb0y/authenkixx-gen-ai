"""Smoke tests for the Gen AI service (no server, no API key needed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chat_in_context():
    r = client.post("/chat", json={"message": "Berapa stok sepatu sneakers putih?"})
    assert r.status_code == 200
    assert r.json()["route"] in ("rag", "manual_order", "owner")


def test_invalid_input():
    r = client.post("/chat", json={"message": "   "})
    assert r.status_code == 422


def test_generative_disabled_without_key():
    # No GENAI_API_KEY is set in the test environment.
    r = client.post("/chat", json={"message": "Apa saja warna sepatu yang tersedia?"})
    assert r.status_code == 200
    assert r.json()["generative_ai"] != "used"
