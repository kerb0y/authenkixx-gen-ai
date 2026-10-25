"""Out-of-context tests: 24 questions that must be refused (Phase 1).

v1 set (10): refused mainly by the keyword guardrail.
Phase 1 set (14 new): none of these contains a v1 keyword, so they
are the proof that the new data-driven layers add coverage. In the
Phase 1 measurements, 13 of the 14 were refused by the
domain-coverage gate (no product anchor + coverage <= 0.50 +
RAG < 0.40 + nearest-training similarity < 0.60 + confidence < 0.85)
and 1 (the flight-ticket price question) was refused by the
product-reference check, because its predicted intent is
cek_stok_harga but it names no shop product, even though its
classifier confidence reached 0.944 in v1 from the word "harga"
alone. All figures are from dummy-data test runs, not real users.

Run (no server, no API key needed):
  python tests/test_out_of_context.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

OUT_OF_CONTEXT_QUESTIONS = [
    # v1 set (10)
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
    # Phase 1 set (14 new, no v1 keyword)
    "Bagaimana cara mengurus paspor baru?",
    "Berapa biaya kuliah semester ini di kampus?",
    "Tolong jelaskan cara kerja mesin mobil diesel",
    "Apa jadwal kereta api ke Bandung besok pagi?",
    "Bagaimana cara daftar SIM online?",
    "Berapa gaji rata-rata programmer di Jakarta?",
    "Tolong buatkan itinerary liburan ke Bali 3 hari",
    "Siapa pemenang lomba menyanyi tadi malam?",
    "Bagaimana cara beternak ayam petelur di rumah?",
    "Berapa harga tiket pesawat ke Singapura?",
    "Jelaskan sejarah kerajaan Majapahit secara singkat",
    "Apa manfaat olahraga lari pagi untuk jantung?",
    "Bagaimana cara mengajukan KPR rumah pertama?",
    "Berapa tarif parkir di mal Jakarta Selatan?",
]

if __name__ == "__main__":
    client = TestClient(app)
    refused = 0
    for q in OUT_OF_CONTEXT_QUESTIONS:
        r = client.post("/chat", json={"message": q})
        body = r.json()
        ok = body["route"] == "refused_out_of_context"
        refused += int(ok)
        print(f"{'REFUSED' if ok else 'NOT REFUSED'}: {q} -> {body['route']} (layer={body.get('refusal_layer')})")
    print(f"Refused {refused}/{len(OUT_OF_CONTEXT_QUESTIONS)} out-of-context questions")


def test_all_refused():
    client = TestClient(app)
    for q in OUT_OF_CONTEXT_QUESTIONS:
        r = client.post("/chat", json={"message": q})
        assert r.status_code == 200
        assert r.json()["route"] == "refused_out_of_context"
