import sqlite3
import os
import re

DB_NAME = "conflues.db"

def get_db_connection():
    """
    Tạo kết nối tới database SQLite
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Để truy cập các cột qua tên như dictionary
    return conn

def init_db():
    """
    Khởi tạo bảng symbols nếu chưa tồn tại
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tạo bảng nếu chưa tồn tại
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS symbols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            exchange TEXT NOT NULL,
            type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            country TEXT DEFAULT '',
            base_country TEXT DEFAULT '',
            quote_country TEXT DEFAULT ''
        )
    ''')

    # Cập nhật schema nếu bảng đã tồn tại từ trước mà chưa có cột country, base_country, quote_country
    try:
        cursor.execute('ALTER TABLE symbols ADD COLUMN country TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE symbols ADD COLUMN base_country TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE symbols ADD COLUMN quote_country TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass

    # Tạo bảng settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Tạo bảng indicators
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            period INTEGER NOT NULL,
            color TEXT DEFAULT '#10b981',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Thiết lập giá trị mặc định cho settings nếu chưa có
    default_settings = {
        "candle_count": "100",
        "bull_color": "#10b981",
        "bear_color": "#ffffff",
        "timeframes": "1m,3m,5m,15m,30m,45m,1h,2h,3h,4h,1d,1w,1m"
    }
    for k, v in default_settings.items():
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        ''', (k, v))

    conn.commit()
    conn.close()
    
def save_symbols_to_db(symbols: list, exchange: str, asset_type: str, country: str = "", base_country: str = "", quote_country: str = ""):
    """
    Lưu danh sách mã giao dịch vào CSDL
    """
    if not symbols:
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Chuẩn hóa (viết hoa và xóa khoảng trắng thừa)
    exchange = exchange.strip().upper() if exchange else ""
    country = country.strip().upper() if country else ""
    base_country = base_country.strip().upper() if base_country else ""
    quote_country = quote_country.strip().upper() if quote_country else ""

    # Nếu không truyền country chung nhưng có base/quote, ghép làm country đại diện
    if not country and (base_country or quote_country):
        parts = [p for p in [base_country, quote_country] if p]
        country = " / ".join(parts)

    # Tạo danh sách các tham số để lưu
    data_to_insert = [(sym.strip().upper(), exchange, asset_type, country, base_country, quote_country) for sym in symbols if sym.strip()]

    cursor.executemany('''
        INSERT INTO symbols (symbol, exchange, type, country, base_country, quote_country)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', data_to_insert)

    conn.commit()
    conn.close()

def get_all_symbols():
    """
    Lấy danh sách tất cả các mã giao dịch từ CSDL
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM symbols ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_symbol(symbol_id: int):
    """
    Xóa một mã giao dịch khỏi CSDL
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM symbols WHERE id = ?', (symbol_id,))
    conn.commit()
    conn.close()

def update_symbol(symbol_id: int, symbol: str, exchange: str, asset_type: str, country: str = "", base_country: str = "", quote_country: str = ""):
    """
    Cập nhật thông tin mã giao dịch
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Chuẩn hóa (viết hoa và xóa khoảng trắng thừa)
    exchange = exchange.strip().upper() if exchange else ""
    country = country.strip().upper() if country else ""
    base_country = base_country.strip().upper() if base_country else ""
    quote_country = quote_country.strip().upper() if quote_country else ""

    if not country and (base_country or quote_country):
        parts = [p for p in [base_country, quote_country] if p]
        country = " / ".join(parts)

    cursor.execute('''
        UPDATE symbols
        SET symbol = ?, exchange = ?, type = ?, country = ?, base_country = ?, quote_country = ?
        WHERE id = ?
    ''', (symbol.strip().upper(), exchange, asset_type, country, base_country, quote_country, symbol_id))
    conn.commit()
    conn.close()

def get_setting(key: str, default: str = "") -> str:
    """
    Lấy một giá trị cài đặt từ CSDL
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["value"]
    return default

def set_setting(key: str, value: str):
    """
    Lưu một giá trị cài đặt vào CSDL
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    ''', (key, value))
    conn.commit()
    conn.close()

def parse_indicator_timeframes(value):
    """
    Chuyển khung thời gian sang danh sách chuẩn.
    Hỗ trợ kiểu string hoặc list/tuple.
    """
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        raw = []
        for item in value:
            raw.extend(str(item).split(','))
    else:
        raw = str(value).split(',')

    cleaned = []
    for part in raw:
        for token in re.split(r'[|;\s]+', str(part).strip()):
            token = token.strip().lower()
            if token:
                cleaned.append(token)

    ordered = ['1m', '3m', '5m', '15m', '30m', '45m', '1h', '2h', '3h', '4h', '1d', '1w', '1M', '3M', '6M', '12M']
    unique = []
    for tf in ordered:
        if tf.lower() in [x.lower() for x in cleaned]:
            unique.append(tf)
    for tf in cleaned:
        if tf not in [x.lower() for x in unique]:
            unique.append(tf)
    return unique


def stringify_indicator_timeframes(value):
    """Trả về chuỗi dạng comma-separated, chuẩn hóa key"""
    return ','.join(parse_indicator_timeframes(value))


def get_all_indicators():
    """
    Lấy danh sách tất cả các chỉ báo
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM indicators ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_active_indicators_by_timeframe(timeframe: str):
    """
    Lấy danh sách các chỉ báo đang bật theo timeframe.
    Hỗ trợ một chỉ báo có nhiều khung thời gian (1d,1w,...).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM indicators WHERE is_active = 1 ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()

    requested = str(timeframe).strip().lower()
    matched = []
    for row in [dict(r) for r in rows]:
        tf_values = parse_indicator_timeframes(row.get('timeframe', ''))
        if requested in tf_values:
            matched.append(row)
    return matched


def add_indicator(name: str, type_: str, timeframe, period: int, color: str = "#10b981"):
    """
    Thêm chỉ báo mới
    """
    timeframe_value = stringify_indicator_timeframes(timeframe)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO indicators (name, type, timeframe, period, color, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (name.strip(), type_.strip().lower(), timeframe_value, period, color.strip()))
    conn.commit()
    conn.close()


def update_indicator(indicator_id: int, name: str, type_: str, timeframe, period: int, color: str = "#10b981"):
    """
    Cập nhật chỉ báo
    """
    timeframe_value = stringify_indicator_timeframes(timeframe)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE indicators
        SET name = ?, type = ?, timeframe = ?, period = ?, color = ?
        WHERE id = ?
    ''', (name.strip(), type_.strip().lower(), timeframe_value, period, color.strip(), indicator_id))
    conn.commit()
    conn.close()

def delete_indicator(indicator_id: int):
    """
    Xóa một chỉ báo
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM indicators WHERE id = ?', (indicator_id,))
    conn.commit()
    conn.close()

def toggle_indicator(indicator_id: int):
    """
    Bật/tắt trạng thái chỉ báo
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE indicators SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?', (indicator_id,))
    conn.commit()
    conn.close()
