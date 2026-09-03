"""Canlı demo için gerçekçi ticket geçmişi.

Herkese açık demo (Hugging Face Spaces) her yeniden başlatmada diski sıfırlar;
ziyaretçi boş bir dashboard görmesin diye, `DEMO_SEED_HISTORY=true` iken ve
ticket_history tablosu boşsa bu kayıtlar son ~10 güne yayılarak eklenir.
Son 7 günde 3'ten fazla "ağ" kaydı olduğu için "tekrarlayan sorun" uyarısı da
tetiklenir; birkaç kayıt manuel düzeltme örneği taşır.
"""

from datetime import datetime, timedelta, timezone

from app.config import SQLITE_DB_PATH
from app.db.database import fetch_ticket_history, insert_ticket_history, update_ticket_correction

# (gün önce, saat, metin, kategori, öncelik, ekip, düzeltilmiş kategori | None)
DEMO_HISTORY = [
    (0, 1, "VPN'e bağlanınca 30 saniye sonra bağlantı kopuyor, tekrar denemek zorunda kalıyorum", "ağ", "orta", "Network Operasyon Ekibi", None),
    (0, 3, "Outlook'ta yeni mailler gelmiyor, gönderdiklerim de giden kutusunda takılı", "yazılım", "orta", "Uygulama Destek Ekibi", None),
    (1, 2, "Toplantı odasındaki projeksiyon HDMI'dan görüntü almıyor", "donanım", "düşük", "Donanım Destek Ekibi", None),
    (1, 5, "Evden bağlanınca şirket içi portala girilemiyor, VPN açık olmasına rağmen", "ağ", "yüksek", "Network Operasyon Ekibi", None),
    (2, 1, "Yeni başlayan stajyer için e-posta ve Teams hesabı açılması gerekiyor", "erişim", "düşük", "Erişim ve Kimlik Yönetimi Ekibi", None),
    (2, 6, "Wi-Fi 4. katta çok yavaş, video görüşmeleri donuyor", "ağ", "orta", "Network Operasyon Ekibi", None),
    (3, 2, "ERP'de rapor alırken 'zaman aşımı' hatası, muhasebe kapanış yapamıyor", "yazılım", "yüksek", "Uygulama Destek Ekibi", None),
    (3, 4, "Şifremi 3 kere yanlış girdim, hesabım kilitlendi", "erişim", "orta", "Erişim ve Kimlik Yönetimi Ekibi", None),
    (4, 3, "Paylaşımlı sürücü ağda görünmüyor, 'ağ yolu bulunamadı' diyor", "erişim", "orta", "Erişim ve Kimlik Yönetimi Ekibi", "ağ"),
    (4, 7, "Laptop şarj olmuyor, adaptör ışığı yanıp sönüyor", "donanım", "yüksek", "Donanım Destek Ekibi", None),
    (5, 2, "Uzak masaüstü bağlantısı sürekli 'bağlantı kesildi' uyarısı veriyor", "ağ", "orta", "Network Operasyon Ekibi", None),
    (5, 5, "Kat yazıcısı 'kağıt sıkıştı' diyor ama kağıt yok", "donanım", "düşük", "Donanım Destek Ekibi", None),
    (6, 1, "Teams'te mikrofon çalışmıyor, karşı taraf beni duymuyor", "yazılım", "düşük", "Uygulama Destek Ekibi", "donanım"),
    (6, 4, "CRM'e giriş yaparken SSO 'oturum doğrulanamadı' hatası veriyor", "erişim", "orta", "Erişim ve Kimlik Yönetimi Ekibi", None),
    (7, 3, "Antivirüs sürekli tarama yapıyor, bilgisayar kullanılamaz hale geliyor", "yazılım", "orta", "Uygulama Destek Ekibi", None),
    (8, 2, "Sunucu odasında sıcaklık alarmı çaldı", "donanım", "yüksek", "Donanım Destek Ekibi", None),
    (9, 5, "DNS bazı iç sistemleri çözemiyor, IP ile giriyoruz", "ağ", "orta", "Network Operasyon Ekibi", None),
    (10, 1, "Lisanslı tasarım yazılımı kurulumu için talep", "yazılım", "düşük", "Uygulama Destek Ekibi", None),
]


def seed_demo_history(db_path: str = SQLITE_DB_PATH) -> int:
    """Geçmiş tablosu boşsa demo kayıtlarını ekler. Eklenen kayıt sayısını döner."""
    if fetch_ticket_history(db_path=db_path):
        return 0

    now = datetime.now(timezone.utc)
    inserted = 0
    # En eski kayıt önce eklensin ki id sırası da kronolojik olsun.
    for days_ago, hour, text, category, priority, team, corrected in reversed(DEMO_HISTORY):
        created_at = (now - timedelta(days=days_ago, hours=hour)).strftime("%Y-%m-%d %H:%M:%S")
        ticket_id = insert_ticket_history(
            text, category, priority, team, db_path=db_path, created_at=created_at
        )
        if corrected:
            update_ticket_correction(ticket_id, corrected, db_path=db_path)
        inserted += 1
    return inserted
