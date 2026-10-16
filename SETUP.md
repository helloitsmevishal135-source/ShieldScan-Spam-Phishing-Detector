# ShieldScan — Setup & Integration Guide

This guide explains how to run the production-style web app built around your existing ML pipeline.

## Project structure

```
modules/
├── app/                    # Flask application package
│   ├── __init__.py         # App factory (create_app)
│   ├── config.py           # Configuration
│   ├── extensions.py       # SQLAlchemy, Flask-Login
│   ├── auth/               # Login, register, logout
│   ├── routes/             # Dashboard, profile
│   ├── models/             # User, Scan (database)
│   └── services/           # ML wrapper + scan persistence
├── main.py                 # YOUR ML PIPELINE (unchanged)
├── models/                 # Trained .pkl files
├── templates/              # HTML templates
├── static/                 # CSS & JavaScript
├── instance/               # SQLite database (auto-created)
├── run.py                  # Start the web app
└── requirements.txt
```

## ML integration (unchanged logic)

Your detection logic remains in `main.py`:

- `predict()` — routes TEXT vs URL and calls Naive Bayes / Random Forest
- Models loaded from `models/nb_model.pkl`, `vectorizer.pkl`, `rf_model.pkl`
- Whitelist from `whitelist.csv`

The web layer only calls this via `app/services/ml_service.py`:

```python
from main import predict as _predict
```

No models were retrained or modified.

## Quick start

### 1. Install dependencies

```bash
cd modules
pip install -r requirements.txt
```

### 2. Verify ML assets

Ensure these exist in the project root:

- `models/nb_model.pkl`
- `models/vectorizer.pkl`
- `models/rf_model.pkl`
- `whitelist.csv`

### 3. Run the application

```bash
python run.py
```

Open: **http://127.0.0.1:5000**

- First visit redirects to **Register** → create an account → **Dashboard**

### 4. Legacy single-page app (optional)

The original `app.py` still works for a simple unauthenticated scan UI:

```bash
python app.py
```

For the full authenticated experience, use `run.py` instead.

## Features

| Feature | Route / location |
|---------|------------------|
| Register | `/auth/register` |
| Login | `/auth/login` |
| Logout | `/auth/logout` |
| Dashboard | `/` (after login) |
| Scan (AJAX) | `POST /scan` |
| Connect Gmail | `GET /gmail/connect` |
| Gmail OAuth callback | `GET /gmail/callback` |
| Gmail disconnect | `POST /gmail/disconnect` |
| Gmail email results (JSON) | `GET /gmail/emails` |
| Profile | `/profile` |

## Gmail OAuth2 (automated email scanning)

1. Copy `.env.example` to `.env` and fill in Google credentials.
2. In [Google Cloud Console](https://console.cloud.google.com/):
   - Create an OAuth 2.0 **Web application** client
   - Enable **Gmail API**
   - Add authorized redirect URI: `http://127.0.0.1:5000/gmail/callback` (must match `GOOGLE_REDIRECT_URI`)
3. Sign in to ShieldScan → **Connect Gmail** on the dashboard.
4. New inbox messages are fetched and analyzed with your existing `main.py` pipeline (no duplicate detection logic).
5. Background sync runs every `GMAIL_SYNC_INTERVAL_MINUTES` (default: 5).

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLIENT_ID` | OAuth client ID (server only) |
| `GOOGLE_CLIENT_SECRET` | OAuth secret (never expose to browser) |
| `GOOGLE_REDIRECT_URI` | Callback URL registered in Google Cloud |
| `GMAIL_SYNC_INTERVAL_MINUTES` | Background fetch interval |
| `GMAIL_FETCH_MAX_RESULTS` | Max messages per sync |
| `FLASK_ENV` | `development` locally; `production` on deploy |
| `OAUTHLIB_INSECURE_TRANSPORT` | Set to `1` in `.env` for local HTTP OAuth only |

**Local HTTP OAuth:** Google blocks token exchange over HTTP unless `OAUTHLIB_INSECURE_TRANSPORT=1` is set before OAuth runs. The app loads `.env` at startup and sets this automatically when `FLASK_ENV=development`. In production (`FLASK_ENV=production`), HTTPS is enforced and this variable is removed.

## Database

- **SQLite** file: `instance/shield.db`
- Tables: `users`, `scans`, `email_scans`
- Created automatically on first run (existing DBs get new columns via lightweight migration)

To reset the database, delete `instance/shield.db` and restart the app.

## Production notes

1. Set a strong secret key:
   ```bash
   set SECRET_KEY=your-random-secret-key
   ```
2. Use PostgreSQL later by setting `DATABASE_URL`.
3. Run with a production WSGI server (e.g. Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn "run:app" -b 0.0.0.0:8000
   ```

## Threat levels (UI mapping)

| Level | Color | When |
|-------|-------|------|
| Safe | Green | HAM / SAFE labels |
| Suspicious | Yellow | Threat with 40–69% confidence |
| Dangerous | Red | SPAM / PHISHING with ≥70% confidence |
