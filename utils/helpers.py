def score_label(score):
    if score >= 6: return "Very Strong"
    if score >= 4: return "Strong"
    if score >= 2: return "Moderate"
    return "Weak"

def fmt_price(p):
    if p >= 1000: return f"${p:,.2f}"
    if p >= 1:    return f"${p:.4f}"
    return f"${p:.8f}"
