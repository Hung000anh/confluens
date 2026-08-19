import json
from typing import List, Optional

from app.config.settings import COUNTRIES_JSON_PATH
from app.db.base import get_db_connection


def seed_countries(conn=None):
    if not COUNTRIES_JSON_PATH.exists():
        return

    payload = json.loads(COUNTRIES_JSON_PATH.read_text(encoding="utf-8"))
    rows = []
    for item in payload:
        code = str(item.get("code", "")).strip().upper()
        name = str(item.get("name", "")).strip()
        if code and name:
            rows.append((code, name))

    if not rows:
        return

    close_conn = conn is None
    if close_conn:
        conn = get_db_connection()

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR REPLACE INTO countries (code, name) VALUES (?, ?)",
        rows,
    )

    if close_conn:
        conn.commit()
        conn.close()


def get_all_countries() -> List[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code, name FROM countries ORDER BY name COLLATE NOCASE")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_country_by_code(code: str) -> Optional[dict]:
    normalized = (code or "").strip().upper()
    if not normalized:
        return None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code, name FROM countries WHERE code = ?", (normalized,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def resolve_country_code(code: str) -> str:
    normalized = (code or "").strip().upper()
    if not normalized:
        return ""

    country = get_country_by_code(normalized)
    if not country:
        raise ValueError(f"Quốc gia '{code}' không tồn tại trong danh mục")
    return country["code"]
