# AI-Based Network Anomaly Detection System

> IEEE-inspired, product-level ML system for classifying network traffic as **Normal** or **Attack** in real-time, with a live Flask dashboard, SQLite logging, and alert notifications.

---

## 📁 Project Structure

```
pdp/
├── app.py                 ← Flask web dashboard
├── model.py               ← ML training (Random Forest + Isolation Forest)
├── preprocess.py          ← Data loading, cleaning, encoding, normalization
├── realtime.py            ← Real-time simulation (chunks streamed from test set)
├── database.py            ← SQLite integration (detection_logs table)
├── alerts.py              ← Desktop + email alerts on attack detection
├── download_dataset.py    ← Auto-downloads NSL-KDD dataset
├── requirements.txt       ← Python dependencies
├── data/
│   ├── KDDTrain+.txt      ← NSL-KDD training file (downloaded)
│   └── KDDTest+.txt       ← NSL-KDD test file (downloaded)
├── models/
│   ├── rf_model.pkl       ← Trained Random Forest model
│   ├── if_model.pkl       ← Trained Isolation Forest model
│   └── scaler.pkl         ← Fitted MinMaxScaler
├── static/
│   ├── style.css          ← Dark glassmorphism dashboard styles
│   ├── dashboard.js       ← SSE client + Chart.js live graph
│   ├── confusion_matrix.png
│   ├── metrics.png
│   └── feature_importance.png
├── templates/
│   ├── index.html         ← Main dashboard page
│   └── logs.html          ← Paginated detection logs page
└── anomaly_detection.db   ← SQLite database (auto-created)
```

---

## ⚙️ Prerequisites

- Python 3.10+ (tested on 3.11)
- Internet connection for initial dataset download

---

## 🚀 Step-by-Step Setup & Run

### Step 1 — Install dependencies

```bash
cd C:\Users\LENOVO\Desktop\pdp
pip install -r requirements.txt
```

---

### Step 2 — Download the NSL-KDD dataset

```bash
python download_dataset.py
```

Downloads `KDDTrain+.txt` and `KDDTest+.txt` into `./data/`.  
> If this fails, download manually from https://github.com/defcom17/NSL_KDD and place in `./data/`.

---

### Step 3 — Train the model

```bash
python model.py
```

**Output:**
- Prints Accuracy, Precision, Recall, F1-Score, and classification report
- Saves `models/rf_model.pkl`, `models/if_model.pkl`, `models/scaler.pkl`
- Saves `static/confusion_matrix.png`, `static/metrics.png`, `static/feature_importance.png`

**Sample output:**
```
==================================================
  Accuracy : 99.21%
  Precision: 99.14%
  Recall   : 99.35%
  F1-Score : 99.24%
==================================================
              precision    recall  f1-score
    Normal       0.99      0.99      0.99
    Attack       0.99      0.99      0.99
```

---

### Step 4 — Launch the Flask dashboard

```bash
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

---

### Step 5 — Run real-time simulation

Either:
- Click **▶ Start Simulation** in the dashboard, **OR**
- Run standalone: `python realtime.py`

The simulation streams the test dataset in chunks of 50 rows every 1.5 seconds,  
predicts each row, stores results in SQLite, and fires alerts for attacks.

---

## 📊 Dashboard Pages

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:5000/` | Live dashboard — stat cards, Chart.js traffic graph, recent logs, model charts |
| `http://127.0.0.1:5000/logs` | Full paginated detection_logs table (50 rows/page) |
| `http://127.0.0.1:5000/api/stats` | JSON API — stats + last 20 logs |
| `http://127.0.0.1:5000/api/stream` | SSE stream (used by dashboard JS) |

---

## 🗄️ Database Schema

Table: **`detection_logs`** (SQLite — `anomaly_detection.db`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK AUTOINCREMENT | Row identifier |
| `timestamp` | TEXT | UTC datetime |
| `source_ip` | TEXT | Simulated source IP |
| `prediction` | TEXT | `Normal` or `Attack` |
| `confidence_score` | REAL | Model confidence (0–1) |

Query the DB directly:
```bash
python -c "import database; print(database.fetch_recent_logs(5))"
python -c "import database; print(database.fetch_stats())"
```

---

## 🔔 Alert Configuration (Optional)

### Desktop alerts (enabled by default)
Uses `plyer` — shows a system toast notification when an attack is detected. No config needed.

### Email alerts (disabled by default)
Set environment variables before running `app.py`:

```bash
set ALERT_EMAIL_ENABLED=true
set SENDER_EMAIL=your_gmail@gmail.com
# IMPORTANT: Use a Gmail App Password — NOT your account password
# Generate at: https://myaccount.google.com/apppasswords
set SENDER_APP_PASSWORD=xxxx xxxx xxxx xxxx
set RECIPIENT_EMAIL=recipient@example.com
python app.py
```

---

## 🔧 Fixes Applied

| # | Fix | Module |
|---|-----|--------|
| 1 | Correct 43-column NSL-KDD column assignment | `preprocess.py` |
| 2 | Proper duplicate removal + missing-value imputation | `preprocess.py` |
| 3 | RF model loaded **once** before simulation loop | `realtime.py` |
| 4 | Secure SMTP with STARTTLS + App Password | `alerts.py` |
| 5 | Graceful email/desktop alert failure (no crash) | `alerts.py` |
| 6 | `threading.Event` for clean simulation stop/start | `realtime.py` |
| 7 | Daemon thread — exits when Flask exits | `realtime.py` |
| 8 | try-except on all DB operations | `database.py` |
| 9 | try-except on all Flask routes | `app.py` |
| 10 | try-except on prediction + DB insert in loop | `realtime.py` |

---

## 📦 Dependencies

```
flask            ← Web framework / dashboard
scikit-learn     ← Random Forest, Isolation Forest, metrics
pandas           ← Data manipulation
numpy            ← Numerical operations
matplotlib       ← Chart generation
seaborn          ← Heatmap (confusion matrix)
joblib           ← Model serialization
plyer            ← Desktop notifications
```
