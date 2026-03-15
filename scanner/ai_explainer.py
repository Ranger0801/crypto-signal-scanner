"""
ai_explainer.py — Phase 3
Uses Claude API to generate plain English signal explanations.
Fires when score >= 10 (very strong setups only, to keep costs low).

Setup:
  1. Go to console.anthropic.com -> API Keys -> Create Key
  2. Add ANTHROPIC_API_KEY to your .env file
"""
import os, logging, requests

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_API_URL    = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL      = "claude-haiku-4-5-20251001"


def explain_signal(symbol: str, timeframe: str,
                   signals: list, score: int, ind: dict) -> str | None:
    """
    Generate a 2-3 sentence plain English explanation of a signal.
    Returns None if API key not configured or request fails.
    """
    if not ANTHROPIC_API_KEY:
        log.debug("ANTHROPIC_API_KEY not set — skipping AI explanation.")
        return None

    try:
        resp = requests.post(
            CLAUDE_API_URL,
            headers={
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      CLAUDE_MODEL,
                "max_tokens": 220,
                "messages":   [{"role": "user", "content": _prompt(symbol, timeframe, signals, score, ind)}],
            },
            timeout=15,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        log.info(f"[Claude] Explanation generated for {symbol} {timeframe}")
        return text
    except Exception as e:
        log.error(f"[Claude] Failed: {e}")
        return None


def _prompt(symbol, timeframe, signals, score, ind) -> str:
    bullish = [s["signal_type"] for s in signals if s["direction"] == "bullish"]
    bearish = [s["signal_type"] for s in signals if s["direction"] == "bearish"]
    bias    = "bullish" if len(bullish) > len(bearish) else \
              "bearish" if len(bearish) > len(bullish) else "neutral"
    close   = ind.get("close", 0)

    return f"""You are a professional crypto trading analyst. Write exactly 2-3 sentences explaining why this signal fired based on the indicator data. Be specific. Do not give financial advice or say buy/sell.

Asset: {symbol} | Timeframe: {timeframe} | Price: ${close:,.4f}
Bias: {bias} | Score: {score}
Bullish signals: {", ".join(bullish) if bullish else "None"}
Bearish signals: {", ".join(bearish) if bearish else "None"}
RSI: {ind.get("rsi","N/A")} | ADX: {ind.get("adx","N/A")} | EMA20: {ind.get("ema20","N/A")} | EMA50: {ind.get("ema50","N/A")}
VWAP: {ind.get("vwap","N/A")} | BB%B: {ind.get("bb_pct","N/A")} | Volume ratio: {ind.get("volume_ratio","N/A")}x

2-3 sentence explanation:"""
