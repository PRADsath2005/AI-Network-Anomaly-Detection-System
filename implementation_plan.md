# AI-Based Network Anomaly Detection System — Implementation Plan

A product-level, IEEE-inspired system for detecting network traffic anomalies using Machine Learning, with a real-time Flask dashboard, SQLite logging, email/desktop alerts, and matplotlib visualizations.

---

## Proposed Changes

### Project Root: `c:\Users\LENOVO\Desktop\pdp\`

---

#### [NEW] `requirements.txt`
All Python dependencies: flask, scikit-learn, pandas, numpy, matplotlib, seaborn, imbalanced-learn, plyer (desktop alerts).

---

### Data Layer

#### [NEW] `data/` directory
- `KDDTrain+.txt` and `KDDTest+.txt` — NSL-KDD dataset files (downloaded by a helper script).
- `download_dataset.py` — auto-downloads NSL-KDD via URL.

---

### Core Modules

#### [NEW] `preprocess.py`
- Load KDDTrain+ / KDDTest+ CSV files with correct column names.
- Drop duplicates, handle missing values.
- Encode categorical columns (protocol_type, service, flag) with LabelEncoder.
- MinMaxScaler normalization on numeric features.
- Binarize labels: `normal` → 0, everything else → 1 (Attack).
- Exports: `load_and_preprocess()` → returns `(X_train, X_test, y_train, y_test, feature_names)`.

#### [NEW] `model.py`
- Train **Random Forest** classifier on preprocessed data.
- Optionally train **Isolation Forest** for unsupervised anomaly scoring.
- Evaluate: accuracy, precision, recall, F1, confusion matrix.
- Save trained model to `models/rf_model.pkl` via joblib.
- Generate and save: confusion matrix heatmap → `static/confusion_matrix.png`, metrics bar chart → `static/metrics.png`.
- Entry point: `python model.py` trains and evaluates the model.

#### [NEW] `database.py`
- SQLite database: `anomaly_detection.db`.
- Table `detection_logs`:
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `timestamp` TEXT
  - `source_ip` TEXT
  - `prediction` TEXT (Normal / Attack)
  - `confidence_score` REAL
- Exports: `init_db()`, `insert_log(...)`, `fetch_all_logs()`, `fetch_recent_logs(n)`.

#### [NEW] `alerts.py`
- `send_email_alert(details)` — sends SMTP email (Gmail) on Attack detection. Credentials via env vars or config.
- `send_desktop_alert(details)` — uses `plyer.notification` for desktop toast.
- `trigger_alert(source_ip, confidence)` — calls both; gracefully fails if not configured.

#### [NEW] `realtime.py`
- Load test set from `preprocess.py`.
- Stream in chunks of N rows (configurable, default 50).
- For each chunk: predict with loaded RF model, store each row to `detection_logs`, trigger `alerts.py` if Attack detected.
- Simulates a "live feed" with a configurable delay between chunks (`time.sleep`).
- Can be run standalone: `python realtime.py` or called by Flask background thread.

#### [NEW] `app.py`
- Flask application with routes:
  - `GET /` → dashboard (index.html) with latest stats.
  - `GET /logs` → paginated detection_logs table page.
  - `GET /api/stats` → JSON: total, attacks, normals, recent 20 logs.
  - `GET /api/stream` → Server-Sent Events (SSE) for live updates.
  - `POST /api/start_simulation` → starts `realtime.py` in background thread.
  - `GET /api/charts` → returns URLs of saved chart images.
- Serves static images (confusion matrix, metrics charts).

---

### Templates & Static

#### [NEW] `templates/index.html`
- Dark-themed dashboard with:
  - Live stat cards (Total / Attacks / Normals / Attack Rate %).
  - Real-time traffic chart (Chart.js line chart, polling `/api/stats`).
  - Recent logs table (last 20 rows from DB).
  - Confusion matrix + metrics bar chart images embedded.
  - Start Simulation button.

#### [NEW] `templates/logs.html`
- Full paginated table of all detection_logs from SQLite.
- Color-coded rows: red for Attack, green for Normal.

#### [NEW] `static/style.css`
- Dark glassmorphism theme, gradient cards, responsive layout.

#### [NEW] `static/dashboard.js`
- Polls `/api/stats` every 3 seconds.
- Updates stat cards and Chart.js line graph dynamically.

---

### Documentation

#### [NEW] `README.md`
- Prerequisites, installation, how to download dataset, how to train model, how to run Flask app, how to configure email alerts.

---

## Verification Plan

### Automated / Terminal Tests

1. **Install dependencies**
   ```
   cd c:\Users\LENOVO\Desktop\pdp
   pip install -r requirements.txt
   ```

2. **Download dataset**
   ```
   python download_dataset.py
   ```
   Expected: `data/KDDTrain+.txt` and `data/KDDTest+.txt` created.

3. **Train model**
   ```
   python model.py
   ```
   Expected: Accuracy, Precision, Recall, F1 printed; `models/rf_model.pkl`, `static/confusion_matrix.png`, `static/metrics.png` created.

4. **Initialize DB and run realtime simulation**
   ```
   python realtime.py
   ```
   Expected: Chunk-by-chunk predictions printed; DB populated with rows.

5. **Launch Flask dashboard**
   ```
   python app.py
   ```
   Expected: Server running at `http://127.0.0.1:5000`; dashboard loads and shows stats and charts.

### Manual Verification (Browser)
- Open `http://127.0.0.1:5000` — confirm dashboard renders with stat cards and charts.
- Click **Start Simulation** — confirm live log table updates every few seconds.
- Open `http://127.0.0.1:5000/logs` — confirm full paginated log table with color-coded rows.
- Check DB: `python -c "import database; print(database.fetch_recent_logs(5))"` — confirm rows returned.
