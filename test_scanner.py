"""
test_scanner.py — run this BEFORE setting up the database.
Tests Binance data fetch + all 19 indicators + signal detection.
Usage:
  python test_scanner.py          # BTC 1h
  python test_scanner.py ETH 4h
  python test_scanner.py SOL 1d
"""
import sys
from scanner.fetch_data import fetch_ohlcv
from scanner.indicators import calculate_indicators
from scanner.signal_detector import detect_signals, compute_composite_score, build_summary

SYMBOL    = sys.argv[1].upper() if len(sys.argv) > 1 else "BTC"
TIMEFRAME = sys.argv[2]         if len(sys.argv) > 2 else "1h"

print(f"\n{'='*52}")
print(f"  {SYMBOL} [{TIMEFRAME}] — Signal Scanner Test")
print(f"{'='*52}")

print("\n📡 Fetching candles from Binance...")
df = fetch_ohlcv(SYMBOL, interval=TIMEFRAME, limit=210)
if df is None:
    print("❌ Failed — check internet connection."); sys.exit(1)
print(f"   ✅ {len(df)} candles | Close: ${df['close'].iloc[-1]:,.4f}")

print("\n📊 Calculating 19 indicators...")
ind = calculate_indicators(df)
if ind is None:
    print("❌ Calculation failed."); sys.exit(1)

groups = {
    "Trend":      [("MACD Line",ind.get("macd_line")),("MACD Signal",ind.get("macd_signal")),
                   ("EMA20",ind.get("ema20")),("EMA50",ind.get("ema50")),
                   ("EMA200",ind.get("ema200")),("ADX",ind.get("adx"))],
    "Momentum":   [("RSI",ind.get("rsi")),("Stoch %K",ind.get("stoch_k")),
                   ("Stoch %D",ind.get("stoch_d")),("CCI",ind.get("cci"))],
    "Volume":     [("Volume Ratio",ind.get("volume_ratio")),("OBV",ind.get("obv")),
                   ("VWAP",ind.get("vwap"))],
    "Volatility": [("BB Upper",ind.get("bb_upper")),("BB Lower",ind.get("bb_lower")),
                   ("BB %B",ind.get("bb_pct")),("BB Squeeze",ind.get("bb_squeeze")),
                   ("ATR",ind.get("atr")),("Stop Distance",ind.get("stop_distance"))],
    "Levels":     [("Pivot",ind.get("pivot")),("R1",ind.get("r1")),("S1",ind.get("s1")),
                   ("Fib 38.2%",ind.get("fib_382")),("Fib 61.8%",ind.get("fib_618"))],
}
for group, items in groups.items():
    print(f"\n  {group}")
    for label, val in items:
        if val is None: display = "N/A"
        elif isinstance(val, bool): display = "YES 🔔" if val else "No"
        elif isinstance(val, float) and val > 1000: display = f"${val:,.2f}"
        else: display = f"{val:.4f}" if isinstance(val, float) else str(val)
        print(f"    {label:<20} {display}")

print(f"\n⚡ Detecting signals...")
signals = detect_signals(SYMBOL, TIMEFRAME, ind)
if not signals:
    print("   No signals right now.")
else:
    score   = compute_composite_score(signals)
    summary = build_summary(signals, score, ind)
    icons   = {"bullish":"🟢","bearish":"🔴","neutral":"🟡"}
    for s in signals:
        print(f"   {icons.get(s['direction'],'⚪')}  {s['signal_type']:<35} ({s['direction']})")
    print(f"\n   Score   : {score}")
    print(f"   Bias    : {summary['overall'].upper()}")
    print(f"   Stop    : {summary.get('stop_distance') or 'N/A'}")
    label = "🔥🔥 VERY STRONG" if score>=10 else "🔥 STRONG — alert fires" if score>=7 \
            else "⚠️  Moderate" if score>=4 else "📎 Weak"
    print(f"   Strength: {label}")
print(f"\n{'='*52}\n")
