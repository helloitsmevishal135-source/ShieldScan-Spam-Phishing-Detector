"""
Legacy single-page scanner (no authentication).

For the full dashboard with login, scan history, and stats, use:
    python run.py
"""

from flask import Flask, render_template, request

# your unified ML pipeline
from main import predict

app = Flask(__name__)


# =========================
# HOME ROUTE (SINGLE INPUT)
# =========================

@app.route("/", methods=["GET", "POST"])
def home():

    result = None

    if request.method == "POST":

        user_input = request.form.get("input_data", "").strip()

        if user_input:

            res = predict(user_input)

            result = {
                "type": res["type"],
                "label": res["label"],
                "confidence": round(float(res["confidence"]), 2)
            }

    return render_template("index.html", result=result)


# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    app.run(debug=True)