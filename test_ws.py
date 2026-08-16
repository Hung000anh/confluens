from tradingview_websocket import TradingViewWebSocket
import json
import re
import time

def verify_and_get_info(symbol):
    try:
        ws = TradingViewWebSocket(symbol, "1D", 1)
        ws.connect()
        session = ws.generate_session()
        chart_session = ws.generate_chart_session()
        symbol_string = "={\"symbol\":\"" + ws.symbol + "\",\"adjustment\":\"splits\"}"
        
        ws.send_message("set_auth_token", ["unauthorized_user_token"])
        ws.send_message("chart_create_session", [chart_session, ""])
        ws.send_message("quote_create_session", [session])
        
        fields = ["ch", "chp", "current_session", "description", "local_description", "language", "exchange", "fractional", "is_tradable", "lp", "lp_time", "minmov", "minmove2", "original_name", "pricescale", "pro_name", "short_name", "type", "update_mode", "volume", "currency_code", "rchp", "rtc"]
        ws.send_message("quote_set_fields", [session] + fields)
        
        ws.send_message("quote_add_symbols", [session, ws.symbol, {"flags": ['force_permission']}])
        ws.send_message("resolve_symbol", [chart_session, "symbol_" + ws.timeframe, symbol_string])
        ws.send_message("create_series", [chart_session, "s" + ws.timeframe, "s" + ws.timeframe, "symbol_" + ws.timeframe, ws.timeframe, ws.candles])
        
        ws.ws.settimeout(2.0)
        
        all_qsd_v = []
        
        start_time = time.time()
        while time.time() - start_time < 3: # wait 3 seconds
            try:
                result = ws.ws.recv()
                data = re.split('~m~\d+~m~', result)
                for i in data:
                    if i.strip():
                        parsed_data = json.loads(i)
                        m = parsed_data.get('m')
                        
                        if m == 'qsd':
                            p = parsed_data.get('p')
                            if len(p) > 1 and p[1].get('s') == 'ok':
                                v = p[1].get('v', {})
                                if v:
                                    all_qsd_v.append(v)
                            
            except Exception as e:
                pass
                
        return all_qsd_v
                    
    except Exception as e:
        return {"error": str(e)}
        
print("=== RAW QSD DATA FOR EURUSD ===")
aapl_info = verify_and_get_info("EURUSD")
print(json.dumps(aapl_info, indent=2))
