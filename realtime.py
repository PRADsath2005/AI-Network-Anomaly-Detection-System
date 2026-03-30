import time
import random
import threading

# ---------------- STATE ----------------
_stop_event = threading.Event()
_sim_thread = None

simulation_stats = {
    "running": False,
    "processed": 0,
    "attacks": 0,
    "normals": 0,
}

# ---------------- IP ----------------
def _random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

# ---------------- SIMULATION ----------------
def _run_simulation(delay_seconds=2):
    from alerts import trigger_alert

    print("🔥 Dummy Simulation Started")

    while not _stop_event.is_set():

        time.sleep(delay_seconds)

        simulation_stats["processed"] += 1

        # random attack
        if random.random() > 0.7:
            simulation_stats["attacks"] += 1

            # 🔥 EMAIL ALERT
            trigger_alert(_random_ip(), 0.95)

        else:
            simulation_stats["normals"] += 1

        print("📊 STATS:", simulation_stats)

    simulation_stats["running"] = False

# ---------------- START ----------------
def start_simulation(delay_seconds=2):
    global _sim_thread

    if simulation_stats["running"]:
        return False

    _stop_event.clear()

    simulation_stats["running"] = True
    simulation_stats["processed"] = 0
    simulation_stats["attacks"] = 0
    simulation_stats["normals"] = 0

    _sim_thread = threading.Thread(
        target=_run_simulation,
        kwargs={"delay_seconds": delay_seconds},
        daemon=True
    )

    _sim_thread.start()
    return True

# ---------------- STOP ----------------
def stop_simulation():
    if not simulation_stats["running"]:
        return False

    _stop_event.set()
    return True

# ---------------- STATUS ----------------
def is_running():
    return simulation_stats.get("running", False)
