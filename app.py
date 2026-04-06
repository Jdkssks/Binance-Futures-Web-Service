from flask import Flask, request, jsonify, render_template
import requests
import pandas as pd
import pandas_ta as ta

app = Flask(__name__)

def get_signal(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=100"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        "timestamp","open","high","low","close","volume",
        "close_time","quote_asset_volume","trades",
        "taker_buy_base","taker_buy_quote","ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    # 技術指標
    rsi = ta.rsi(df["close"], length=14).iloc[-1]
    macd = ta.macd(df["close"]).iloc[-1].tolist()
    ema20 = ta.ema(df["close"], length=20).iloc[-1]
    ema50 = ta.ema(df["close"], length=50).iloc[-1]
    atr = ta.atr(df["high"].astype(float), df["low"].astype(float), df["close"], length=14).iloc[-1]

    # 簡單判斷
    signal = "看漲" if ema20 > ema50 and rsi < 70 else "看跌" if ema20 < ema50 and rsi > 30 else "中性"

    return {
        "RSI": round(rsi, 2),
        "MACD": [round(x, 2) for x in macd],
        "EMA20": round(ema20, 2),
        "EMA50": round(ema50, 2),
        "Volume": round(df["volume"].iloc[-1], 2),
        "ATR": round(atr, 2),
        "Signal": signal
    }

@app.route("/")
def index():
    # 抓取所有 Binance Futures 標的
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    data = requests.get(url).json()
    symbols = [s["symbol"] for s in data["symbols"]]
    return render_template("index.html", symbols=symbols)

@app.route("/signal")
def signal():
    symbol = request.args.get("symbol", "BTCUSDT")
    return jsonify(get_signal(symbol))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
