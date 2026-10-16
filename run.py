"""
Entry point for the ShieldScan web application.

Run from the project root:
    python run.py
"""

import os
import sys

# Ensure ML modules (main.py, models/, etc.) resolve from project root
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# .env + OAUTHLIB_INSECURE_TRANSPORT (dev only) before app/OAuth imports
from app.env_bootstrap import bootstrap_environment

bootstrap_environment()

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
