from app.agent.tools import assign_team, get_priority


def test_get_priority_high_keyword():
    result = get_priority.invoke(
        {"category": "ağ", "keywords": "üretim sunucusu çöktü, tüm ekip etkilendi"}
    )
    assert result == "yüksek"


def test_get_priority_low_keyword():
    result = get_priority.invoke(
        {"category": "erişim", "keywords": "yeni işe başlayan için hesap talebi"}
    )
    assert result == "düşük"


def test_get_priority_falls_back_to_category_default():
    assert get_priority.invoke({"category": "erişim", "keywords": "genel bir soru"}) == "düşük"
    assert get_priority.invoke({"category": "ağ", "keywords": "genel bir soru"}) == "orta"


def test_assign_team_known_categories():
    assert assign_team.invoke({"category": "donanım"}) == "Donanım Destek Ekibi"
    assert assign_team.invoke({"category": "yazılım"}) == "Uygulama Destek Ekibi"
    assert assign_team.invoke({"category": "ağ"}) == "Network Operasyon Ekibi"
    assert assign_team.invoke({"category": "erişim"}) == "Erişim ve Kimlik Yönetimi Ekibi"


def test_assign_team_unknown_category_falls_back_to_service_desk():
    assert assign_team.invoke({"category": "bilinmeyen"}) == "Service Desk"
