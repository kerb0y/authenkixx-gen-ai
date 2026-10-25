"""In-scope tests (Phase 1, plus Nike catalogue update): 13 questions
that must NOT be refused.

This file exists to prove the stronger refusal did not simply
refuse everything. Every question below names a shop product or a
clear shop context (order, complaint, stock, price, channel label),
so the product-anchor and domain-coverage gates must let it through
to a real route (rag, manual_order, or owner). All data is dummy.
The 13th question was added with the Nike dummy catalogue: a Nike
model name alone must count as a product anchor, even without the
word "sepatu".

Run (no server, no API key needed):
  python tests/test_in_scope.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

IN_SCOPE_QUESTIONS = [
    "Berapa stok sepatu sneakers putih?",
    "Apakah sepatu kasual cokelat masih tersedia?",
    "Berapa harga sepatu slip-on abu?",
    "Sepatu apa saja yang dijual di sini?",
    "Bagaimana cara memesan sepatu sneakers hitam?",
    "Saya mau pesan sepatu lari ringan, bagaimana caranya?",
    "Sepatu saya rusak setelah dipakai seminggu, bagaimana komplainnya?",
    "Saya kecewa, pesanan saya belum sampai, siapa yang bisa bantu?",
    "Apakah ada sepatu ukuran 42?",
    "Berapa harga sepatu sneakers merah?",
    "Kapan stok sepatu merah akan ditambah?",
    "Toko ini jual sepatu apa saja di Instagram?",
    "Berapa stok Nike Air Force 1?",
]

ALLOWED_ROUTES = {"rag", "manual_order", "owner"}

if __name__ == "__main__":
    client = TestClient(app)
    passed = 0
    for q in IN_SCOPE_QUESTIONS:
        r = client.post("/chat", json={"message": q})
        body = r.json()
        ok = body["route"] in ALLOWED_ROUTES
        passed += int(ok)
        print(f"{'OK' if ok else 'REFUSED (BAD)'}: {q} -> {body['route']} (intent={body.get('intent')})")
    print(f"Not refused {passed}/{len(IN_SCOPE_QUESTIONS)} in-scope questions")


def test_none_refused():
    client = TestClient(app)
    for q in IN_SCOPE_QUESTIONS:
        r = client.post("/chat", json={"message": q})
        assert r.status_code == 200
        assert r.json()["route"] in ALLOWED_ROUTES
