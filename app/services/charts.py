import io
import json
import re
import time
from typing import List

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from tradingview_websocket import TradingViewWebSocket

from app.db.indicators import get_indicator_by_id
from app.db.symbols import get_symbol_by_id
from app.services.settings import SettingsService


def compute_custom_ticks(df: pd.DataFrame, timeframe: str):
    tf = timeframe.lower()
    dates = df.index
    positions = []
    labels = []

    if len(dates) == 0:
        return positions, labels

    if tf in ['1', '3', '5']:
        last_hour = None
        for i, dt in enumerate(dates):
            if last_hour is None or dt.hour != last_hour:
                positions.append(i)
                labels.append(dt.strftime('%H:%M'))
                last_hour = dt.hour
    elif tf in ['15', '30', '45']:
        last_hour_group = None
        for i, dt in enumerate(dates):
            hour_group = (dt.date(), dt.hour // 4)
            if last_hour_group is None or hour_group != last_hour_group:
                positions.append(i)
                labels.append(dt.strftime('%d/%m %H:%M') if dt.hour == 0 else dt.strftime('%H:%M'))
                last_hour_group = hour_group
    elif tf in ['1h', '2h', '3h', '4h']:
        last_day = None
        for i, dt in enumerate(dates):
            if last_day is None or dt.date() != last_day:
                positions.append(i)
                labels.append(dt.strftime('%d/%m'))
                last_day = dt.date()
    elif tf == '1d':
        last_month = None
        for i, dt in enumerate(dates):
            ym = (dt.year, dt.month)
            if last_month is None or ym != last_month:
                positions.append(i)
                labels.append(dt.strftime('%m/%Y'))
                last_month = ym
    elif tf == '1w':
        last_quarter = None
        for i, dt in enumerate(dates):
            quarter = (dt.year, (dt.month - 1) // 3 + 1)
            if last_quarter is None or quarter != last_quarter:
                positions.append(i)
                labels.append(f"Q{quarter[1]}/{dt.year}")
                last_quarter = quarter
    elif tf in ['1m', '3m', '6m', '12m']:
        last_year = None
        for i, dt in enumerate(dates):
            if last_year is None or dt.year != last_year:
                positions.append(i)
                labels.append(dt.strftime('%Y'))
                last_year = dt.year
    else:
        return None, None

    if len(positions) > 10:
        step = max(1, len(positions) // 6)
        positions = positions[::step]
        labels = labels[::step]

    return positions, labels


class ChartService:
    @staticmethod
    def get_chart_data(symbol_id: int, timeframe: str = '1d') -> tuple:
        symbol_data = get_symbol_by_id(symbol_id)
        if not symbol_data:
            raise ValueError(f'Symbol with ID {symbol_id} not found')

        symbol = symbol_data['symbol']
        exchange = symbol_data['exchange']
        settings = SettingsService.get_chart_settings()
        candle_count = settings['candle_count']

        check_str = f'{exchange}:{symbol}' if exchange and exchange != 'ECONOMICS' else symbol
        ws = TradingViewWebSocket(check_str, timeframe.upper(), candle_count)
        ws.connect()
        session = ws.generate_session()
        chart_session = ws.generate_chart_session()
        symbol_string = '={"symbol":"' + ws.symbol + '","adjustment":"splits"}'

        ws.send_message('set_auth_token', ['unauthorized_user_token'])
        ws.send_message('chart_create_session', [chart_session, ''])
        ws.send_message('resolve_symbol', [chart_session, 'symbol_' + ws.timeframe, symbol_string])
        ws.send_message('create_series', [chart_session, 's' + ws.timeframe, 's' + ws.timeframe, 'symbol_' + ws.timeframe, ws.timeframe, ws.candles])
        ws.ws.settimeout(3.0)

        ohlc_data = []
        start_time = time.time()
        while time.time() - start_time < 3:
            try:
                result = ws.ws.recv()
                data = re.split(r'~m~\d+~m~', result)
                for item in data:
                    if item.strip():
                        parsed_data = json.loads(item)
                        if parsed_data.get('m') == 'timescale_update':
                            try:
                                s_data = parsed_data['p'][1][f's{ws.timeframe}']['s']
                                for node in s_data:
                                    ohlc_data.append([
                                        node['v'][0],
                                        node['v'][1],
                                        node['v'][2],
                                        node['v'][3],
                                        node['v'][4],
                                        node['v'][5] if len(node['v']) > 5 else 0,
                                    ])
                            except KeyError:
                                pass
                            break
                if ohlc_data:
                    break
            except Exception:
                pass

        return ohlc_data, check_str, symbol_data

    @staticmethod
    def render_chart(symbol_id: int, timeframe: str = '1d', indicator_ids: List[int] = None) -> bytes:
        ohlc_data, check_str, _ = ChartService.get_chart_data(symbol_id, timeframe)
        settings = SettingsService.get_chart_settings()

        if not ohlc_data:
            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor('#18181b')
            ax.set_facecolor('#18181b')
            ax.text(
                0.5, 0.5, 'No Data Available', horizontalalignment='center',
                verticalalignment='center', transform=ax.transAxes, color='#ef4444', fontsize=14
            )
            for spine in ax.spines.values():
                spine.set_color('#555555')
        else:
            df = pd.DataFrame(ohlc_data, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)

            is_economics = (df['Open'] == df['Close']).all() and (df['High'] == df['Low']).all()
            style = mpf.make_mpf_style(
                marketcolors=mpf.make_marketcolors(
                    up=settings['bull_color'],
                    down=settings['bear_color'],
                    edge='inherit',
                    wick='inherit',
                    volume='in',
                ),
                rc={
                    'axes.grid': True,
                    'axes.titlesize': 13,
                    'font.size': 11,
                    'axes.labelsize': 9,
                    'figure.facecolor': '#18181b',
                    'axes.facecolor': '#18181b',
                    'savefig.facecolor': '#18181b',
                    'axes.edgecolor': '#555555',
                    'axes.labelcolor': '#ffffff',
                    'xtick.color': '#ffffff',
                    'ytick.color': '#ffffff',
                    'text.color': '#ffffff',
                    'grid.color': '#3a3a3a',
                    'grid.linestyle': '--',
                    'grid.linewidth': 0.6,
                    'grid.alpha': 0.5,
                },
            )

            addplot_list = []
            if indicator_ids:
                for indicator_id in indicator_ids:
                    indicator = get_indicator_by_id(indicator_id)
                    if not indicator:
                        continue
                    p = indicator['period']
                    if len(df) >= p:
                        if indicator['type'] == 'ema':
                            series = df['Close'].ewm(span=p, adjust=False).mean()
                        else:
                            series = df['Close'].rolling(window=p).mean()
                        if not series.isna().all():
                            addplot_list.append(mpf.make_addplot(series, color=indicator['color'], width=1.5))

            plot_kwargs = {
                'type': 'line' if is_economics else 'candle',
                'style': style,
                'figsize': (12, 6),
                'title': f"{check_str} - {timeframe.upper()} ({len(df)} Candles)",
                'returnfig': True,
                'tight_layout': False,
                'warn_too_much_data': len(df) + 1,
            }
            if addplot_list:
                plot_kwargs['addplot'] = addplot_list

            fig, axlist = mpf.plot(df, **plot_kwargs)
            ax_price = axlist[0]
            positions, labels = compute_custom_ticks(df, timeframe)
            if positions is not None and len(positions) > 0:
                ax_price.set_xticks(positions)
                ax_price.set_xticklabels(labels, rotation=0, ha='center', fontsize=9)

            ax_price.tick_params(axis='x', length=0, labelsize=9)
            ax_price.tick_params(axis='y', length=0, labelsize=9)
            fig.subplots_adjust(left=0.06, right=0.98, top=0.90, bottom=0.10, hspace=0.0)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', facecolor='#18181b', edgecolor='none', transparent=False)
        buf.seek(0)
        plt.close(fig)
        return buf.getvalue()
