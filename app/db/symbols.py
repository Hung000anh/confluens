from typing import List, Optional
from app.db.base import get_db_connection
from app.db.countries import resolve_country_code
from app.models.base import SymbolCreate, SymbolUpdate


def create_symbol(symbol: SymbolCreate) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO symbols (symbol, exchange, type, country, base_country, quote_country)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        symbol.symbol.strip().upper(),
        symbol.exchange.strip().upper() if symbol.exchange else "",
        symbol.type,
        resolve_country_code(symbol.country),
        resolve_country_code(symbol.base_country),
        resolve_country_code(symbol.quote_country),
    ))
    conn.commit()
    symbol_id = cursor.lastrowid
    conn.close()
    return symbol_id


def get_all_symbols() -> List[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM symbols ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_symbol_by_id(symbol_id: int) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM symbols WHERE id = ?', (symbol_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_symbol(symbol_id: int, symbol: SymbolUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    update_data = []
    update_fields = []

    if symbol.symbol:
        update_fields.append('symbol = ?')
        update_data.append(symbol.symbol.strip().upper())
    if symbol.exchange is not None:
        update_fields.append('exchange = ?')
        update_data.append(symbol.exchange.strip().upper() if symbol.exchange else "")
    if symbol.type:
        update_fields.append('type = ?')
        update_data.append(symbol.type)
    if symbol.country is not None:
        update_fields.append('country = ?')
        update_data.append(resolve_country_code(symbol.country))
    if symbol.base_country is not None:
        update_fields.append('base_country = ?')
        update_data.append(resolve_country_code(symbol.base_country))
    if symbol.quote_country is not None:
        update_fields.append('quote_country = ?')
        update_data.append(resolve_country_code(symbol.quote_country))

    if update_fields:
        update_data.append(symbol_id)
        query = f"UPDATE symbols SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_data)
        conn.commit()

    conn.close()


def delete_symbol(symbol_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM symbols WHERE id = ?', (symbol_id,))
    conn.commit()
    conn.close()


def create_multiple_symbols(symbols: List[str], exchange: str, asset_type: str,
                           country: str = "", base_country: str = "", quote_country: str = ""):
    if not symbols:
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    exchange = exchange.strip().upper() if exchange else ""
    country = resolve_country_code(country)
    base_country = resolve_country_code(base_country)
    quote_country = resolve_country_code(quote_country)

    if not country and (base_country or quote_country):
        country = ' / '.join(part for part in [base_country, quote_country] if part)

    data_to_insert = [
        (sym.strip().upper(), exchange, asset_type, country, base_country, quote_country)
        for sym in symbols if sym.strip()
    ]

    cursor.executemany('''
        INSERT INTO symbols (symbol, exchange, type, country, base_country, quote_country)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', data_to_insert)

    conn.commit()
    conn.close()
