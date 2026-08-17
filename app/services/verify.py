import json
import re
import time
from typing import Dict, List
from tradingview_websocket import TradingViewWebSocket


class VerificationService:
    @staticmethod
    def verify_symbols(symbols: List[str], exchange: str = "") -> Dict[str, bool]:
        results = {}
        for symbol in symbols:
            symbol_to_check = symbol.strip().upper()
            if not symbol_to_check:
                continue

            check_str = f"{exchange.upper()}:{symbol_to_check}" if exchange else symbol_to_check
            try:
                ws = TradingViewWebSocket(check_str, "1D", 1)
                ws.connect()
                session = ws.generate_session()
                chart_session = ws.generate_chart_session()
                symbol_string = '={"symbol":"' + ws.symbol + '","adjustment":"splits"}'

                ws.send_message("set_auth_token", ["unauthorized_user_token"])
                ws.send_message("chart_create_session", [chart_session, ""])
                ws.send_message("quote_create_session", [session])
                ws.send_message("quote_set_fields", [session, "ch"])
                ws.send_message("quote_add_symbols", [session, ws.symbol, {"flags": ["force_permission"]}])
                ws.send_message("resolve_symbol", [chart_session, "symbol_" + ws.timeframe, symbol_string])
                ws.send_message("create_series", [chart_session, "s" + ws.timeframe, "s" + ws.timeframe, "symbol_" + ws.timeframe, ws.timeframe, ws.candles])

                ws.ws.settimeout(2.0)
                is_valid = True
                start_time = time.time()

                while time.time() - start_time < 2:
                    try:
                        result = ws.ws.recv()
                        data = re.split(r'~m~\d+~m~', result)
                        for item in data:
                            if item.strip():
                                parsed_data = json.loads(item)
                                if parsed_data.get('m') == 'symbol_error':
                                    is_valid = False
                                    break
                                elif parsed_data.get('m') in ['timescale_update', 'series_completed']:
                                    break
                        if not is_valid:
                            break
                    except Exception:
                        pass
                results[symbol_to_check] = is_valid
            except Exception:
                results[symbol_to_check] = False

        return results
