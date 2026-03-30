import time
import random
import threading
from database import insert_log

_stop_event = threading.Event()

simulation_stats = {
    "running": False,
    "processed": 0,
    "attacks": 0,
    "normals": 0,
}


# ---------------- RANDOM IP ----------------
def _random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


# ---------------- MAIN LOOP ----------------
def _run():
    from alerts import trigger_alert

    print("🔥 SIMULATION STARTED")

    while not _stop_event.is_set():
        time.sleep(2)

        simulation_stats["processed"] += 1

        ip = _random_ip()   # 🔥 ADD THIS

        if random.random() > 0.7:
            simulation_stats["attacks"] += 1
            prediction = "Attack"   # 🔥 ADD THIS
            trigger_alert(ip, 0.95)
        else:
            simulation_stats["normals"] += 1
            prediction = "Normal"   # 🔥 ADD THIS

        # 🔥 SAVE TO DATABASE
        insert_log({
            "source_ip": ip,
            "prediction": prediction,
            "confidence_score": 0.95
        })

        print("STATS:", simulation_stats)

    simulation_stats["running"] = False
    print("⛔ SIMULATION STOPPED")


# ---------------- START ----------------
def start_simulation():

    if simulation_stats["running"]:
        print("⚠ Already running")
        return

    print("▶ Starting simulation...")

    _stop_event.clear()

    simulation_stats["running"] = True
    simulation_stats["processed"] = 0
    simulation_stats["attacks"] = 0
    simulation_stats["normals"] = 0

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# ---------------- STOP ----------------
def stop_simulation():
    print("⏹ Stopping simulation...")
    _stop_event.set()


# ---------------- STATUS ----------------
def is_running():
    return simulation_stats["running"]
