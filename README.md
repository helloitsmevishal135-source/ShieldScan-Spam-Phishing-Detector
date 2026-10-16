# ShieldScan

**Flask-based phishing & spam detection platform** with Gmail OAuth scanning, website URL analysis, and an admin dashboard.

---

## Project Description

ShieldScan is a full-stack security application that helps users detect phishing and spam threats. It combines a Flask web application with a machine learning detection pipeline to classify text messages and URLs, optionally sync and scan Gmail messages via Google OAuth, and crawl websites to analyze extracted links.

The system includes:

- **User authentication** and a personal security dashboard  
- **Gmail integration** (OAuth 2.0, readonly) with automatic and manual mailbox sync  
- **Website Link Analyzer** that crawls a page and scores discovered URLs  
- **ML detection** for spam (text) and phishing (URLs)  
- **Admin dashboard** for platform monitoring, domains, models, and logs  

---

## Live Demo

Try the deployed application:

**https://shieldscan-itck.onrender.com**

---

## Demo Notes

- The live application is publicly accessible for portfolio and demonstration use.
- Gmail integration uses Google OAuth in **Testing** mode.
- Only Google accounts added as **OAuth Test Users** in the Google Cloud Console can use **Connect Gmail**.
- This is a Google OAuth restriction, not an application bug.
- All other public features remain available for demo: account registration/login, manual text and URL analysis, website scanning, and general exploration of the dashboard.

---

## Features

- User registration, login, and session-based authentication  
- Quick scan for pasted text or URLs  
- Threat level display (safe / suspicious / dangerous) with scan history and stats charts  
- Gmail OAuth connect / disconnect *(live demo: limited to authorized Google OAuth test users)*  
- Automatic background Gmail sync (configurable interval)  
- Manual **Refresh Gmail** to scan only new, unscanned messages  
- Duplicate prevention via Gmail message IDs  
- Website crawler with phishing model analysis of page links  
- Trusted / blocked domain awareness  
- Admin panel (login, dashboard stats, domain lists, model info, activity logs)  
- Encrypted storage of Gmail OAuth tokens at rest  
- SQLite by default; `DATABASE_URL` ready for production databases  

---

## Technology Stack

| Layer | Technologies |
|--------|----------------|
| **Frontend** | HTML5, Jinja2 templates, Bootstrap 5, Chart.js, vanilla JavaScript |
| **Backend** | Python 3, Flask, Flask-Login, Flask-SQLAlchemy, APScheduler |
| **Database** | SQLite (default), SQLAlchemy ORM (`DATABASE_URL` for PostgreSQL/MySQL-compatible URIs) |
| **Machine Learning** | scikit-learn, joblib, NumPy, pandas, NLTK; Naive Bayes (spam), Random Forest (phishing) |
| **Authentication** | Flask-Login (app users); Google OAuth 2.0 (Gmail) |
| **APIs** | Gmail API (`gmail.readonly`), Google Auth libraries |
| **Deployment-ready** | `requirements.txt`, `Procfile` (Gunicorn), `runtime.txt`, `.env.example` |

---

## Project Architecture

```
User
  ↓
Flask Application (run.py → create_app)
  ↓
Authentication / Gmail OAuth / Website Scanner / Admin
  ↓
ML Detection Pipeline (app/ml + models/)
  ↓
Database (SQLite / configured DATABASE_URL)
```

**Typical Gmail flow**

```
OAuth (Gmail) → gmail_service → email_scan_service → ML pipeline → Database
```

---

## Folder Structure

```
full-app/
├── app/                          # Flask application package
│   ├── admin/                    # Admin blueprint (auth, dashboard, domains, models, logs)
│   │   └── services/
│   ├── auth/                     # User register / login / logout
│   ├── ml/                       # Inference, crawler, features, spam/phishing pipelines
│   │   ├── crawler/
│   │   ├── html_features/
│   │   ├── phishing/
│   │   ├── risk_engine/
│   │   ├── spam/
│   │   ├── url_features/
│   │   └── utils/
│   ├── models/                   # SQLAlchemy models (User, Scan, EmailScan, platform)
│   ├── routes/                   # Dashboard, Gmail, crawler, profile
│   ├── services/                 # Business services (scan, Gmail, ML, crawler, crypto)
│   ├── tasks/                    # Background Gmail sync scheduler
│   ├── config.py
│   ├── db_migrate.py
│   ├── env_bootstrap.py
│   ├── extensions.py
│   └── __init__.py               # Application factory
├── custom_models/                # Legacy / custom model helpers
├── models/                       # Trained model artifacts
│   └── sklearn/                  # Preferred scikit-learn joblib pipelines
├── static/                       # CSS & JavaScript
│   ├── css/
│   └── js/
├── templates/                    # Jinja2 templates (dashboard, auth, admin)
├── training/                     # Model training scripts & metrics helpers
├── instance/                     # Local SQLite DB (not committed)
├── run.py                        # Web app entry point
├── main.py                       # ML inference facade
├── requirements.txt
├── Procfile                      # Process definition for PaaS (e.g. Heroku/Railway)
├── runtime.txt                   # Python version hint for Heroku-style hosts
├── .env.example                  # Environment variable template (no secrets)
├── .gitignore
└── README.md
```

Additional root-level scripts and CSVs may exist for training, legacy CLI use, or datasets (`*.csv`, `train_*.py`, etc.).

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 2. Create a virtual environment

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at least `SECRET_KEY`, and (for Gmail) Google OAuth values. See [Environment Variables](#environment-variables).

### 5. Run Flask

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Environment Variables

Copy `.env.example` to `.env`. **Never commit `.env` or real secrets.**

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask session signing key. Use a long random string in production. |
| `FLASK_ENV` | No | `development` or `production` |
| `FLASK_DEBUG` | No | Enable debug-related behavior when truthy |
| `PRODUCTION` | No | If truthy, treats environment as production (stricter OAuth transport) |
| `ENV` | No | Alternate env name; `production` enforces HTTPS OAuth rules |
| `DATABASE_URL` | No | SQLAlchemy DB URI. Defaults to SQLite under `instance/shield.db` |
| `TOKEN_ENCRYPTION_KEY` | No | Key material for encrypting Gmail tokens. Falls back to `SECRET_KEY` if empty |
| `GOOGLE_CLIENT_ID` | For Gmail | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | For Gmail | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | For Gmail | Must match Google Cloud console (e.g. `http://127.0.0.1:5000/gmail/callback`) |
| `OAUTHLIB_INSECURE_TRANSPORT` | Local only | Set `1` for HTTP OAuth on localhost. **Do not use in production.** |
| `GMAIL_SYNC_INTERVAL_MINUTES` | No | Background sync interval (default `5`; `0` disables) |
| `GMAIL_FETCH_MAX_RESULTS` | No | Max inbox messages fetched per sync (default `25`) |
| `ADMIN_USERNAME` | No | Default admin username created on first startup |
| `ADMIN_EMAIL` | No | Default admin email |
| `ADMIN_PASSWORD` | Yes (prod) | Default admin password — **change in production** |
| `CRAWLER_TIMEOUT_SECONDS` | No | HTTP timeout for website crawler (default `12`) |
| `CRAWLER_MAX_LINKS` | No | Max links analyzed per crawl (default `50`) |
| `CRAWLER_MAX_BYTES` | No | Max HTML bytes downloaded (default `2000000`) |

---

## Gmail OAuth Setup

1. Open [Google Cloud Console](https://console.cloud.google.com/).  
2. Create a project (or select an existing one).  
3. Enable the **Gmail API**.  
4. Configure the **OAuth consent screen** (External or Internal). Add scopes for Gmail readonly if prompted.  
5. Create **OAuth 2.0 Client ID** credentials → Application type **Web application**.  
6. Under **Authorized redirect URIs**, add exactly:

   ```text
   http://127.0.0.1:5000/gmail/callback
   ```

   For production, add your HTTPS callback URL instead (and set `GOOGLE_REDIRECT_URI` to match).  
7. Copy the **Client ID** and **Client Secret** into your `.env` as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.  
8. Restart the app, sign in to ShieldScan, and click **Connect Gmail**.

> Do not commit client secrets, token files, or a real `.env` file.

---

## Running the Application

### Development

```bash
python run.py
```

Default bind: `127.0.0.1:5000` (see `run.py`).

### Production-style (Gunicorn)

```bash
gunicorn -b 0.0.0.0:$PORT "run:app"
```

Or rely on the included `Procfile` on platforms that read it.

### Admin access

On first startup, a default admin account is created from `ADMIN_*` environment variables. Sign in via the admin login route provided by the app, then change the password.

---

## Future Improvements

- PostgreSQL as the default production database with migrations (Alembic)  
- Docker / docker-compose for one-command local and cloud deploys  
- CI (lint + tests) on pull requests  
- Stronger rate limiting and CSRF protection on mutating routes  
- Optional email alerting for high-risk detections  
- Model versioning and admin-triggered retrain workflows  
- Git LFS or artifact hosting for large model/dataset files  

---

## Author

Built in collaboration between:

- [@KiryuJiiro](https://github.com/KiryuJiiro)  
- [@Luz-ana](https://github.com/Luz-ana)

Contributions and issue reports are welcome via GitHub.
