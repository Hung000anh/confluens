import sqlite3
from app.config.settings import DB_PATH


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

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

    for col in ['country', 'base_country', 'quote_country']:
        try:
            cursor.execute(f'ALTER TABLE symbols ADD COLUMN {col} TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

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

    for key, value in {
        "candle_count": "100",
        "bull_color": "#10b981",
        "bear_color": "#ffffff",
        "timeframes": "1m,3m,5m,15m,30m,45m,1h,2h,3h,4h,1d,1w,1m",
    }.items():
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))

    conn.commit()
    conn.close()
