import re
from typing import List, Optional
from app.db.base import get_db_connection
from app.models.base import IndicatorCreate, IndicatorUpdate


def parse_indicator_timeframes(value) -> List[str]:
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


def stringify_indicator_timeframes(value: str) -> str:
    return ','.join(parse_indicator_timeframes(value))


def create_indicator(indicator: IndicatorCreate) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    timeframe_value = stringify_indicator_timeframes(indicator.timeframe)

    cursor.execute('''
        INSERT INTO indicators (name, type, timeframe, period, color, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (
        indicator.name.strip(),
        indicator.type.strip().lower(),
        timeframe_value,
        indicator.period,
        indicator.color.strip(),
    ))

    conn.commit()
    indicator_id = cursor.lastrowid
    conn.close()
    return indicator_id


def get_all_indicators() -> List[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM indicators ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_indicator_by_id(indicator_id: int) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM indicators WHERE id = ?', (indicator_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_indicator(indicator_id: int, indicator: IndicatorUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    update_data = []
    update_fields = []

    if indicator.name:
        update_fields.append('name = ?')
        update_data.append(indicator.name.strip())
    if indicator.type:
        update_fields.append('type = ?')
        update_data.append(indicator.type.strip().lower())
    if indicator.timeframe:
        update_fields.append('timeframe = ?')
        update_data.append(stringify_indicator_timeframes(indicator.timeframe))
    if indicator.period:
        update_fields.append('period = ?')
        update_data.append(indicator.period)
    if indicator.color:
        update_fields.append('color = ?')
        update_data.append(indicator.color.strip())

    if update_fields:
        update_data.append(indicator_id)
        query = f"UPDATE indicators SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_data)
        conn.commit()

    conn.close()


def delete_indicator(indicator_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM indicators WHERE id = ?', (indicator_id,))
    conn.commit()
    conn.close()


def toggle_indicator(indicator_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE indicators SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?',
        (indicator_id,),
    )
    conn.commit()
    conn.close()


def get_active_indicators_by_timeframe(timeframe: str) -> List[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM indicators WHERE is_active = 1 ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()

    requested = str(timeframe).strip().lower()
    matched = []
    for row in [dict(r) for r in rows]:
        tf_values = parse_indicator_timeframes(row.get('timeframe', ''))
        if requested in [x.lower() for x in tf_values]:
            matched.append(row)
    return matched
