"""Out-of-context test: 10 questions that must be refused.

Run with the service logic directly (no server needed):
  python -m pytest tests/test_out_of_context.py -q   (if pytest installed)
or simply:  python tests/test_out_of_context.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

OUT_OF_CONTEXT_QUESTIONS = [
    "Siapa presiden Indonesia saat ini?",
    "Bagaimana cara memasak rendang yang enak?",
    "Berapa skor pertandingan sepak bola semalam?",
    "Apa ramalan cuaca besok di Jakarta?",
    "Jelaskan teori relativitas Einstein secara detail",
    "Berapa harga saham perusahaan teknologi hari ini?",
    "Ceritakan dongeng sebelum tidur untuk anak",
    "Bagaimana cara mendaftar CPNS tahun ini?",
    "Apa itu blockchain dan bagaimana cara investasi crypto?",
    "Tolong buatkan skripsi saya dari awal sampai akhir",
]

if __name__ == "__main__":
    client = TestClient(app)
    refused = 0
    for q in OUT_OF_CONTEXT_QUESTIONS:
        r = client.post("/chat", json={"message": q})
        body = r.json()
        ok = body["route"] == "refused_out_of_context"
        refused += int(ok)
        print(f"{'REFUSED' if ok else 'NOT REFUSED'}: {q} -> {body['route']}")
    print(f"Refused {refused}/{len(OUT_OF_CONTEXT_QUESTIONS)} out-of-context questions")


def test_all_refused():
    client = TestClient(app)
    for q in OUT_OF_CONTEXT_QUESTIONS:
        r = client.post("/chat", json={"message": q})
        assert r.status_code == 200
        assert r.json()["route"] == "refused_out_of_context"
