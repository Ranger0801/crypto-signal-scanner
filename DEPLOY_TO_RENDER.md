# 🚀 Deploy Crypto Signal Scanner to Render — Step-by-Step

## What You Need
- A free account at [render.com](https://render.com)
- A free account at [github.com](https://github.com)
- This project folder

---

## Step 1 — Push to GitHub

1. Go to github.com → click **New repository**
2. Name it `crypto-signal-scanner` → click **Create repository**
3. In your terminal, inside this project folder:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/crypto-signal-scanner.git
git push -u origin main
```

---

## Step 2 — Create a Web Service on Render

1. Go to [render.com](https://render.com) → **New +** → **Web Service**
2. Connect your GitHub account → select `crypto-signal-scanner`
3. Fill in the settings:

| Field | Value |
|-------|-------|
| **Name** | `crypto-signal-scanner` |
| **Region** | Closest to you |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn start:app --workers 2 --threads 2 --bind 0.0.0.0:$PORT --timeout 120` |

4. Click **Create Web Service**

---

## Step 3 — Set Environment Variables

In Render → your service → **Environment** tab, add:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Click "Generate" or type a random string |
| `DEBUG` | `false` |
| `DATABASE_URL` | `sqlite:///crypto_signals.db` |

---

## Step 4 — Deploy 🎉

Render will automatically build and deploy. Takes ~2 minutes.

Your live URL will be:
```
https://crypto-signal-scanner.onrender.com
```

---

## Step 5 — Verify It Works

1. Visit your URL — you should see the dark dashboard
2. Visit `https://your-app.onrender.com/health` → should return `{"status":"ok"}`
3. Visit `https://your-app.onrender.com/api/market-summary`

---

## Auto-Deploy on Push

Every time you `git push` to `main`, Render redeploys automatically. ✅

---

## Upgrading Database (Optional)

For production with persistent data, replace SQLite with a free PostgreSQL on Render:
1. Render → **New +** → **PostgreSQL** (free tier)
2. Copy the **Internal Database URL**
3. Set it as `DATABASE_URL` environment variable

---

## Free Tier Notes

- Free Render services **spin down after 15 min of inactivity** (cold start ~30s)
- Upgrade to Render Starter ($7/month) to keep it always-on
- SQLite data resets on redeploy — use PostgreSQL for persistence
