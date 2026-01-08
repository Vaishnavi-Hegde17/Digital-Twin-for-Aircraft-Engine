import os
import json
import pandas as pd
from flask import Flask, request, jsonify, session
from flask import send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from utils import generate_sample
import joblib
import smtplib
from email.message import EmailMessage

# Basic configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.xlsx")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Serve frontend files from the sibling Frontend folder so pages run on same origin
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, os.pardir, 'Frontend'))

@app.route('/', defaults={'path': 'login.html'})
@app.route('/<path:path>')
def serve_frontend(path):
    target = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(target) and os.path.isfile(target):
        return send_from_directory(FRONTEND_DIR, path)
    # fallback to login page for unknown paths (SPAs)
    return send_from_directory(FRONTEND_DIR, 'login.html')

# Load config or create default
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {
        "SECRET_KEY": "change_this_secret",
        "SMTP": {
            "HOST": "smtp.example.com",
            "PORT": 587,
            "USER": "your@domain.com",
            "PASSWORD": "yourpassword",
            "USE_TLS": True
        },
        "MODEL": {
            "type": "rf",
            "rf_path": "rf_engine_health_model.pkl",
            "scaler_path": "scaler.pkl",
            "label_encoder_path": "label_encoder.pkl",
            "features_path": "model_features.pkl"
        }
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

app.secret_key = config.get("SECRET_KEY", os.urandom(24))

# Allow anonymous predictions for local/dev testing when enabled in config
ALLOW_ANON_PREDICT = config.get("ALLOW_ANON_PREDICT", False)

# Load model and preprocessors if available
MODEL = None
SCALER = None
LE = None
MODEL_FEATURES = None
MODEL_TYPE = config.get("MODEL", {}).get("type", "rf")

try:
    mconf = config.get("MODEL", {})
    if MODEL_TYPE == "rf":
        def resolve_path(p):
            # try absolute / relative to BASE_DIR / savedmodels folder
            if not p:
                return None
            if os.path.isabs(p) and os.path.exists(p):
                return p
            candidate = os.path.join(BASE_DIR, p)
            if os.path.exists(candidate):
                return candidate
            # try savedmodels subfolder
            candidate2 = os.path.join(BASE_DIR, "savedmodels", os.path.basename(p))
            if os.path.exists(candidate2):
                return candidate2
            return None

        rf_p = resolve_path(mconf.get("rf_path", "rf_engine_health_model.pkl"))
        sc_p = resolve_path(mconf.get("scaler_path", "scaler.pkl"))
        le_p = resolve_path(mconf.get("label_encoder_path", "label_encoder.pkl"))
        ft_p = resolve_path(mconf.get("features_path", "model_features.pkl"))

        if rf_p and sc_p and le_p and ft_p:
            MODEL = joblib.load(rf_p)
            SCALER = joblib.load(sc_p)
            LE = joblib.load(le_p)
            MODEL_FEATURES = joblib.load(ft_p)
        else:
            print("Model files not found. Looked for:", mconf)
except Exception as e:
    print("Model load warning:", e)


def send_alert_email(to_email, subject, body):
    smtp = config.get("SMTP", {})
    host = smtp.get("HOST")
    port = smtp.get("PORT")
    user = smtp.get("USER")
    password = smtp.get("PASSWORD")
    use_tls = smtp.get("USE_TLS", True)

    if not host or not user or not password:
        print("SMTP not configured; skipping email")
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_email
        msg.set_content(body)

        server = smtplib.SMTP(host, port, timeout=10)
        if use_tls:
            server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Failed to send email:", e)
        return False


def read_users():
    if os.path.exists(USERS_FILE):
        try:
            return pd.read_excel(USERS_FILE)
        except Exception:
            return pd.DataFrame(columns=["username", "email", "password"])
    return pd.DataFrame(columns=["username", "email", "password"])


def write_users(df):
    df.to_excel(USERS_FILE, index=False)


def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        # allow anonymous access to predict endpoints when enabled in config
        try:
            from flask import request
            path = request.path
        except Exception:
            path = None

        if ALLOW_ANON_PREDICT and path in ("/predict", "/sensor/latest"):
            return fn(*args, **kwargs)

        if "user" not in session:
            return jsonify({"error": "unauthorized"}), 401
        return fn(*args, **kwargs)

    return wrapper


@app.route("/register", methods=["POST"])
def register():
    data = request.json or request.form
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "missing fields"}), 400

    users = read_users()
    if not users.empty and username in users["username"].values:
        return jsonify({"error": "username exists"}), 400

    hashed = generate_password_hash(password)
    new_user = pd.DataFrame([{"username": username, "email": email, "password": hashed}])
    users = pd.concat([users, new_user], ignore_index=True)
    write_users(users)
    return jsonify({"status": "ok"})


@app.route("/login", methods=["POST"])
def login():
    data = request.json or request.form
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "missing fields"}), 400

    users = read_users()
    if users.empty:
        return jsonify({"error": "no users"}), 400

    row = users[users["username"] == username]
    if row.empty:
        return jsonify({"error": "invalid credentials"}), 401

    saved = row.iloc[0]
    if not check_password_hash(saved["password"], password):
        return jsonify({"error": "invalid credentials"}), 401

    session["user"] = username
    return jsonify({"status": "ok", "username": username})


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.pop("user", None)
    return jsonify({"status": "ok"})


@app.route("/sensor/latest", methods=["GET"])
@login_required
def sensor_latest():
    sample = generate_sample(live=True)

    # run prediction if model available
    pred_label = None
    pred_proba = None
    if MODEL is not None and SCALER is not None and LE is not None and MODEL_FEATURES is not None:
        try:
            import pandas as pd
            # build DataFrame row with model features
            row = pd.DataFrame([sample])
            # one-hot phase
            row = pd.get_dummies(row, columns=["Phase"])
            # align
            for f in MODEL_FEATURES:
                if f not in row.columns:
                    row[f] = 0
            row = row[MODEL_FEATURES]
            X = SCALER.transform(row)
            proba = MODEL.predict_proba(X)[0]
            idx = int(proba.argmax())
            pred_label = LE.inverse_transform([idx])[0]
            pred_proba = {LE.inverse_transform([i])[0]: float(proba[i]) for i in range(len(proba))}

            # if anomaly (not NORMAL) -> send alert
            if pred_label != "NORMAL":
                users = read_users()
                user = session.get("user")
                rowu = users[users["username"] == user]
                if not rowu.empty:
                    to_email = rowu.iloc[0].get("email")
                    subject = f"Engine Alert: {pred_label} detected"
                    body = f"An anomaly was detected: {pred_label} with probabilities {pred_proba}\nSample: {sample}"
                    send_alert_email(to_email, subject, body)

        except Exception as e:
            print("Prediction error:", e)

    return jsonify({"sample": sample, "prediction": pred_label, "probabilities": pred_proba})


@app.route("/predict", methods=["POST"])
@login_required
def predict():
    data = request.json
    if not data:
        return jsonify({"error": "no data"}), 400

    if MODEL is None:
        return jsonify({"error": "model not loaded", "hint": "Place model files in Backend/savedmodels or update Backend/config.json MODEL paths."}), 500

    try:
        import pandas as pd
        row = pd.DataFrame([data])
        row = pd.get_dummies(row, columns=["Phase"]) if "Phase" in row.columns else row
        for f in MODEL_FEATURES:
            if f not in row.columns:
                row[f] = 0
        row = row[MODEL_FEATURES]
        X = SCALER.transform(row)
        proba = MODEL.predict_proba(X)[0]
        idx = int(proba.argmax())
        pred_label = LE.inverse_transform([idx])[0]
        pred_proba = {LE.inverse_transform([i])[0]: float(proba[i]) for i in range(len(proba))}
        return jsonify({"prediction": pred_label, "probabilities": pred_proba})
    except Exception as e:
        print("Predict error:", e)
        return jsonify({"error": "prediction failed"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
