import pandas as pd
import mplfinance as mpf
import io

df = pd.DataFrame({
    'Open': [1, 2],
    'High': [3, 4],
    'Low': [0.5, 1],
    'Close': [2, 1],
    'Volume': [100, 200]
}, index=pd.to_datetime(['2023-01-01', '2023-01-02']))

COLOR_BULL = "#10b981"
COLOR_BEAR = "#ffffff"

_STYLE = mpf.make_mpf_style(
    marketcolors=mpf.make_marketcolors(
        up=COLOR_BULL, down=COLOR_BEAR,
        edge="inherit", wick="inherit",
        volume="in",
    ),
    rc={"figure.facecolor": "#212121"}
)

fig, _ = mpf.plot(df, type="candle", style=_STYLE, returnfig=True)
fig.savefig('test_mpf.png')
print("Done")
