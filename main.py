from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import jinja2
from jinja2 import Environment, FileSystemLoader
import json
import re
import time
from tradingview_websocket import TradingViewWebSocket
import os
from database import init_db, get_all_symbols, save_symbols_to_db, delete_symbol, update_symbol, get_db_connection, get_setting, set_setting, get_all_indicators, get_active_indicators_by_timeframe, add_indicator, update_indicator, delete_indicator, toggle_indicator
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import pandas as pd
import numpy as np
import mplfinance as mpf

# Khởi tạo database
init_db()

app = FastAPI(title="Conflues")

# Thiết lập thư mục static (CSS, JS, Images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Thiết lập Jinja2 trực tiếp
env = Environment(loader=FileSystemLoader("templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Render trang chủ với danh sách mã giao dịch và modal thêm/sửa
    """
    symbols = get_all_symbols()
    template = env.get_template("index.html")
    return HTMLResponse(template.render(request=request, symbols=symbols, current_path="/"))

class VerifyRequest(BaseModel):
    symbols: list[str]
    exchange: str = ""

@app.post("/verify_symbol")
async def verify_symbol(req: VerifyRequest):
    """
    Xác minh danh sách symbol qua TradingView WebSocket
    """
    results = {}
    for sym in req.symbols:
        symbol_to_check = sym.strip().upper()
        if not symbol_to_check:
            continue
            
        if req.exchange:
            check_str = f"{req.exchange.upper()}:{symbol_to_check}"
        else:
            check_str = symbol_to_check
            
        try:
            ws = TradingViewWebSocket(check_str, "1D", 1)
            ws.connect()
            session = ws.generate_session()
            chart_session = ws.generate_chart_session()
            symbol_string = "={\"symbol\":\"" + ws.symbol + "\",\"adjustment\":\"splits\"}"
            
            ws.send_message("set_auth_token", ["unauthorized_user_token"])
            ws.send_message("chart_create_session", [chart_session, ""])
            ws.send_message("quote_create_session", [session])
            ws.send_message("quote_set_fields", [session, "ch"])
            ws.send_message("quote_add_symbols", [session, ws.symbol, {"flags": ['force_permission']}])
            ws.send_message("resolve_symbol", [chart_session, "symbol_" + ws.timeframe, symbol_string])
            ws.send_message("create_series", [chart_session, "s" + ws.timeframe, "s" + ws.timeframe, "symbol_" + ws.timeframe, ws.timeframe, ws.candles])
            
            ws.ws.settimeout(2.0)
            is_valid = True
            
            start_time = time.time()
            while time.time() - start_time < 2:
                try:
                    result = ws.ws.recv()
                    data = re.split('~m~\d+~m~', result)
                    for i in data:
                        if i.strip():
                            parsed_data = json.loads(i)
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
        except Exception as e:
            results[symbol_to_check] = False
            
    return {"results": results}

@app.post("/add_symbol", response_class=HTMLResponse)
async def add_symbol(
    request: Request,
    symbol: list[str] = Form(...),
    exchange: str = Form(""),
    asset_type: str = Form(...),
    country: str = Form(""),
    base_country: str = Form(""),
    quote_country: str = Form("")
):
    """
    Xử lý khi người dùng submit form thêm mã giao dịch (hỗ trợ nhiều dòng và phân tách dấu phẩy)
    """
    # Lấy dữ liệu từ tất cả các ô input có name="symbol"
    symbols_list = []
    for sym_group in symbol:
        for s in sym_group.split(','):
            if s.strip():
                symbols_list.append(s.strip())

    print(f"Received request to save symbols {symbols_list} of type {asset_type} on {exchange} (Base: {base_country}, Quote: {quote_country})")

    # Lưu vào SQLite
    save_symbols_to_db(symbols_list, exchange, asset_type, country, base_country, quote_country)

    # Trả về trang chủ sau khi thêm thành công
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete_symbol/{symbol_id}")
async def delete_symbol_endpoint(symbol_id: int):
    """
    API xóa symbol
    """
    delete_symbol(symbol_id)
    return {"status": "success"}

@app.post("/edit_symbol/{symbol_id}")
async def edit_symbol_endpoint(
    symbol_id: int,
    request: Request,
    symbol: str = Form(...),
    exchange: str = Form(""),
    asset_type: str = Form(...),
    country: str = Form(""),
    base_country: str = Form(""),
    quote_country: str = Form("")
):
    """
    Xử lý lưu khi người dùng sửa 1 mã
    """
    update_symbol(symbol_id, symbol, exchange, asset_type, country, base_country, quote_country)
    return RedirectResponse(url="/", status_code=303)

@app.get("/charts", response_class=HTMLResponse)
async def charts_page(request: Request, symbol_id: int = None, timeframe: str = "1d"):
    """
    Trang xem biểu đồ riêng
    """
    symbols = get_all_symbols()
    active_timeframes = get_setting("timeframes", "1d,1w,1m").split(",")
    active_indicators = [ind for ind in get_all_indicators() if ind.get("is_active") == 1]

    indicators_param = request.query_params.get("indicators")
    selected_indicator_ids = []
    if indicators_param is not None:
        raw_ids = [item.strip() for item in indicators_param.split(",") if item.strip()]
        for item in raw_ids:
            try:
                selected_indicator_ids.append(int(item))
            except ValueError:
                continue
    elif active_indicators:
        selected_indicator_ids = [int(ind["id"]) for ind in active_indicators]

    template = env.get_template("chart.html")
    return HTMLResponse(template.render(
        request=request,
        symbols=symbols,
        current_path="/charts",
        selected_id=symbol_id,
        selected_timeframe=timeframe,
        active_timeframes=active_timeframes,
        active_timeframes_json=json.dumps(active_timeframes),
        active_indicators=active_indicators,
        selected_indicator_ids=selected_indicator_ids
    ))

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, msg: str = ""):
    """
    Trang Cài đặt
    """
    candle_count = get_setting("candle_count", "100")
    bull_color = get_setting("bull_color", "#10b981")
    bear_color = get_setting("bear_color", "#ffffff")

    template = env.get_template("settings.html")
    return HTMLResponse(template.render(
        request=request,
        current_path="/settings",
        candle_count=candle_count,
        bull_color=bull_color,
        bear_color=bear_color,
        message=msg
    ))

@app.get("/indicators", response_class=HTMLResponse)
async def indicators_page(request: Request):
    """
    Trang quản lý chỉ báo
    """
    indicators = get_all_indicators()
    template = env.get_template("indicators.html")
    return HTMLResponse(template.render(
        request=request,
        current_path="/indicators",
        indicators=indicators
    ))

@app.post("/add_indicator", response_class=HTMLResponse)
async def add_indicator_endpoint(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    timeframe: list[str] = Form(...),
    period: int = Form(...),
    color: str = Form("#10b981")
):
    """
    Thêm chỉ báo mới
    """
    add_indicator(name, type, timeframe, period, color)
    return RedirectResponse(url="/indicators", status_code=303)

@app.post("/update_indicator/{indicator_id}", response_class=HTMLResponse)
async def update_indicator_endpoint(
    indicator_id: int,
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    timeframe: list[str] = Form(...),
    period: int = Form(...),
    color: str = Form("#10b981")
):
    """
    Cập nhật chỉ báo
    """
    update_indicator(indicator_id, name, type, timeframe, period, color)
    return RedirectResponse(url="/indicators", status_code=303)

@app.post("/delete_indicator/{indicator_id}")
async def delete_indicator_endpoint(indicator_id: int):
    """
    Xóa chỉ báo
    """
    delete_indicator(indicator_id)
    return RedirectResponse(url="/indicators", status_code=303)

@app.post("/toggle_indicator/{indicator_id}")
async def toggle_indicator_endpoint(indicator_id: int):
    """
    Bật/tắt trạng thái chỉ báo
    """
    toggle_indicator(indicator_id)
    return RedirectResponse(url="/indicators", status_code=303)

@app.post("/settings", response_class=HTMLResponse)
async def save_settings_endpoint(
    request: Request,
    candle_count: str = Form("100"),
    bull_color: str = Form("#10b981"),
    bear_color: str = Form("#ffffff")
):
    """
    Lưu thông tin cài đặt từ form
    """
    set_setting("candle_count", candle_count)
    set_setting("bull_color", bull_color)
    set_setting("bear_color", bear_color)

    return RedirectResponse(url="/settings?msg=C%E1%BA%A5u%20h%C3%ACnh%20%C4%91%C3%A3%20%C4%91%C6%B0%E1%BB%A3c%20l%C6%B0u%20th%C3%A0nh%20c%C3%B4ng!", status_code=303)

COLOR_BULL = "#10b981" # Xanh lá
COLOR_BEAR = "#ffffff" # Trắng
COLOR_LINE = "#2196F3"

_STYLE = mpf.make_mpf_style(
    marketcolors=mpf.make_marketcolors(
        up=COLOR_BULL, down=COLOR_BEAR,
        edge="inherit", wick="inherit",
        volume="in",
    ),
    rc={
        "axes.grid":         True,
        "axes.titlesize":    13,
        "font.size":         11,
        "axes.labelsize":    9,
        "figure.facecolor":  "#212121",
        "axes.facecolor":    "#212121",
        "savefig.facecolor": "#212121",
        "axes.edgecolor":    "#555555",
        "axes.labelcolor":   "#ffffff",
        "xtick.color":       "#ffffff",
        "ytick.color":       "#ffffff",
        "text.color":        "#ffffff",
        "grid.color":        "#3a3a3a",
        "grid.linestyle":    "--",
        "grid.linewidth":    0.6,
        "grid.alpha":        0.5,
    },
)

def _compute_custom_ticks(df: pd.DataFrame, timeframe: str):
    """
    Tính toán vị trí các mốc tick tự nhiên và định dạng nhãn theo khung thời gian:
    - 1, 3, 5 phút: tick ở đầu mỗi giờ (HH:00) hoặc mỗi 30 phút, nhãn HH:MM
    - 15, 30, 45 phút: tick ở đầu mỗi 2-4 giờ, nhãn HH:MM
    - 1h, 2h, 3h, 4h: tick ở cây nến đầu tiên của mỗi ngày mới, nhãn DD/MM
    - 1d: tick ở cây nến đầu tiên của mỗi tháng mới, nhãn MM/YYYY
    - 1w: tick ở cây nến đầu tiên của mỗi quý (T1, T4, T7, T10), nhãn Qx/YYYY
    - 1M, 3M, 6M, 12M: tick ở cây nến đầu tiên của mỗi năm mới, nhãn YYYY
    """
    tf = timeframe.lower()
    dates = df.index
    positions = []
    labels = []

    if len(dates) == 0:
        return positions, labels

    if tf in ['1', '3', '5']:
        # Mốc đầu mỗi giờ tròn (phút == 0 hoặc cây nến đầu tiên của giờ mới)
        last_hour = None
        for i, dt in enumerate(dates):
            if last_hour is None or dt.hour != last_hour:
                positions.append(i)
                labels.append(dt.strftime("%H:%M"))
                last_hour = dt.hour
    elif tf in ['15', '30', '45']:
        # Mốc mỗi 2 hoặc 4 giờ (hoặc đầu ngày mới)
        last_hour_group = None
        for i, dt in enumerate(dates):
            hour_group = (dt.date(), dt.hour // 4)
            if last_hour_group is None or hour_group != last_hour_group:
                positions.append(i)
                labels.append(dt.strftime("%d/%m %H:%M") if dt.hour == 0 else dt.strftime("%H:%M"))
                last_hour_group = hour_group
    elif tf in ['1h', '2h', '3h', '4h']:
        # Cây nến đầu tiên của mỗi ngày mới
        last_day = None
        for i, dt in enumerate(dates):
            if last_day is None or dt.date() != last_day:
                positions.append(i)
                labels.append(dt.strftime("%d/%m"))
                last_day = dt.date()
    elif tf == '1d':
        # Cây nến đầu tiên của mỗi tháng mới
        last_month = None
        for i, dt in enumerate(dates):
            ym = (dt.year, dt.month)
            if last_month is None or ym != last_month:
                positions.append(i)
                labels.append(dt.strftime("%m/%Y"))
                last_month = ym
    elif tf == '1w':
        # Cây nến đầu tiên của mỗi quý (T1, T4, T7, T10) hoặc mỗi năm
        last_quarter = None
        for i, dt in enumerate(dates):
            quarter = (dt.year, (dt.month - 1) // 3 + 1)
            if last_quarter is None or quarter != last_quarter:
                positions.append(i)
                labels.append(f"Q{quarter[1]}/{dt.year}")
                last_quarter = quarter
    elif tf in ['1m', '3m', '6m', '12m']:
        # Cây nến đầu tiên của mỗi năm mới
        last_year = None
        for i, dt in enumerate(dates):
            if last_year is None or dt.year != last_year:
                positions.append(i)
                labels.append(dt.strftime("%Y"))
                last_year = dt.year
    else:
        return None, None

    # Nếu quá ít ticks (< 2) hoặc quá nhiều (> 10), điều tiết tỉ lệ lấy mẫu
    if len(positions) > 10:
        step = max(1, len(positions) // 6)
        positions = positions[::step]
        labels = labels[::step]

    return positions, labels

@app.get("/view_chart/{symbol_id}")
async def view_chart(request: Request, symbol_id: int, timeframe: str = "1d"):
    """
    Tạo biểu đồ nến với mplfinance
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM symbols WHERE id = ?', (symbol_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return HTMLResponse("Not found", status_code=404)

    symbol = row["symbol"]
    exchange = row["exchange"]

    indicators_param = request.query_params.get("indicators")
    selected_indicator_ids = []
    if indicators_param is not None:
        raw_ids = [item.strip() for item in indicators_param.split(",") if item.strip()]
        for item in raw_ids:
            try:
                selected_indicator_ids.append(int(item))
            except ValueError:
                continue

    # Đọc cấu hình từ DB
    try:
        candle_count = int(get_setting("candle_count", "100"))
    except ValueError:
        candle_count = 100
    bull_color = get_setting("bull_color", "#10b981")
    bear_color = get_setting("bear_color", "#ffffff")

    style = mpf.make_mpf_style(
        marketcolors=mpf.make_marketcolors(
            up=bull_color, down=bear_color,
            edge="inherit", wick="inherit",
            volume="in",
        ),
        rc={
            "axes.grid":         True,
            "axes.titlesize":    13,
            "font.size":         11,
            "axes.labelsize":    9,
            "figure.facecolor":  "#18181b",
            "axes.facecolor":    "#18181b",
            "savefig.facecolor": "#18181b",
            "axes.edgecolor":    "#555555",
            "axes.labelcolor":   "#ffffff",
            "xtick.color":       "#ffffff",
            "ytick.color":       "#ffffff",
            "text.color":        "#ffffff",
            "grid.color":        "#3a3a3a",
            "grid.linestyle":    "--",
            "grid.linewidth":    0.6,
            "grid.alpha":        0.5,
        },
    )

    if exchange and exchange != 'ECONOMICS':
        check_str = f"{exchange}:{symbol}"
    else:
        check_str = symbol

    tv_timeframe = timeframe.upper()
    ws = TradingViewWebSocket(check_str, tv_timeframe, candle_count)
    ws.connect()
    session = ws.generate_session()
    chart_session = ws.generate_chart_session()
    symbol_string = "={\"symbol\":\"" + ws.symbol + "\",\"adjustment\":\"splits\"}"

    ws.send_message("set_auth_token", ["unauthorized_user_token"])
    ws.send_message("chart_create_session", [chart_session, ""])
    ws.send_message("resolve_symbol", [chart_session, "symbol_" + ws.timeframe, symbol_string])
    ws.send_message("create_series", [chart_session, "s" + ws.timeframe, "s" + ws.timeframe, "symbol_" + ws.timeframe, ws.timeframe, ws.candles])

    ws.ws.settimeout(3.0)

    ohlc_data = []
    start_time = time.time()
    while time.time() - start_time < 3:
        try:
            result = ws.ws.recv()
            data = re.split(r'~m~\d+~m~', result)
            for i in data:
                if i.strip():
                    parsed_data = json.loads(i)
                    if parsed_data.get('m') == 'timescale_update':
                        try:
                            s_data = parsed_data['p'][1][f's{ws.timeframe}']['s']
                            for node in s_data:
                                ohlc_data.append([
                                    node['v'][0], # timestamp
                                    node['v'][1], # open
                                    node['v'][2], # high
                                    node['v'][3], # low
                                    node['v'][4], # close
                                    node['v'][5] if len(node['v']) > 5 else 0 # volume
                                ])
                        except KeyError:
                            pass
                        break
            if ohlc_data:
                break
        except Exception:
            pass

    if ohlc_data:
        df = pd.DataFrame(ohlc_data, columns=["timestamp", "Open", "High", "Low", "Close", "Volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df.set_index("timestamp", inplace=True)

        is_economics = (df["Open"] == df["Close"]).all() and (df["High"] == df["Low"]).all()

        # Tính toán các chỉ báo theo timeframe và danh sách ID được chọn từ URL
        addplot_list = []
        conn = get_db_connection()
        cursor = conn.cursor()
        if indicators_param is not None:
            if selected_indicator_ids:
                placeholders = ', '.join('?' for _ in selected_indicator_ids)
                cursor.execute(
                    f"SELECT * FROM indicators WHERE is_active = 1 AND LOWER(timeframe) = LOWER(?) AND id IN ({placeholders}) ORDER BY created_at DESC",
                    (timeframe, *selected_indicator_ids)
                )
            else:
                active_inds = []
                cursor.fetchall()
        else:
            cursor.execute('SELECT * FROM indicators WHERE is_active = 1 AND LOWER(timeframe) = LOWER(?) ORDER BY created_at DESC', (timeframe,))
        if indicators_param is not None and selected_indicator_ids:
            active_inds = [dict(row) for row in cursor.fetchall()]
        elif indicators_param is None:
            active_inds = [dict(row) for row in cursor.fetchall()]
        else:
            active_inds = []
        conn.close()

        for ind in active_inds:
            p = ind["period"]
            if len(df) >= p:
                if ind["type"] == "ema":
                    series = df["Close"].ewm(span=p, adjust=False).mean()
                else:
                    series = df["Close"].rolling(window=p).mean()

                if not series.isna().all():
                    addplot_list.append(mpf.make_addplot(series, color=ind["color"], width=1.5))

        plot_kwargs = {
            "type": "line" if is_economics else "candle",
            "style": style,
            "figsize": (12, 6),
            "title": f"{check_str} - {timeframe.upper()} ({len(df)} Candles)",
            "returnfig": True,
            "tight_layout": False,
            "warn_too_much_data": len(df) + 1,
        }
        if addplot_list:
            plot_kwargs["addplot"] = addplot_list

        fig, axlist = mpf.plot(df, **plot_kwargs)

        ax_price = axlist[0]
        positions, labels = _compute_custom_ticks(df, timeframe)
        if positions is not None and len(positions) > 0:
            ax_price.set_xticks(positions)
            ax_price.set_xticklabels(labels, rotation=0, ha="center", fontsize=9)

        ax_price.tick_params(axis="x", length=0, labelsize=9)
        ax_price.tick_params(axis="y", length=0, labelsize=9)
        fig.subplots_adjust(left=0.06, right=0.98, top=0.90, bottom=0.10, hspace=0.0)
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#18181b')
        ax.set_facecolor('#18181b')
        ax.text(0.5, 0.5, 'No Data Available', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, color='#ef4444', fontsize=14)
        for spine in ax.spines.values():
            spine.set_color('#555555')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor='#18181b', edgecolor='none', transparent=False)
    buf.seek(0)
    plt.close(fig)

    return StreamingResponse(buf, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    # Chạy server ở chế độ reload (dùng cho dev)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
