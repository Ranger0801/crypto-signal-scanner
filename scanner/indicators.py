"""
indicators.py — Phase 1 + Phase 2 combined
19 indicators across 5 categories.
Compatible with pandas-ta 0.4.x column naming.
"""
import logging, numpy as np
import pandas as pd
import pandas_ta as ta

log = logging.getLogger(__name__)

def calculate_indicators(df: pd.DataFrame) -> dict | None:
    if df is None or len(df) < 60:
        log.warning("Need >=60 candles")
        return None
    try:
        c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
        r = {}

        # ── TREND ──────────────────────────────────────────
        macd = ta.macd(c, fast=12, slow=26, signal=9)
        mc = macd.columns.tolist()
        # mc[0]=MACD, mc[1]=MACDh, mc[2]=MACDs  (order may vary by version)
        macd_col   = [x for x in mc if str(x).startswith("MACD_")  or x == mc[0]][0]
        macds_col  = [x for x in mc if str(x).startswith("MACDs_") or x == mc[2]][0]
        macdh_col  = [x for x in mc if str(x).startswith("MACDh_") or x == mc[1]][0]
        r["macd_line"]     = _f(macd.iloc[-1][macd_col])
        r["macd_signal"]   = _f(macd.iloc[-1][macds_col])
        r["macd_hist"]     = _f(macd.iloc[-1][macdh_col])
        r["macd_prev"]     = _f(macd.iloc[-2][macd_col])
        r["macd_sig_prev"] = _f(macd.iloc[-2][macds_col])
        r["macd_hist_prev"]= _f(macd.iloc[-2][macdh_col])

        ema20 = ta.ema(c, length=20)
        ema50 = ta.ema(c, length=50)
        r["ema20"]      = _f(ema20.iloc[-1])
        r["ema50"]      = _f(ema50.iloc[-1])
        r["ema20_prev"] = _f(ema20.iloc[-2])
        r["ema50_prev"] = _f(ema50.iloc[-2])
        r["ema200"]     = _f(ta.ema(c, length=200).iloc[-1]) if len(df) >= 200 else None

        adx_df = ta.adx(h, l, c, length=14)
        ac = adx_df.columns.tolist()
        adx_col = [x for x in ac if str(x).startswith("ADX")][0]
        dmp_col = [x for x in ac if str(x).startswith("DMP")][0]
        dmn_col = [x for x in ac if str(x).startswith("DMN")][0]
        r["adx"]     = _f(adx_df.iloc[-1][adx_col])
        r["adx_dmp"] = _f(adx_df.iloc[-1][dmp_col])
        r["adx_dmn"] = _f(adx_df.iloc[-1][dmn_col])

        # ── MOMENTUM ───────────────────────────────────────
        rsi = ta.rsi(c, length=14)
        r["rsi"]      = _f(rsi.iloc[-1])
        r["rsi_prev"] = _f(rsi.iloc[-2])

        stoch = ta.stoch(h, l, c, k=14, d=3, smooth_k=3)
        sc = stoch.columns.tolist()
        stk_col = [x for x in sc if str(x).startswith("STOCHk")][0]
        std_col = [x for x in sc if str(x).startswith("STOCHd")][0]
        r["stoch_k"]      = _f(stoch.iloc[-1][stk_col])
        r["stoch_d"]      = _f(stoch.iloc[-1][std_col])
        r["stoch_k_prev"] = _f(stoch.iloc[-2][stk_col])
        r["stoch_d_prev"] = _f(stoch.iloc[-2][std_col])

        r["cci"] = _f(ta.cci(h, l, c, length=20).iloc[-1])

        # ── VOLUME ─────────────────────────────────────────
        avg_v = v.rolling(20).mean().iloc[-1]
        r["volume"]       = _f(v.iloc[-1])
        r["avg_volume"]   = _f(avg_v)
        r["volume_ratio"] = _f(v.iloc[-1] / avg_v if avg_v > 0 else 0)

        obv = ta.obv(c, v)
        r["obv"]      = _f(obv.iloc[-1])
        r["obv_prev"] = _f(obv.iloc[-5])

        hlc3 = (h + l + c) / 3
        r["vwap"] = _f((hlc3 * v).cumsum().iloc[-1] / v.cumsum().iloc[-1])

        # ── VOLATILITY ─────────────────────────────────────
        bb = ta.bbands(c, length=20, std=2)
        bbc = bb.columns.tolist()
        bbu_col = [x for x in bbc if str(x).startswith("BBU")][0]
        bbm_col = [x for x in bbc if str(x).startswith("BBM")][0]
        bbl_col = [x for x in bbc if str(x).startswith("BBL")][0]
        bbb_col = [x for x in bbc if str(x).startswith("BBB")][0]
        bbp_col = [x for x in bbc if str(x).startswith("BBP")][0]
        r["bb_upper"]  = _f(bb.iloc[-1][bbu_col])
        r["bb_mid"]    = _f(bb.iloc[-1][bbm_col])
        r["bb_lower"]  = _f(bb.iloc[-1][bbl_col])
        r["bb_width"]  = _f(bb.iloc[-1][bbb_col])
        r["bb_pct"]    = _f(bb.iloc[-1][bbp_col])
        bb_avg         = bb[bbb_col].rolling(20).mean().iloc[-1]
        r["bb_squeeze"]= bool(r["bb_width"] is not None and
                              bb_avg is not None and
                              r["bb_width"] < float(bb_avg) * 0.85)

        r["atr"]           = _f(ta.atr(h, l, c, length=14).iloc[-1])
        r["stop_distance"] = _f(r["atr"] * 1.5) if r["atr"] else None

        # ── LEVELS ─────────────────────────────────────────
        ph, pl, pc = float(h.iloc[-2]), float(l.iloc[-2]), float(c.iloc[-2])
        pivot = (ph + pl + pc) / 3
        r["pivot"] = _f(pivot)
        r["r1"]    = _f(2*pivot - pl)
        r["r2"]    = _f(pivot + (ph - pl))
        r["s1"]    = _f(2*pivot - ph)
        r["s2"]    = _f(pivot - (ph - pl))

        sh = float(h.iloc[-50:].max())
        sl = float(l.iloc[-50:].min())
        d  = sh - sl
        r["fib_236"] = _f(sh - 0.236*d)
        r["fib_382"] = _f(sh - 0.382*d)
        r["fib_500"] = _f(sh - 0.500*d)
        r["fib_618"] = _f(sh - 0.618*d)

        r["close"] = _f(c.iloc[-1])
        return r

    except Exception as e:
        log.error(f"Indicator error: {e}", exc_info=True)
        return None

def _f(val, decimals=6):
    try:
        v = float(val)
        return None if (np.isnan(v) or np.isinf(v)) else round(v, decimals)
    except:
        return None
