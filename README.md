# Inkself — AI Writing Assistant

A personal AI writing assistant that learns your writing style and improves from your corrections.

## Project Structure

```
inkself/
├── app.py               # Flask backend
├── requirements.txt     # Python dependencies
├── Procfile             # For Railway/Render deployment
├── .env.example         # Environment variable template
├── .gitignore
└── templates/
    └── index.html       # Frontend
```

---

## Deploy to Railway (Recommended — Free tier available)

Railway is the easiest option. Takes about 5 minutes.

### Step 1 — Push to GitHub

```bash
cd inkself
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/inkself.git
git push -u origin main
```

### Step 2 — Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select your `inkself` repo
4. Railway will auto-detect Python and deploy it

### Step 3 — Add your API key

1. In Railway, click your project → **Variables** tab
2. Add: `ANTHROPIC_API_KEY` = your key from [console.anthropic.com](https://console.anthropic.com)
3. Railway will redeploy automatically

### Step 4 — Get your URL

Click **Settings → Domains → Generate Domain**. Your app is live at `https://inkself-xxx.up.railway.app`

---

## Deploy to Render (Also free)

1. Go to [render.com](https://render.com) and sign up
2. Click **New → Web Service → Connect a repository**
3. Select your repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Add environment variable: `ANTHROPIC_API_KEY`
6. Click **Create Web Service**

---

## Run Locally

```bash
# Clone and enter directory
cd inkself

# Create virtual environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run
python app.py
```

Visit `http://localhost:5000`

---

## Getting Your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Click **API Keys → Create Key**
4. Copy it — you'll only see it once

---

## How It Works

- **Backend (Python/Flask):** Handles all AI generation requests. Your API key lives only on the server — never exposed to the browser.
- **Frontend (HTML/JS):** Your writing samples and corrections are stored in the browser's localStorage on your device.
- **Streaming:** Text streams back word-by-word so you see it appear in real time.
- **Learning:** Every correction you save gets sent with future generation requests, so the AI improves over time.
