from app.db.database import (
    fetch_recurring_alerts,
    fetch_ticket_history,
    init_db,
    insert_ticket_history,
    update_ticket_correction,
)


def _db(tmp_path):
    path = str(tmp_path / "history_test.db")
    init_db(path)
    return path


def test_fetch_ticket_history_starts_empty(tmp_path):
    db_path = _db(tmp_path)

    assert fetch_ticket_history(db_path=db_path) == []


def test_insert_and_fetch_history_orders_newest_first(tmp_path):
    db_path = _db(tmp_path)

    first_id = insert_ticket_history("ilk ticket", "ağ", "orta", "Network Operasyon Ekibi", db_path=db_path)
    second_id = insert_ticket_history("ikinci ticket", "donanım", "yüksek", "Donanım Destek Ekibi", db_path=db_path)

    history = fetch_ticket_history(db_path=db_path)

    assert [item["id"] for item in history] == [second_id, first_id]
    assert history[0]["ticket_text"] == "ikinci ticket"
    assert history[0]["category"] == "donanım"
    assert history[0]["corrected_category"] is None


def test_insert_ticket_history_allows_null_fields(tmp_path):
    db_path = _db(tmp_path)

    insert_ticket_history("belirsiz ticket", None, None, None, db_path=db_path)

    entry = fetch_ticket_history(db_path=db_path)[0]
    assert entry["category"] is None
    assert entry["priority"] is None
    assert entry["assigned_team"] is None


def test_update_ticket_correction_sets_corrected_category(tmp_path):
    db_path = _db(tmp_path)
    ticket_id = insert_ticket_history("bir ticket", "yazılım", "orta", "Uygulama Destek Ekibi", db_path=db_path)

    updated = update_ticket_correction(ticket_id, "ağ", db_path=db_path)

    assert updated is not None
    assert updated["id"] == ticket_id
    assert updated["corrected_category"] == "ağ"
    # Orijinal (modelin verdiği) kategori korunuyor, sadece düzeltme ayrı alanda.
    assert updated["category"] == "yazılım"


def test_update_ticket_correction_returns_none_for_missing_id(tmp_path):
    db_path = _db(tmp_path)

    assert update_ticket_correction(999, "ağ", db_path=db_path) is None


def test_fetch_recurring_alerts_does_not_trigger_at_threshold(tmp_path):
    db_path = _db(tmp_path)
    for _ in range(3):
        insert_ticket_history("ağ sorunu", "ağ", "orta", "Network Operasyon Ekibi", db_path=db_path)

    assert fetch_recurring_alerts(db_path=db_path) == []


def test_fetch_recurring_alerts_triggers_above_threshold(tmp_path):
    db_path = _db(tmp_path)
    for _ in range(4):
        insert_ticket_history("ağ sorunu", "ağ", "orta", "Network Operasyon Ekibi", db_path=db_path)

    alerts = fetch_recurring_alerts(db_path=db_path)

    assert len(alerts) == 1
    assert alerts[0]["category"] == "ağ"
    assert alerts[0]["count"] == 4
    assert alerts[0]["days"] == 7
    assert alerts[0]["threshold"] == 3


def test_fetch_recurring_alerts_only_flags_categories_over_threshold(tmp_path):
    db_path = _db(tmp_path)
    for _ in range(4):
        insert_ticket_history("ağ sorunu", "ağ", "orta", "Network Operasyon Ekibi", db_path=db_path)
    for _ in range(2):
        insert_ticket_history("donanım sorunu", "donanım", "düşük", "Donanım Destek Ekibi", db_path=db_path)

    alerts = fetch_recurring_alerts(db_path=db_path)

    assert [a["category"] for a in alerts] == ["ağ"]
