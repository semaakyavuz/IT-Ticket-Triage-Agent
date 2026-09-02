"""SQLite veritabanını oluşturur ve mock ticket verisiyle doldurur.

Kullanım (proje kök dizininden):
    python -m scripts.init_db
"""

from app.db.database import fetch_all_tickets, init_db, seed_if_empty


def main() -> None:
    init_db()
    inserted = seed_if_empty()
    total = len(fetch_all_tickets())
    if inserted:
        print(f"{inserted} mock ticket eklendi. Toplam kayıt: {total}")
    else:
        print(f"Veritabanı zaten dolu, ekleme yapılmadı. Toplam kayıt: {total}")


if __name__ == "__main__":
    main()
