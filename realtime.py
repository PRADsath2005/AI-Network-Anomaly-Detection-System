"""
realtime.py
-----------
Simulates real-time network traffic by streaming the test dataset in chunks.
FIX 1: Model is loaded ONCE outside the loop (not reloaded per chunk).
FIX 2: stop/start controlled via a threading.Event — thread terminates cleanly.
FIX 3: Error handling around prediction, DB insert, and alert dispatch.
"""

import os
import time
import random
import logging
import threading
import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR      = os.path.dirname(__file__)
MODELS_DIR    = os.path.join(BASE_DIR, "models")
RF_MODEL_PATH = os.path.join(MODELS_DIR, "rf_model.pkl")
SCALER_PATH   = os.path.join(MODELS_DIR, "scaler.pkl")

# -------------------------------------------------------------------
# Simulation state — shared across Flask + this module
# -------------------------------------------------------------------
_stop_event   = threading.Event()   # set() → stops the loop
_sim_thread   = None                # reference to the running thread
_sim_lock     = threading.Lock()    # guards thread lifecycle

# Stats updated in real-time, readable by Flask /api/stats
simulation_stats = {
    "running":    False,
    "processed":  0,
    "attacks":    0,
    "normals":    0,
}


# -------------------------------------------------------------------
# IP generator
# -------------------------------------------------------------------
def _random_ip() -> str:
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


# -------------------------------------------------------------------
# Core simulation loop
# -------------------------------------------------------------------
def _run_simulation(
    chunk_size: int = 50,
    delay_seconds: float = 1.5,
    max_chunks: int = None,   # None = unlimited
):
    """
    Internal loop: streams test data, predicts, stores, alerts.
    Runs until _stop_event is set or max_chunks reached.
    Model loaded ONCE before the loop to avoid redundant I/O.
    """
    import joblib
    from database import init_db, insert_log
    from alerts import trigger_alert

    # -- Init DB ----------------------------------------------------------
    init_db()

    # -- Load model ONCE (FIX: not inside loop) ---------------------------
    try:
        rf_model = joblib.load(RF_MODEL_PATH)
        scaler   = joblib.load(SCALER_PATH)
        logger.info("[REALTIME] Model loaded from %s", RF_MODEL_PATH)
    except Exception as e:
        logger.error("[REALTIME] Cannot load model: %s. Run python model.py first.", e)
        simulation_stats["running"] = False
        return

    # -- Load test data ---------------------------------------------------
    try:
        from preprocess import load_and_preprocess
        _, X_test, _, y_test, _, _, _ = load_and_preprocess()
    except Exception as e:
        logger.error("[REALTIME] Cannot load data: %s", e)
        simulation_stats["running"] = False
        return

    n_rows      = len(X_test)
    chunk_count = 0
    idx         = 0

    logger.info("[REALTIME] Starting simulation (chunk_size=%d, delay=%.1fs)",
                chunk_size, delay_seconds)

    while not _stop_event.is_set():
        if max_chunks is not None and chunk_count >= max_chunks:
            logger.info("[REALTIME] Reached max_chunks=%d. Stopping.", max_chunks)
            break

        # Wrap around if we run out of test rows
        end = min(idx + chunk_size, n_rows)
        chunk = X_test[idx:end]
        idx   = end % n_rows if end >= n_rows else end

        # -- Predict ------------------------------------------------------
        try:
            probas      = rf_model.predict_proba(chunk)   # shape (n, 2)
            predictions = np.argmax(probas, axis=1)       # 0=Normal, 1=Attack
            confidences = probas[np.arange(len(probas)), predictions]
        except Exception as e:
            logger.error("[REALTIME] Prediction error: %s", e)
            time.sleep(delay_seconds)
            continue

        # -- Store + alert each row ---------------------------------------
        for pred, conf in zip(predictions, confidences):
            label     = "Attack" if pred == 1 else "Normal"
            source_ip = _random_ip()

            try:
                insert_log(source_ip, label, float(conf))
            except Exception as e:
                logger.error("[REALTIME] DB insert error: %s", e)

            if pred == 1:
                trigger_alert(source_ip, float(conf))

            # Update in-memory stats
            simulation_stats["processed"] += 1
            if pred == 1:
                simulation_stats["attacks"] += 1
            else:
                simulation_stats["normals"] += 1

        chunk_count += 1
        logger.info(
            "[REALTIME] Chunk %d processed | attacks=%d normals=%d",
            chunk_count,
            simulation_stats["attacks"],
            simulation_stats["normals"],
        )

        # -- Wait or check stop -------------------------------------------
        _stop_event.wait(timeout=delay_seconds)

    simulation_stats["running"] = False
    logger.info("[REALTIME] Simulation stopped.")


# -------------------------------------------------------------------
# Public API — used by Flask app.py
# -------------------------------------------------------------------
def start_simulation(chunk_size: int = 50, delay_seconds: float = 1.5) -> bool:
    """
    Start the simulation in a background daemon thread.
    Returns False if already running.
    """
    global _sim_thread
    with _sim_lock:
        if simulation_stats["running"]:
            logger.warning("[REALTIME] Already running.")
            return False
        _stop_event.clear()
        simulation_stats["running"]   = True
        simulation_stats["processed"] = 0
        simulation_stats["attacks"]   = 0
        simulation_stats["normals"]   = 0

        _sim_thread = threading.Thread(
            target=_run_simulation,
            kwargs={"chunk_size": chunk_size, "delay_seconds": delay_seconds},
            daemon=True,   # FIX: daemon=True so it doesn't prevent Flask from exiting
            name="SimulationThread",
        )
        _sim_thread.start()
        logger.info("[REALTIME] Simulation thread started.")
    return True


def stop_simulation() -> bool:
    """
    Signal the simulation thread to stop gracefully.
    Returns False if not running.
    """
    with _sim_lock:
        if not simulation_stats["running"]:
            return False
        _stop_event.set()
    logger.info("[REALTIME] Stop signal sent.")
    return True


def is_running() -> bool:
    return simulation_stats.get("running", False)


# -------------------------------------------------------------------
# Standalone execution
# -------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    start_simulation(chunk_size=30, delay_seconds=2.0)
    try:
        while is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Ctrl+C — stopping simulation...")
        stop_simulation()
