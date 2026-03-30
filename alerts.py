"""
alerts.py
---------
Alert system — desktop toast + Telegram alert (secure)
"""

import os
import logging
import threading
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# ---------------- DESKTOP (PLYER) ----------------
try:
    from plyer import notification as _plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    _plyer_notification = None
    PLYER_AVAILABLE = False
    logger.warning("plyer not installed — desktop notifications disabled")


# ---------------- TELEGRAM CONFIG ----------------
TELEGRAM_ENABLED = True

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ---------------- DESKTOP ALERT ----------------
def send_desktop_alert(source_ip, confidence):
    if not PLYER_AVAILABLE:
        print("Desktop alert skipped — plyer not installed")
        return

    try:
        _plyer_notification.notify(
            title="⚠ Network Attack Detected!",
            message=f"IP: {source_ip}\nConfidence: {confidence*100:.1f}%",
            timeout=5
        )
        print("Desktop alert sent ✅")
    except Exception as e:
        print("Desktop alert error:", e)


# ---------------- TELEGRAM ALERT ----------------
def send_telegram_alert(source_ip, confidence):

    if not TELEGRAM_ENABLED:
        print("Telegram disabled ❌")
        return

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram config missing ❌")
        return

    message = f"""
🚨 NETWORK ATTACK DETECTED 🚨

🌐 IP: {source_ip}
📊 Confidence: {confidence*100:.2f}%
🕒 Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }

        response = requests.post(url, data=payload)

        if response.status_code == 200:
            print("✅ Telegram alert sent!")
        else:
            print("❌ Telegram error:", response.text)

    except Exception as e:
        print("❌ Telegram error:", e)


# ---------------- TRIGGER ----------------
def trigger_alert(source_ip, confidence):
    def run():
        send_desktop_alert(source_ip, confidence)
        send_telegram_alert(source_ip, confidence)

    threading.Thread(target=run, daemon=True).start()


# ---------------- TEST ----------------
if __name__ == "__main__":
    print("Testing alert system...")
    trigger_alert("192.168.1.100", 0.95)
