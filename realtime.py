import time
import random
import threading

_stop_event = threading.Event()

simulation_stats = {
    "running": False,
    "processed": 0,
    "attacks": 0,
    "normals": 0,
}

def _random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def _run():
    from alerts import trigger_alert

    print("🔥 SIMULATION STARTED")

    while not _stop_event.is_set():
        time.sleep(2)

        simulation_stats["processed"] += 1

        if random.random() > 0.7:
            simulation_stats["attacks"] += 1
            trigger_alert(_random_ip(), 0.95)
        else:
            simulation_stats["normals"] += 1

        print("STATS:", simulation_stats)

    simulation_stats["running"] = False

def start_simulation():
    if simulation_stats["running"]:
        return

    _stop_event.clear()

    simulation_stats["running"] = True
    simulation_stats["processed"] = 0
    simulation_stats["attacks"] = 0
    simulation_stats["normals"] = 0

    t = threading.Thread(target=_run, daemon=True)
    t.start()

def stop_simulation():
    _stop_event.set()

def is_running():
    return simulation_stats["running"]
