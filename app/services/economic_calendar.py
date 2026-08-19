import requests
import calendar
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any

# Map từ mã quốc gia của TradingView sang đồng tiền tương ứng
COUNTRY_TO_CURRENCY = {
    "US": "USD", "EU": "EUR", "GB": "GBP", "JP": "JPY",
    "CA": "CAD", "AU": "AUD", "CH": "CHF", "NZ": "NZD"
}

# Map mức độ tác động từ TradingView sang hệ thống hiện tại
IMPACT_MAP = {
    -1: "low",
    0: "medium",
    1: "high"
}

class EconomicCalendarService:
    @staticmethod
    def scrape_month(year: int, month: int) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các sự kiện lịch kinh tế từ TradingView API.
        Không lưu CSDL, lấy trực tiếp realtime theo dải ngày.
        """
        # Xác định ngày đầu và ngày cuối của tháng
        last_day = calendar.monthrange(year, month)[1]

        # Format dải ngày ISO dạng: YYYY-MM-DD
        from_date = f"{year}-{month:02d}-01T00:00:00Z"
        to_date = f"{year}-{month:02d}-{last_day:02d}T23:59:59Z"

        # Danh sách quốc gia được TradingView hỗ trợ cho các đồng tiền tệ chính
        # US: USD, EU: EUR, GB: GBP, JP: JPY, CA: CAD, AU: AUD, CH: CHF, NZ: NZD
        countries = list(COUNTRY_TO_CURRENCY.keys())

        # Xây dựng URL endpoint của TradingView Economic Calendar
        # Ví dụ: https://economic-calendar.tradingview.com/events?from=...&to=...&countries=US,EU...
        params = {
            "from": from_date,
            "to": to_date,
            "countries": ",".join(countries),
            "importance": "-1,0,1" # Lọc tất cả các tầm ảnh hưởng: Low, Medium, High
        }

        url = f"https://economic-calendar.tradingview.com/events?{urllib.parse.urlencode(params)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.tradingview.com/",
            "Origin": "https://www.tradingview.com"
        }

        try:
            print(f"Fetching TradingView Economic Calendar API: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            # API trả về list trực tiếp hoặc bọc trong dictionary {"status": "ok", "result": [...]}
            data_json = response.json()
            if isinstance(data_json, dict) and "result" in data_json:
                raw_events = data_json["result"]
            elif isinstance(data_json, dict) and "events" in data_json:
                raw_events = data_json["events"]
            else:
                raw_events = data_json

            print(f"Successfully fetched {len(raw_events)} events from TradingView")

            # Chuẩn hóa dữ liệu tương thích 100% với giao diện hiện tại
            processed_events = []
            for ev in raw_events:
                # Trích xuất thời gian
                # TradingView trả về time dạng giây epoch hoặc chuỗi ngày ISO hoặc trường "date"
                ts = ev.get("date") or ev.get("time")
                if ts:
                    try:
                        # Thường là chuỗi "2026-08-03T01:30:00.000Z" hoặc tương tự
                        cleaned_ts = str(ts).replace(".000Z", "Z")
                        if "T" in cleaned_ts:
                            dt_obj = datetime.strptime(cleaned_ts.split(".")[0].rstrip("Z"), "%Y-%m-%dT%H:%M:%S")
                        else:
                            dt_obj = datetime.utcfromtimestamp(int(ts))
                        date_str = dt_obj.strftime("%Y-%m-%d")
                        time_str = dt_obj.strftime("%H:%M")
                    except Exception as parse_err:
                        print(f"Time parse error for {ts}: {parse_err}")
                        date_str = str(ts)[:10] if ts else "-"
                        time_str = "-"
                else:
                    date_str = "-"
                    time_str = "-"

                # Ánh xạ quốc gia sang đồng tiền
                country_code = ev.get("country", "").upper()
                currency = COUNTRY_TO_CURRENCY.get(country_code, country_code)

                # Ánh xạ mức độ tác động (importance: -1 -> low, 0 -> medium, 1 -> high)
                importance = ev.get("importance")
                impact = IMPACT_MAP.get(importance, "low")

                # Lấy các giá trị Actual, Forecast, Previous
                actual = ev.get("actual")
                forecast = ev.get("forecast")
                previous = ev.get("previous")

                # Format hiển thị giá trị số nếu có
                def format_num_val(val) -> str:
                    if val is None:
                        return ""
                    try:
                        # Thử ép kiểu số để hiển thị cho đẹp
                        num = float(val)
                        return f"{num:,.2f}".rstrip('0').rstrip('.')
                    except ValueError:
                        return str(val)

                processed_events.append({
                    "date": date_str,
                    "time": time_str,
                    "utc_iso": ts,
                    "currency": currency,
                    "event": ev.get("title", ""),
                    "impact": impact,
                    "actual": format_num_val(actual),
                    "forecast": format_num_val(forecast),
                    "previous": format_num_val(previous),
                })

            # Sắp xếp các sự kiện tăng dần theo Ngày và Giờ
            processed_events.sort(key=lambda x: (x["date"], x["time"]))
            return processed_events

        except Exception as e:
            print(f"Error calling TradingView Calendar API: {e}")
            import traceback
            traceback.print_exc()
            return []
