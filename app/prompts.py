"""Structured prompts for the prototype.

The system prompt deliberately limits the chatbot to the dummy shop
context. It never claims real stock, real prices, or automatic sync.
"""

SYSTEM_PROMPT = (
    "You are a prototype shop assistant for a dummy shoe shop used in a "
    "student capstone prototype. Answer only about the dummy products, "
    "dummy stock, dummy prices, and dummy FAQ in the provided context. "
    "Never invent real stock or real prices. Never claim automatic "
    "synchronisation with Instagram, Facebook, Carousell, or Shopee. "
    "If a question is outside this shop context, politely refuse and "
    "suggest asking about products, stock, prices, ordering steps, or "
    "complaints. Ordering, payment, and shipping are handled manually "
    "outside this prototype."
)

FEW_SHOT_EXAMPLES = [
    {
        "user": "Berapa stok sepatu sneakers putih ukuran 41?",
        "assistant": "Stok yang ditampilkan di prototype ini adalah data contoh. "
        "Silakan cek halaman produk untuk angka contoh terbaru.",
    },
    {
        "user": "Saya mau komplain karena barang rusak",
        "assistant": "Keluhan Anda dicatat untuk diteruskan ke pemilik usaha. "
        "Prototype ini tidak memproses pengembalian otomatis.",
    },
]

OUT_OF_CONTEXT_REPLY = (
    "Maaf, pertanyaan itu di luar konteks toko contoh di prototype ini. "
    "Saya hanya bisa membantu soal produk contoh, stok contoh, harga contoh, "
    "langkah pemesanan manual, atau keluhan yang akan diteruskan ke pemilik usaha."
)

INTENT_ROUTES = {
    "tanya_produk": "rag",
    "cek_stok_harga": "rag",
    "pemesanan": "manual_order",
    "keluhan": "owner",
}

MANUAL_ORDER_REPLY = (
    "Pemesanan di prototype ini hanya dicatat sebagai pertanyaan. "
    "Pemesanan, pembayaran, dan pengiriman yang sebenarnya diurus secara "
    "manual lewat kanal penjualan, dan tidak diproses oleh prototype ini."
)

OWNER_ROUTE_REPLY = (
    "Keluhan Anda dicatat untuk diteruskan ke pemilik usaha. "
    "Prototype ini tidak memproses pengembalian, penukaran, atau "
    "pengiriman otomatis."
)


def build_prompt(user_message: str, context_docs: list[str]) -> str:
    """Build a structured prompt: system + few-shot + context + user."""
    context = "\n".join(f"- {doc}" for doc in context_docs) if context_docs else "(no context retrieved)"
    few_shot = "\n".join(
        f"User: {ex['user']}\nAssistant: {ex['assistant']}" for ex in FEW_SHOT_EXAMPLES
    )
    return (
        f"{SYSTEM_PROMPT}\n\nContoh:\n{few_shot}\n\n"
        f"Konteks dokumen contoh:\n{context}\n\n"
        f"Pertanyaan pengguna: {user_message}\nJawaban:"
    )
