Project: Digital Twin for Aircraft Engine

Run the backend API (Flask):

1. Create virtual environment and install requirements

```bash
python -m venv dt_env
# Windows
dt_env\Scripts\activate
pip install -r Backend/requirements.txt
```

2. Configure SMTP and secret key (optional) in `Backend/config.json` or edit default values.

3. Run the backend

```bash
python Backend/app.py
```

4. Open frontend: open `Frontend/login.html` in your browser. The frontend talks to `http://127.0.0.1:5000`.

Notes:
- Registrations are stored in `Backend/users.xlsx`.
- Models should exist in `Backend/` (e.g., `rf_engine_health_model.pkl`, `scaler.pkl`, `label_encoder.pkl`, `model_features.pkl`).
- For demo the dashboard polls every 5 seconds; change the interval in `Frontend/script.js` to 300000 for 5 minutes.
