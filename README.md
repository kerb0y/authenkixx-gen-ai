# Prototype Gen AI (Capstone Authenkixx)

Ini masih prototype, ya. Dibuat oleh Ade Bintang. Semua datanya
dummy. Nggak ada data asli UMKM, nggak ada data customer, nggak ada
password, dan nggak ada sinkronisasi otomatis ke platform lain.

## Yang berubah di Fase 1 (25 Oktober 2026)

- Penolakan pertanyaan di luar konteks sekarang lebih kuat dari
  sekadar daftar kata kunci (lihat bagian baru di bawah). Hasil
  test di data dummy: 24/24 pertanyaan di luar konteks ditolak
  (10 dari v1 ditambah 14 pertanyaan baru di Fase 1), 12/12
  pertanyaan yang masih dalam konteks NGGAK ditolak, dan smoke test
  API 4/4. Kode barunya ada di `app/refusal.py`, test barunya ada di
  `tests/test_in_scope.py` dan `tests/test_out_of_context.py` yang
  sudah diperluas.
- `ChatResponse` sekarang ikut menampilkan `refusal_layer` (null
  kalau pertanyaan dijawab, atau `keyword`, `product_reference`,
  `domain_coverage`, atau `low_evidence_fallback` kalau ditolak),
  jadi pas demo kelihatan lapis mana yang bekerja.
- RAG TF-IDF NGGAK diganti jadi vector store di Fase 1, keputusan
  itu (TF-IDF vs ChromaDB/FAISS) masih terbuka buat Ade dan tim.
- Fase 1 ini sudah di-push ke GitHub.

## Masalah apa yang diselesaikan model ini

Pemilik toko itu sering banget ditanya hal yang itu-itu saja soal
produk, stok, harga, cara pesan, dan komplain, dari berbagai kanal.
Service ini tugasnya mengklasifikasikan pertanyaan ke satu intent,
mengambil dokumen FAQ atau produk dummy yang relevan, terus
mengarahkan pertanyaannya: pertanyaan produk dan stok/harga ke
retrieval prototype, pertanyaan pesanan ke catatan pesanan manual,
dan komplain ke pemilik. Yang jelas, service ini NGGAK bikin pesanan,
pembayaran, pengiriman, atau retur.

## Cara jalanin

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Dokumentasi API interaktif (Swagger/OpenAPI):
http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health

Backend Full-Stack yang jadi perantara ke service ini. Frontend
nggak pernah manggil service ini langsung.

## Preprocessing (sebelum masuk model)

`app/preprocessing.py`: diubah ke huruf kecil semua, tanda baca
dihapus, spasi berlebih dirapikan, dan stopword Bahasa Indonesia
yang kecil-kecil dibuang. Kalau input-nya kosong atau nggak ada kata
yang bisa dipakai setelah preprocessing, dibalas HTTP 422 dengan
pesan yang jelas.

## Data (cuma dummy)

- `data/dummy_intents.csv`: 48 contoh berlabel, 12 per intent.
- `data/dummy_faq.csv`: 6 dokumen FAQ dummy.
- `data/dummy_products.csv`: 6 produk dummy (bentuk katalog dummy-nya
  sama kayak inventory di Full-Stack).

Keseimbangan kelas: dataset dummy ini seimbang (12 / 12 / 12 / 12),
jadi nggak perlu resampling. LogisticRegression tetap pakai
`class_weight="balanced"` buat jaga-jaga di versi final, kalau data
aslinya ternyata nggak seimbang. Kalau nanti data aslinya memang
nggak seimbang, versi final wajib melaporkan jumlahnya, cara
menanganinya (misalnya class weight atau resampling), dan efeknya,
sebelum mengklaim hasil apa pun.

## Perbandingan model (data dummy, metrik dan split yang sama)

Split: stratified, test_size=0.25, random_state=42 (train 36,
test 12). Metrik: accuracy dan macro F1 di test set yang dipisahkan.
Jalankan: `python scripts/train_compare.py` (output-nya di
`outputs/model_comparison.json`).

| Model / konfigurasi | Accuracy (test) | Macro F1 (test) |
|---|---|---|
| TF-IDF + LogisticRegression (C=1.0) | 0.6667 | 0.5750 |
| TF-IDF + MultinomialNB | 0.6667 | 0.5685 |
| TF-IDF + LogisticRegression, tuned (C=10.0) | 0.7500 | 0.6518 |

Tuning hyperparameter: GridSearchCV buat C di [0.1, 1.0, 10.0]
dengan 3-fold CV yang cuma dipakai di training split saja, hasilnya
C terbaik 10.0 dengan CV macro F1 0.8075. Tuning ini menaikkan
accuracy test dari 0.6667 jadi 0.7500 dan macro F1 test dari 0.5750
jadi 0.6518 di dataset dummy ini.

Alasan pemilihan: LogisticRegression yang sudah di-tuning dipilih
karena accuracy dan macro F1 test-nya paling tinggi dari ketiganya.
Batasan yang jujur: test set-nya cuma 12 contoh dummy, jadi angka
ini cuma demo pipeline, bukan bukti performa buat pertanyaan asli.
Model yang dipakai service di `app/classifier.py` adalah konfigurasi
tuned (C=10.0). Versi final wajib latih ulang dan bandingkan ulang
di data yang lebih besar dan sudah diputuskan pemiliknya, terus
tabel ini diperbarui.

## Fitur AI generatif

Opsional dan default-nya mati. Atur `GENAI_API_KEY` di environment
(jangan pernah ditulis di kode, lihat `.env.example`) buat
mengaktifkan panggilan ke model proprietary. Kalau key-nya nggak
diset, `/chat` membalas jawaban RAG/template dengan status
`generative_ai: "disabled_no_api_key"`. Kalau service-nya gagal atau
timeout, jawabannya fallback ke RAG/template dengan status
`generative_ai: "failed_fell_back_to_rag"`, bukan malah crash.
Prompt terstruktur ada di `app/prompts.py` (system prompt, contoh
few-shot, dan rute intent).

## RAG (retrieval prototype, bukan integrasi vector beneran)

`app/rag.py` itu retrieval TF-IDF cosine atas dokumen FAQ dummy dan
dokumen produk dummy. Ini BUKAN ChromaDB, FAISS, Pinecone, atau
Weaviate, dan NGGAK pakai embedding model. RAG produksi dengan
embedding model dan vector store itu kerjaan lanjutan (lihat README
di root). Dokumen yang diambil selalu dilabeli dummy di tiap jawaban.

## Penolakan pertanyaan di luar konteks (Fase 1: diperkuat, tetap prototype)

Chatbot menolak pertanyaan di luar konteks toko dummy dengan pesan
yang sopan. Penolakannya sekarang pakai empat lapis, berurutan
(lihat `app/refusal.py` buat lapis yang berbasis data):

1. Guardrail kata kunci (v1, dipertahankan): daftar kata kunci topik
   di luar konteks yang eksplisit di `app/main.py`. Ini lapis
   prototype, bukan detektor out-of-distribution produksi.
2. Cek referensi produk (Fase 1, baru): kalau intent yang
   diprediksi itu `cek_stok_harga` tapi pertanyaannya nggak
   menyebut produk toko sama sekali (nggak ada kata "sepatu" dan
   nggak ada token nama produk dummy), pertanyaan ditolak. Ini
   nangkep pertanyaan harga soal barang lain yang skor
   confidence-nya bisa tinggi cuma gara-gara kata "harga" saja.
   Terukur di Fase 1: "Berapa harga tiket pesawat ke Singapura?"
   di v1 dapat confidence 0.944, karena mirip contoh latihan
   "harga sepatu", dan sekarang ditolak lewat lapis ini.
3. Domain-coverage gate (Fase 1, baru, berbasis data): tolak kalau
   SEMUA kondisi ini terpenuhi buat pertanyaan tanpa anchor produk:
   cakupan kosakata <= 0.50 (paling banter setengah token hasil
   preprocessing-nya muncul di kosakata TF-IDF dalam konteks, baik
   kosakata classifier maupun retriever, keduanya dilatih cuma dari
   data dummy), skor RAG terbaik < 0.40, cosine similarity ke contoh
   latihan terdekat < 0.60, dan confidence classifier < 0.85.
   Pengecualian anchor produk itu sengaja: pertanyaan yang menyebut
   "sepatu" (atau nama produk dummy) itu masih masuk domain produk
   toko, jadi gate ini nggak menolaknya walaupun cakupannya rendah
   (terukur: "Sepatu apa saja yang dijual di sini?" cakupannya
   0.33 tapi confidence-nya 0.87 dan anchor produknya jelas, dan
   dijawab dengan benar).
4. Fallback bukti rendah (v1, dipertahankan): tolak kalau skor RAG
   terbaik < 0.10 DAN confidence classifier < 0.35.

Threshold di atas itu nilai prototype yang di-tuning dari data
dummy, bukan jaminan produksi. Batasan yang masih ada, disampaikan
dengan jujur: ini tetap guardrail prototype, BUKAN detektor
out-of-distribution produksi. Pertanyaan yang menyebut produk toko
tapi sebenarnya soal hal lain, dan pertanyaan harga polos tanpa
menyebut produk ("Berapa harganya?" tanpa konteks produk), masih
bisa salah rute atau ketolak, karena service ini stateless dan
nggak punya riwayat percakapan. Jangan klaim deteksi OOD kelas
produksi buat service ini.

Pertanyaan di luar konteks yang sudah dites (24/24 ditolak di Fase 1,
terverifikasi dengan menjalankan `tests/test_out_of_context.py`):

1. Siapa presiden Indonesia saat ini? -> ditolak
2. Bagaimana cara memasak rendang yang enak? -> ditolak
3. Berapa skor pertandingan sepak bola semalam? -> ditolak
4. Apa ramalan cuaca besok di Jakarta? -> ditolak
5. Jelaskan teori relativitas Einstein secara detail -> ditolak
6. Berapa harga saham perusahaan teknologi hari ini? -> ditolak
7. Ceritakan dongeng sebelum tidur untuk anak -> ditolak
8. Bagaimana cara mendaftar CPNS tahun ini? -> ditolak
9. Apa itu blockchain dan bagaimana cara investasi crypto? -> ditolak
10. Tolong buatkan skripsi saya dari awal sampai akhir -> ditolak (keyword)

Set Fase 1 (14 baru, nggak ada yang mengandung kata kunci v1, ini
bukti lapis berbasis data memang menambah cakupan):
11. Bagaimana cara mengurus paspor baru? -> ditolak (domain_coverage)
12. Berapa biaya kuliah semester ini di kampus? -> ditolak (domain_coverage)
13. Tolong jelaskan cara kerja mesin mobil diesel -> ditolak (domain_coverage)
14. Apa jadwal kereta api ke Bandung besok pagi? -> ditolak (domain_coverage)
15. Bagaimana cara daftar SIM online? -> ditolak (domain_coverage)
16. Berapa gaji rata-rata programmer di Jakarta? -> ditolak (domain_coverage)
17. Tolong buatkan itinerary liburan ke Bali 3 hari -> ditolak (domain_coverage)
18. Siapa pemenang lomba menyanyi tadi malam? -> ditolak (domain_coverage)
19. Bagaimana cara beternak ayam petelur di rumah? -> ditolak (domain_coverage)
20. Berapa harga tiket pesawat ke Singapura? -> ditolak (product_reference)
21. Jelaskan sejarah kerajaan Majapahit secara singkat -> ditolak (domain_coverage)
22. Apa manfaat olahraga lari pagi untuk jantung? -> ditolak (domain_coverage)
23. Bagaimana cara mengajukan KPR rumah pertama? -> ditolak (domain_coverage)
24. Berapa tarif parkir di mal Jakarta Selatan? -> ditolak (domain_coverage)

Test tandingan dalam konteks (Fase 1, wajib NGGAK ditolak,
terverifikasi dengan menjalankan `tests/test_in_scope.py`): 12/12
nggak ditolak. Pertanyaannya mencakup stok, harga, ketersediaan
produk, langkah pemesanan, dan komplain, semuanya menyebut produk
toko atau konteks toko yang jelas (contohnya "Berapa stok sepatu
sneakers putih?", "Bagaimana cara memesan sepatu sneakers hitam?",
dan "Sepatu saya rusak setelah dipakai seminggu, bagaimana
komplainnya?"). File ini ada buat membuktikan penolakan yang lebih
kuat ini nggak asal menolak semuanya.

## Kalau input nggak valid dan service gagal

- Pesan kosong: HTTP 422 dengan pesan yang jelas.
- JSON nggak valid atau tipe datanya salah: error validasi
  FastAPI/Pydantic.
- Service generatif down atau lambat: jawaban fallback, status yang
  jelas di field `generative_ai`, tanpa crash.
- Proxy backend down: backend Full-Stack membalas HTTP 502 dengan
  pesan yang jelas (lihat README fullstack).

## Test

```bash
python tests/test_out_of_context.py   # 24/24 ditolak (Fase 1, terverifikasi)
python tests/test_in_scope.py         # 12/12 nggak ditolak (Fase 1, terverifikasi)
python -c "from tests.test_api import *; ..."  # lihat test_api.py (4 smoke test, terverifikasi)
```

Catatan: `tests/test_api.py` pakai FastAPI TestClient, yang butuh
package `httpx` yang sudah ada di requirements.txt.

## Disclaimer

Lihat CHECKLIST_STATUS.md di repo ini. Fase 1 bukan versi final.
Target akhirnya adalah menyesuaikan dokumen use case Authenkixx dan
memenuhi semua checklist Main Quest buat Full-Stack, Gen AI, dan
Data Science. Fase 1 belum mengklaim sudah memenuhi semuanya.
