# Configuration Guide

## 🎯 Which .env File Should I Use?

The project has multiple `.env.example` files. Here's which one to use:

### For Running the Dashboard (Most Common)

**Use:** `sal_dashboard/.env.example`

```bash
# 1. Navigate to dashboard directory
cd sal_dashboard

# 2. Copy the example file
cp .env.example .env

# 3. Edit with your information
nano .env  # or use any text editor
```

This is the **main configuration file** for the interactive dashboard.

### For Backend Analysis Only

**Use:** `strategic_alpha/.env.example`

Only needed if you're running the backend analysis tools directly without the dashboard.

### Root .env.example

This is a legacy file - ignore it for now.

---

## 📝 Configuration Fields Explained

### FRED API Key (Optional)

**Purpose**: Fetches macroeconomic data (GDP, unemployment, interest rates, etc.)

**How to get it:**
1. Go to https://fred.stlouisfed.org/
2. Create a free account
3. Navigate to https://fred.stlouisfed.org/docs/api/api_key.html
4. Click "Request API Key"
5. Copy your key

**In .env file:**
```bash
FRED_API_KEY=your_actual_key_here
```

**What happens without it**: The app uses sample/cached macroeconomic data.

---

### SEC EDGAR Configuration (NO API KEY!)

**Important**: The SEC does **NOT** use API keys!

Instead, the SEC requires you to identify yourself with a User-Agent header containing your name and email. This is a requirement from the SEC to prevent abuse.

**Purpose**: Fetches 10-K filings to extract risk factors

**In .env file:**
```bash
SEC_USER_NAME=Your Name
SEC_USER_EMAIL=your.email@example.com
```

**Example:**
```bash
SEC_USER_NAME=John Doe
SEC_USER_EMAIL=john.doe@university.edu
```

**What happens without it**: The app uses a generic default ("Strategic Alpha Suite user@example.com") which works but you should provide your own per SEC guidelines.

**SEC Requirements:**
- Use your real name and valid email
- Format: "Name Email" (e.g., "John Doe john@example.com")
- Rate limit: 10 requests per second (automatically enforced)
- See: https://www.sec.gov/os/accessing-edgar-data

---

### Risk Analysis Parameters (Optional)

These have sensible defaults but you can customize:

```bash
# Shock percentage for stress testing (-10% means a 10% decline)
SHOCK_PCT=-0.10

# Peer companies for comparative analysis
RISK_PEER_TICKERS=AMD,AVGO,TSM,ASML,INTC

# Companies to stress test in supply chain analysis
SUPPLY_SHOCK_TICKERS=TSM,ASML
```

---

## 🚀 Quick Setup (Dashboard)

**Minimum config to run dashboard:**

```bash
# In sal_dashboard/.env
FRED_API_KEY=  # Leave empty - uses sample data
SEC_USER_NAME=Your Name  # Replace with your name
SEC_USER_EMAIL=your@email.com  # Replace with your email
SHOCK_PCT=-0.10
RISK_PEER_TICKERS=AMD,AVGO,TSM,ASML,INTC
SUPPLY_SHOCK_TICKERS=TSM,ASML
```

Then run:
```bash
cd sal_dashboard
streamlit run app/streamlit_app.py
```

---

## 🔒 Security Best Practices

### Local Development
- ✅ Copy `.env.example` to `.env`
- ✅ Never commit `.env` to git (it's in `.gitignore`)
- ✅ Use your real contact info for SEC requests
- ✅ Get your own FRED API key (free)

### Streamlit Cloud Deployment
- ✅ Use Streamlit's secrets management (not .env files)
- ✅ Add secrets in the app settings UI
- ✅ Format: same as `.streamlit/secrets.toml.example`

---

## 🐛 Troubleshooting

### "SEC API Error"
- ✅ Make sure you're providing valid User-Agent info
- ✅ Check you're not making more than 10 requests/second
- ✅ The app will fall back to sample data if SEC is unavailable

### "FRED API Error"
- ✅ Verify your API key is correct
- ✅ Check you haven't exceeded the daily limit (usually 1000 calls/day)
- ✅ The app will use sample data if FRED is unavailable

### "Config not found"
- ✅ Make sure you copied `.env.example` to `.env`
- ✅ Make sure you're in the right directory (`sal_dashboard/` for dashboard)
- ✅ Check file permissions

### "Port 8501 already in use"
```bash
# Kill existing Streamlit process
lsof -ti:8501 | xargs kill -9

# Or use a different port
streamlit run app/streamlit_app.py --server.port 8502
```

---

## 📂 File Locations Summary

```
Stock Finder/
│
├── sal_dashboard/
│   ├── .env.example          ← **USE THIS for dashboard**
│   ├── .env                  ← Copy from .env.example (gitignored)
│   └── .streamlit/
│       └── secrets.toml.example  ← For Streamlit Cloud
│
└── strategic_alpha/
    └── .env.example          ← Use only for backend-only work
```

---

## 💡 Pro Tips

1. **Start Simple**: Run without any API keys first to test the app with sample data
2. **Add FRED Next**: Get a free FRED API key for real macro data
3. **Configure SEC**: Add your name/email for real 10-K data
4. **Keep Defaults**: The risk parameters have good defaults for semiconductors

5. **For Resume/Portfolio**:
   - Deploy to Streamlit Cloud
   - Use Streamlit secrets management (cleaner than .env)
   - Keep your FRED API key secret!

---

## 🆘 Still Confused?

Common questions:

**Q: Do I need to pay for SEC access?**
A: No! SEC EDGAR is completely free. Just provide your contact info.

**Q: Which .env file is for Streamlit Cloud?**
A: None! Streamlit Cloud uses secrets management (see `.streamlit/secrets.toml.example`)

**Q: Can I run the app without any API keys?**
A: Yes! It will use sample data. You'll see warnings but it will work fine.

**Q: Why are there multiple .env.example files?**
A: Historical reasons. Use `sal_dashboard/.env.example` for the dashboard.

---

**Questions?** Check [DEPLOYMENT.md](sal_dashboard/DEPLOYMENT.md) for deployment-specific config.
