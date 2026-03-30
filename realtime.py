import os
import time
import random
import logging
import threading
import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, "models")
RF_MODEL_PATH = os.path.join(MODELS_DIR, "rf_model.pkl")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")

# ---------------- STATE ----------------
_stop_event = threading.Event()
_sim_thread = None
_sim_lock = threading.Lock()

simulation_stats = {
    "running": False,
    "total": 0,
    "attacks": 0,
    "normal": 0,
}

# ---------------- IP ----------------
def _random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


# ---------------- SIMULATION ----------------
def _run_simulation(chunk_size=50, delay_seconds=1.5):
    import joblib
    from database import init_db
    from alerts import trigger_alert

    init_db()

    # Load model
    try:
        rf_model = joblib.load(RF_MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        logger.info("Model loaded")
    except Exception as e:
        logger.error("Model load error: %s", e)
        simulation_stats["running"] = False
        return

    # Load data
    try:
        from preprocess import load_and_preprocess
        _, X_test, _, _, _, _, _ = load_and_preprocess()
    except Exception as e:
        logger.error("Data load error: %s", e)
        simulation_stats["running"] = False
        return

    n_rows = len(X_test)
    idx = 0

    while not _stop_event.is_set():

        # chunk
        end = min(idx + chunk_size, n_rows)
        chunk = X_test[idx:end]
        idx = end if end < n_rows else 0

        # prediction
        try:
            probas = rf_model.predict_proba(chunk)
            predictions = np.argmax(probas, axis=1)
            confidences = probas[np.arange(len(probas)), predictions]
        except Exception as e:
            logger.error("Prediction error: %s", e)
            time.sleep(delay_seconds)
            continue

        # process each row
        for pred, conf in zip(predictions, confidences):
            simulation_stats["total"] += 1

            if pred == 1:
                simulation_stats["attacks"] += 1

                # alert
                try:
                    trigger_alert(_random_ip(), conf)
                except Exception as e:
                    logger.error("Alert error: %s", e)
            else:
                simulation_stats["normal"] += 1

        # wait
        _stop_event.wait(timeout=delay_seconds)

    simulation_stats["running"] = False
    logger.info("Simulation stopped")


# ---------------- START ----------------
def start_simulation(chunk_size=50, delay_seconds=1.5):
    global _sim_thread

    with _sim_lock:
        if simulation_stats["running"]:
            return False

        _stop_event.clear()

        simulation_stats["running"] = True
        simulation_stats["total"] = 0
        simulation_stats["attacks"] = 0
        simulation_stats["normal"] = 0

        _sim_thread = threading.Thread(
            target=_run_simulation,
            kwargs={"chunk_size": chunk_size, "delay_seconds": delay_seconds},
            daemon=True
        )

        _sim_thread.start()
        logger.info("Simulation started")

    return True


# ---------------- STOP ----------------
def stop_simulation():
    with _sim_lock:
        if not simulation_stats["running"]:
            return False

        _stop_event.set()
        logger.info("Stop signal sent")

    return True


# ---------------- STATUS ----------------
def is_running():
    return simulation_stats.get("running", False)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    start_simulation()

    try:
        while is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        stop_simulation()
