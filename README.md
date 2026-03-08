# 🎯 HuntAI — Local AI Lead Generation & Outreach Agent

```
  ██╗  ██╗██╗   ██╗███╗   ██╗████████╗ █████╗ ██╗
  ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔══██╗██║
  ███████║██║   ██║██╔██╗ ██║   ██║   ███████║██║
  ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══██║██║
  ██║  ██║╚██████╔╝██║ ╚████║   ██║   ██║  ██║██║
  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝

  [ LOCAL AI LEAD GENERATION & OUTREACH AGENT ]
  v1.0.0 | Powered by Ollama + glm4:9b
```

**HuntAI** is a fully local, privacy-first AI lead generation and outreach automation tool. It runs entirely on your machine — no cloud AI fees, no data sent to third parties. Powered by [Ollama](https://ollama.ai) and open-source LLMs.

> ⚠️ **For legitimate business use only.** HuntAI is designed for ethical, permission-compliant outreach to businesses that match your service offering. Always comply with CAN-SPAM, GDPR, and your local regulations.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Local AI** | Uses Ollama with `glm4:9b` — runs 100% on your hardware |
| 🎯 **Lead Scraping** | Apify-powered scraping from Google Maps, directories & more |
| 📧 **Email Automation** | AI-personalized outreach with SMTP sending |
| 📊 **Web Dashboard** | Real-time dashboard at `localhost:3000` |
| 🔔 **Notifications** | Email updates when outreach is sent |
| 🔄 **Follow-ups** | AI-generated smart follow-up sequences |
| 💾 **Local Storage** | SQLite — everything stays on your machine |
| ⚡ **Background Worker** | 24/7 campaign automation |

---

## 🖥️ CLI Preview

```
  ╔══════════════════════════════════════════════════╗
  ║           MAIN MENU — SELECT OPTION              ║
  ╠══════════════════════════════════════════════════╣
  ║  [01] Start HuntAI          Launch automated lead generation
  ║  [02] Setup / Onboarding    Configure your profile & targets
  ║  [03] Configure Email       SMTP & outreach settings
  ║  [04] Lead Scraping Settings Define scraping parameters
  ║  [05] Launch Dashboard      Open web dashboard (localhost:3000)
  ║  [06] View History          Browse past campaigns & leads
  ║  [07] System Status         Check AI, Ollama & scraper status
  ║  [EX] Exit                  Quit HuntAI
  ╚══════════════════════════════════════════════════╝
```

---

## 📋 Requirements

- **Python** 3.8+
- **Ollama** (with `glm4:9b` model pulled)
- **Apify API Key** (free tier available at [apify.com](https://apify.com))
- **Email App Password** (Gmail, Outlook, etc.)
- Linux, macOS, or **Termux on Android**

---

## 🚀 Installation

### Step 1: Install Ollama

**Linux / macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Termux (Android):**
```bash
pkg install ollama
```

### Step 2: Start Ollama & Pull Model

```bash
# Start Ollama server
ollama serve

# In a new terminal, pull the model
ollama pull glm4:9b
```

> **Note:** `glm4:9b` requires ~6GB disk space. For lower-spec devices, try `qwen2:1.5b` or `phi3:mini`.

### Step 3: Clone & Install HuntAI

```bash
git clone https://github.com/itskousik08/huntai
cd huntai
bash install.sh
```

### Step 4: Launch

```bash
python huntai.py
```

On first launch, the **Onboarding Wizard** will guide you through setup.

---

## ⚙️ Onboarding Setup

When you first run HuntAI, you'll be asked:

```
  Your Name:
  Company Name:
  Company Website (https://...):
  What service does your company provide:
  Target customer type (B2B/B2C/Both):
  Target industry (e.g. SaaS, Retail):
  Target country/location:
  Ideal client size (startup/small/enterprise/any):
  Your outreach email address:
  Email App Password (hidden):
  Notification email (where HuntAI sends updates):
  Apify API Key:
```

All data is stored locally at `~/.huntai/config.json` with sensitive fields base64-encoded.

---

## 📧 Email Setup (Gmail)

1. Enable **2-Factor Authentication** on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Generate an App Password for "Mail"
4. Use this password in HuntAI (not your regular Gmail password)

**SMTP Settings (auto-configured for Gmail):**
```
Host: smtp.gmail.com
Port: 587
Security: STARTTLS
```

For other providers:
| Provider | SMTP Host | Port |
|---|---|---|
| Gmail | smtp.gmail.com | 587 |
| Outlook | smtp.office365.com | 587 |
| Yahoo | smtp.mail.yahoo.com | 587 |
| Zoho | smtp.zoho.com | 587 |

---

## 🔑 Apify Setup

1. Create a free account at [apify.com](https://apify.com)
2. Go to **Settings → Integrations** → copy your API token
3. Enter it during HuntAI onboarding or in `[04] Lead Scraping Settings`

**Free tier includes:** 5 actor compute units/month (enough for ~200-500 leads)

> **Tip:** Without an Apify key, HuntAI will use a mock scraper that generates demo data so you can still test the full pipeline.

---

## 📊 Dashboard

Launch the web dashboard:

```
[05] Launch Dashboard  →  http://localhost:3000
```

Features:
- **Real-time stats** — leads, emails sent, replies, campaign count
- **Live activity feed** via WebSocket
- **Campaign management** — start hunts, monitor progress
- **Lead database** — searchable, filterable table with lead scores
- **Email log** — full outreach history with reply tracking
- **CSV export** — download all leads with one click

---

## 🤖 AI Pipeline

Each lead goes through this AI pipeline:

```
Scraped Lead
     │
     ▼
┌─────────────┐
│  Qualify    │  → Score 1-10, check ICP match
│  (Ollama)   │
└─────────────┘
     │ score ≥ threshold?
     ▼
┌─────────────┐
│  Generate   │  → Personalized subject + body
│  Email      │
└─────────────┘
     │
     ▼
┌─────────────┐
│  Send via   │  → SMTP + notify user
│  SMTP       │
└─────────────┘
     │ no reply after N days?
     ▼
┌─────────────┐
│  Follow-up  │  → Different angle, max 2x
│  (Ollama)   │
└─────────────┘
     │ reply arrives?
     ▼
┌─────────────┐
│  Classify   │  → interested/not_interested/etc.
│  Reply      │
└─────────────┘
```

---

## 🗂️ Project Structure

```
huntai/
├── huntai.py                  # Main entry point
├── install.sh                 # Installer
├── requirements.txt
├── README.md
│
├── cli/
│   └── interface.py           # Hacker-style terminal UI
│
├── config/
│   └── manager.py             # Local config (secure storage)
│
├── database/
│   └── db.py                  # SQLite layer
│
├── scraper/
│   └── scraper.py             # Apify lead scraping engine
│
├── ai_agent/
│   └── engine.py              # Ollama AI (qualify, email gen, classify)
│
├── email_engine/
│   └── sender.py              # SMTP sending + inbox monitoring
│
├── background_worker/
│   └── worker.py              # Campaign orchestration
│
└── dashboard/
    ├── api.py                 # FastAPI backend + WebSocket
    └── index.html             # Single-file dashboard UI
```

---

## 🔄 Example Workflow

```bash
# 1. Start HuntAI
python huntai.py

# 2. Complete onboarding [02]
#    → Enter your company info, target, email, API keys

# 3. Start a hunt [01]
#    → Campaign: "SaaS Founders India"
#    → Industry: SaaS
#    → Location: India
#    → Leads: 20

# 4. HuntAI background worker:
#    ① Scrapes 20+ SaaS companies from Google Maps / directories
#    ② AI qualifies each lead (scores 1-10)
#    ③ Sends personalized emails to leads scored ≥ threshold
#    ④ Notifies you at your notification email for each send
#    ⑤ Monitors inbox for replies
#    ⑥ Sends AI follow-ups after 3 days (no reply)

# 5. Open dashboard [05]
#    → http://localhost:3000
#    → Monitor real-time progress
```

---

## 📱 Termux (Android) Usage

```bash
# Install dependencies
pkg install python ollama

# Start Ollama in background
ollama serve &

# Pull model
ollama pull glm4:9b

# Clone & install
git clone https://github.com/itskousik08/huntai
cd huntai
bash install.sh

# Run
python huntai.py
```

---

## ⚙️ Configuration Reference

Config stored at `~/.huntai/config.json`:

| Key | Description |
|---|---|
| `user_name` | Your name |
| `company_name` | Your company |
| `service_description` | What you offer |
| `target_industry` | e.g. "SaaS", "E-commerce" |
| `target_location` | e.g. "USA", "India" |
| `ideal_client_size` | startup / small / enterprise / any |
| `email_address` | Outreach email |
| `email_password` | App password (encoded) |
| `notification_email` | Where HuntAI notifies you |
| `apify_api_key` | Apify token (encoded) |
| `smtp_host` | Default: smtp.gmail.com |
| `smtp_port` | Default: 587 |
| `daily_email_limit` | Max emails/day (default: 50) |
| `email_delay_seconds` | Delay between emails (default: 30) |
| `min_lead_score` | Min score to contact (default: 6) |

---

## 🛡️ Privacy & Ethics

- **100% local** — your leads, emails, and config never leave your machine
- **Ollama only** — no OpenAI, Anthropic, or other cloud AI
- **You control the data** — SQLite file at `~/.huntai/huntai.db`
- **Designed for legitimate B2B outreach** — respect unsubscribes and opt-outs
- **Comply with** CAN-SPAM (USA), CASL (Canada), GDPR (EU)

---

## 🐛 Troubleshooting

**Ollama not responding:**
```bash
ollama serve    # Start the server
ollama list     # Check available models
```

**Model not found:**
```bash
ollama pull glm4:9b
# Or lighter alternative:
ollama pull phi3:mini
```

**SMTP authentication failed:**
- Use an **App Password**, not your regular password
- For Gmail: enable 2FA first, then generate App Password

**Dashboard not loading:**
```bash
pip install uvicorn fastapi
python -m uvicorn dashboard.api:app --host 0.0.0.0 --port 3000
```

---

## 🤝 Contributing

PRs welcome! Areas to improve:
- Additional Apify scraper sources
- Better email warmup logic
- Campaign A/B testing
- Webhook support for reply notifications
- More LLM model support

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## ⚠️ Disclaimer

HuntAI is a tool for **legitimate business outreach only**. The developers are not responsible for misuse. Always obtain proper consent where required and comply with all applicable laws regarding commercial electronic messages.

---

*Built with ❤️ for the indie hacker community.*
