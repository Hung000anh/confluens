import json
import logging
import random
import re
import string
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import requests
import websocket

from app.services.countries import CountryService

logger = logging.getLogger(__name__)

SCANNER_URL = "https://scanner.tradingview.com/economics2/scan"
WS_URL = "wss://data.tradingview.com/socket.io/websocket?from=symbols%2F&date=2026_08_01-12_00"

# Bộ nhớ tạm metadata WebSocket cho các symbol kinh tế
_QUOTE_METADATA_CACHE: Dict[str, Dict[str, Any]] = {}

FREQ_MAP: Dict[str, str] = {
    "D": "Hàng ngày",
    "W": "Hàng tuần",
    "M": "Hàng tháng",
    "3M": "Hàng quý",
    "12M": "Hàng năm",
    "6M": "6 Tháng",
}


def _gen_session_id(prefix: str = "qs_") -> str:
    return prefix + "".join(random.choices(string.ascii_lowercase + string.digits, k=12))


def _prepend_header(msg: str) -> str:
    return f"~m~{len(msg)}~m~{msg}"


def _create_message(func: str, params: list) -> str:
    return _prepend_header(json.dumps({"m": func, "p": params}))


def fetch_economic_quotes_metadata(symbols: List[str], timeout: float = 3.5) -> Dict[str, Dict[str, Any]]:
    """
    Kết nối WebSocket tới TradingView để lấy data_frequency và reference-last-period chính xác 100%
    cho danh sách symbols (vd: ["ECONOMICS:USGDP", "ECONOMICS:USCPI"]).
    """
    missing_symbols = [s for s in symbols if s not in _QUOTE_METADATA_CACHE or not _QUOTE_METADATA_CACHE[s].get("data_frequency")]
    if not missing_symbols:
        return _QUOTE_METADATA_CACHE

    chunk_size = 120
    for i in range(0, len(missing_symbols), chunk_size):
        chunk = missing_symbols[i:i + chunk_size]
        ws = None
        try:
            ws = websocket.create_connection(
                WS_URL,
                header=[
                    "Origin: https://www.tradingview.com",
                    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0",
                ],
                timeout=timeout,
            )
            session_id = _gen_session_id()
            fields = ["data_frequency", "reference-last-period"]
            messages = [
                _create_message("quote_create_session", [session_id]),
                _create_message("quote_set_fields", [session_id, *fields]),
                _create_message("quote_add_symbols", [session_id, *chunk]),
            ]
            for m in messages:
                ws.send(m)

            pending = set(chunk)
            start_t = time.time()
            while pending and (time.time() - start_t) < timeout:
                raw = ws.recv()
                for match in re.findall(r"~m~\d+~m~({.*?})(?=~m~|\Z)", raw, re.S):
                    try:
                        data = json.loads(match)
                    except Exception:
                        continue
                    if data.get("m") == "qsd":
                        p = data.get("p", [])
                        if len(p) >= 2:
                            sym = p[1].get("n")
                            val = p[1].get("v", {})
                            if sym:
                                _QUOTE_METADATA_CACHE.setdefault(sym, {}).update(val)
                                if "data_frequency" in _QUOTE_METADATA_CACHE[sym] or "reference-last-period" in _QUOTE_METADATA_CACHE[sym]:
                                    pending.discard(sym)
        except Exception as exc:
            logger.debug("WebSocket quote fetch exception: %s", exc)
        finally:
            if ws:
                try:
                    ws.close()
                except Exception:
                    pass

    return _QUOTE_METADATA_CACHE


CATEGORIES_MAP: Dict[str, Dict[str, str]] = {
    "all": {"label": "Tất cả chỉ số", "icon": ""},
    "gdp": {"label": "GDP & Tăng trưởng", "icon": ""},
    "prce": {"label": "Giá cả & Lạm phát", "icon": ""},
    "lbr": {"label": "Lao động & Việc làm", "icon": ""},
    "mny": {"label": "Tiền tệ & Lãi suất", "icon": ""},
    "trd": {"label": "Thương mại & Cán cân", "icon": ""},
    "bsnss": {"label": "Sản xuất & Doanh nghiệp", "icon": ""},
    "gov": {"label": "Chính phủ & Nợ công", "icon": ""},
    "cnsm": {"label": "Tiêu dùng & Bán lẻ", "icon": ""},
    "hse": {"label": "Bất động sản & Nhà ở", "icon": ""},
    "clmt": {"label": "Khí hậu & Môi trường", "icon": ""},
    "hlth": {"label": "Y tế & Xã hội", "icon": ""},
    "txs": {"label": "Thuế", "icon": ""},
    "enrg": {"label": "Năng lượng", "icon": ""},
}

# Danh mục các chỉ số cốt lõi phục vụ đối chiếu so sánh
COMPARISON_BENCHMARKS = [
    {
        "id": "gdp_growth",
        "title": "Tăng trưởng GDP (YoY / Full Year)",
        "category": "gdp",
        "keywords": ["full year gdp growth", "gdp growth rate", "gdp annual growth rate", "gdp growth"],
        "unit": "%",
        "higher_is_better": True,
    },
    {
        "id": "gdp_total",
        "title": "Tổng sản phẩm quốc nội (GDP)",
        "category": "gdp",
        "keywords": [" gdp", "gross domestic product"],
        "exact_symbols": ["USGDP", "VNGDP", "CNGDP", "EUGDP", "JPGDP", "DEGDP", "GBGDP", "INGDP", "CAGDP", "AUGDP", "CHGDP"],
        "unit": "USD / Cur",
        "higher_is_better": True,
    },
    {
        "id": "inflation_rate",
        "title": "Tỷ lệ Lạm phát (Inflation Rate YoY)",
        "category": "prce",
        "keywords": ["inflation rate yoy", "consumer price index yoy", "inflation rate"],
        "unit": "%",
        "higher_is_better": False,
    },
    {
        "id": "core_inflation",
        "title": "Lạm phát cốt lõi (Core Inflation YoY)",
        "category": "prce",
        "keywords": ["core inflation rate yoy", "core consumer prices yoy", "core inflation rate"],
        "unit": "%",
        "higher_is_better": False,
    },
    {
        "id": "interest_rate",
        "title": "Lãi suất điều hành (Central Bank Rate)",
        "category": "mny",
        "keywords": ["interest rate", "policy rate", "refinancing rate", "cash rate"],
        "unit": "%",
        "higher_is_better": None,
    },
    {
        "id": "unemployment_rate",
        "title": "Tỷ lệ Thất nghiệp (Unemployment Rate)",
        "category": "lbr",
        "keywords": ["unemployment rate"],
        "exclude_keywords": ["youth", "long term", "u6"],
        "unit": "%",
        "higher_is_better": False,
    },
    {
        "id": "govt_debt_gdp",
        "title": "Nợ công / GDP (Govt Debt to GDP)",
        "category": "gov",
        "keywords": ["government debt to gdp", "debt to gdp"],
        "unit": "%",
        "higher_is_better": False,
    },
    {
        "id": "balance_of_trade",
        "title": "Cán cân Thương mại (Balance of Trade)",
        "category": "trd",
        "keywords": ["balance of trade", "trade balance"],
        "unit": "Cur",
        "higher_is_better": True,
    },
    {
        "id": "current_account_gdp",
        "title": "Cán cân vãng lai / GDP (Current Account)",
        "category": "trd",
        "keywords": ["current account to gdp", "current account balance to gdp"],
        "unit": "%",
        "higher_is_better": True,
    },
    {
        "id": "manufacturing_pmi",
        "title": "Chỉ số PMI Sản xuất (Manufacturing PMI)",
        "category": "bsnss",
        "keywords": ["manufacturing pmi", "manufacturing pmi flash"],
        "unit": "Point",
        "benchmark_value": 50.0,
        "higher_is_better": True,
    },
    {
        "id": "population",
        "title": "Dân số (Population)",
        "category": "lbr",
        "keywords": ["population"],
        "unit": "Người",
        "higher_is_better": None,
    },
]


def format_value(value: Optional[float], measure: Optional[str] = None, unit_id: Optional[str] = None) -> Optional[str]:
    """Format số theo kiểu T/B/M/K + đơn vị (USD, %, point...)"""
    if value is None:
        return None

    suffix = ""
    v = float(value)
    abs_v = abs(v)

    if abs_v >= 1e12:
        v, suffix = v / 1e12, "T"
    elif abs_v >= 1e9:
        v, suffix = v / 1e9, "B"
    elif abs_v >= 1e6:
        v, suffix = v / 1e6, "M"
    elif abs_v >= 1e3 and unit_id not in ["POINT", "PCT"]:
        v, suffix = v / 1e3, "K"

    # Xác định đơn vị
    if measure == "percent" or unit_id == "PCT":
        unit = "%"
    elif measure == "currency":
        unit = "USD"
    elif unit_id and unit_id not in ["POINT", "unit", "INDEX"]:
        unit = unit_id
    else:
        unit = ""

    formatted_num = f"{v:,.2f}{suffix}"
    if formatted_num.endswith(".00" + suffix):
        formatted_num = f"{int(v):,}{suffix}"
    elif formatted_num.endswith("0" + suffix) and "." in formatted_num:
        formatted_num = f"{v:,.1f}{suffix}"

    return f"{formatted_num} {unit}".strip()


def format_observation(ts: Optional[int]) -> Optional[str]:
    """Fallback format thời gian quan sát từ timestamp nếu quote metadata chưa có"""
    if ts is None:
        return None
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return f"{dt.day} {dt.strftime('%b %Y')}"
    except Exception:
        return None


class EconomicIndicatorsService:
    @staticmethod
    def get_country_lookup() -> Dict[str, str]:
        """Lấy danh sách mã quốc gia -> tên quốc gia"""
        try:
            countries = CountryService.get_all()
            return {item["code"]: item["name"] for item in countries if item.get("code")}
        except Exception:
            return {}

    @classmethod
    def get_indicators_by_countries(
        cls,
        country_codes: List[str],
        category: Optional[str] = None,
        limit: int = 1500,
    ) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các chỉ số kinh tế của các quốc gia đã chọn từ TradingView Economics Scanner
        và làm giàu thêm metadata (data_frequency, reference-last-period) từ WebSocket TradingView.
        """
        clean_codes = [c.strip().upper() for c in country_codes if c and c.strip()]
        if not clean_codes:
            clean_codes = ["US"]

        filters = []
        if len(clean_codes) == 1:
            filters.append({
                "left": "country_code",
                "operation": "equal",
                "right": clean_codes[0]
            })
        else:
            filters.append({
                "left": "country_code",
                "operation": "in_range",
                "right": clean_codes
            })

        if category and category != "all" and category in CATEGORIES_MAP:
            filters.append({
                "left": "economic-category-id",
                "operation": "equal",
                "right": category
            })

        payload = {
            "columns": [
                "name",
                "description",
                "country_code",
                "economic-category-id",
                "measure",
                "close",
                "change_abs",
                "time",
                "value-unit-id"
            ],
            "filter": filters,
            "sort": {
                "sortBy": "name",
                "sortOrder": "asc"
            },
            "range": [0, limit]
        }

        try:
            res = requests.post(SCANNER_URL, json=payload, timeout=10)
            res.raise_for_status()
            data = res.json().get("data", [])
        except Exception as exc:
            logger.error("Lỗi khi tải dữ liệu từ TradingView Economics Scanner: %s", exc)
            return []

        # Tải metadata (data_frequency & reference-last-period) trực tiếp từ WebSocket TradingView
        tickers = [item.get("s", "") for item in data if item.get("s")]
        if tickers:
            fetch_economic_quotes_metadata(tickers, timeout=3.5)

        country_lookup = cls.get_country_lookup()
        rows: List[Dict[str, Any]] = []

        for item in data:
            s_ticker = item.get("s", "")
            symbol = s_ticker.split(":", 1)[1] if ":" in s_ticker else s_ticker
            d = item.get("d", [])
            if len(d) < 9:
                continue

            name, desc, country_code, cat_id, measure, close, change_abs, ts, unit_id = d[:9]
            previous = (close - change_abs) if (close is not None and change_abs is not None) else None

            # Tính phần trăm thay đổi nếu có
            pct_change = None
            if previous is not None and previous != 0 and change_abs is not None:
                pct_change = (change_abs / abs(previous)) * 100

            cat_info = CATEGORIES_MAP.get(cat_id or "", {"label": cat_id or "Khác", "icon": ""})

            # Lấy data_frequency và observation từ WebSocket metadata
            meta = _QUOTE_METADATA_CACHE.get(s_ticker, {})
            raw_freq = meta.get("data_frequency")
            freq = FREQ_MAP.get(raw_freq, raw_freq or "-")
            obs = meta.get("reference-last-period") or format_observation(ts)

            rows.append({
                "symbol": symbol,
                "name": name or symbol,
                "indicator": desc or name or symbol,
                "country_code": country_code or "",
                "country_name": country_lookup.get(country_code, country_code),
                "category_id": cat_id or "other",
                "category_name": cat_info["label"],
                "category_icon": cat_info["icon"],
                "data_frequency": freq,
                "raw_frequency": raw_freq,
                "measure": measure,
                "unit_id": unit_id,
                "raw_last": close,
                "raw_previous": previous,
                "raw_change": change_abs,
                "raw_pct_change": pct_change,
                "last": format_value(close, measure, unit_id),
                "previous": format_value(previous, measure, unit_id),
                "change": format_value(change_abs, measure, unit_id) if change_abs is not None else None,
                "observation": obs,
                "raw_time": ts,
            })
        return rows
