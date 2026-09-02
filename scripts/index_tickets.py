"""Mock ticket'ları SQLite'tan okuyup Chroma vector store'una embed'ler.

Kullanım (proje kök dizininden, Ollama çalışır durumdayken):
    python -m scripts.index_tickets
"""

from app.db.database import fetch_all_tickets, init_db, seed_if_empty
from app.rag.vector_store import get_vector_store, index_tickets


def main() -> None:
    init_db()
    seed_if_empty()
    tickets = fetch_all_tickets()

    vector_store = get_vector_store()
    count = index_tickets(vector_store, tickets)
    print(f"{count} ticket Chroma vector store'una eklendi/güncellendi.")


if __name__ == "__main__":
    main()
