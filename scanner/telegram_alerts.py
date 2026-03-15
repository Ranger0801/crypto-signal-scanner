"""
telegram_alerts.py — Phase 3
Sends formatted signal alerts to Telegram.

Setup:
  1. Message @BotFather on Telegram -> /newbot -> copy token
  2. Add bot to your channel or group
  3. Get chat ID: https://api.telegram.org/bot<TOKEN>/getUpdates
  4. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
"""
import logging, requests
from config import Config

log = logging.getLogger(__name__)


def send_signal_alert(symbol, timeframe, signals, score, ind,
                      ai_explanation=None, confidence=None):
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        log.debug("Telegram not configured — skipping.")
        return

    msg = _build_message(symbol, timeframe, signals, score, ind, ai_explanation, confidence)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": Config.TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10)
        r.raise_for_status()
        log.info(f"[Telegram] Alert sent — {symbol} {timeframe} score={score}")
    except Exception as e:
        log.error(f"[Telegram] Failed: {e}")


def _build_message(symbol, timeframe, signals, score, ind,
                   ai_explanation, confidence):
    strength = "🔥🔥 VERY STRONG" if score >= 10 else "🔥 STRONG"
    bullish  = [s for s in signals if s["direction"] == "bullish"]
    bearish  = [s for s in signals if s["direction"] == "bearish"]
    bias     = "📈 BULLISH" if len(bullish) > len(bearish) else \
               "📉 BEARISH" if len(bearish) > len(bullish) else "➡️ NEUTRAL"
    icons    = {"bullish":"🟢","bearish":"🔴","neutral":"🟡"}
    sig_lines = "\n".join(f"  {icons.get(s['direction'],'⚪')} {s['signal_type']}" for s in signals)

    close = ind.get("close", 0)
    price = f"${close:,.2f}" if close >= 1 else f"${close:.6f}"

    msg = f"""<b>⚡ Signal Alert — {symbol}</b>
<b>Timeframe:</b> {timeframe} | <b>Price:</b> {price}
<b>Bias:</b> {bias} | <b>Score:</b> {score} — {strength}"""

    if confidence:
        msg += f"\n<b>ML Confidence:</b> {confidence}% win probability"

    msg += f"\n\n<b>Signals:</b>\n{sig_lines}"
    msg += f"\n\n<b>RSI:</b> {ind.get('rsi','N/A')} | <b>ADX:</b> {ind.get('adx','N/A')}"
    msg += f"\n<b>Stop Distance:</b> ${ind.get('stop_distance',0):,.2f}" if ind.get('stop_distance') else ""

    if ai_explanation:
        msg += f"\n\n<b>🤖 AI Analysis:</b>\n<i>{ai_explanation}</i>"

    msg += "\n\n<i>⚡ CryptoSignal Scanner</i>"
    return msg
