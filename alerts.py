"""
alerts.py
---------
Alert system — desktop toast + Telegram alert
"""

import os
import logging
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# Try importing plyer at module level; fall back gracefully if unavailable
try:
    from plyer import notification as _plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    _plyer_notification = None
    PLYER_AVAILABLE = False
    logger.warning("plyer not installed — desktop notifications disabled")


# ---------------- TELEGRAM CONFIG ----------------
TELEGRAM_ENABLED = True

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "")


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
        print("Desktop alert sent")
    except Exception as e:
        print("Desktop alert error:", e)


# ---------------- EMAIL ALERT ----------------
def send_email_alert(source_ip, confidence):

    if not TELEGRAM_ENABLED:
        print("Telegram disabled ❌")
        return False

    if not SENDER_APP_PASSWORD:
        print("App password missing ❌")
        return False

    subject = f"🚨 Network Attack Detected: {source_ip}"
    body = f"""
    ALERT!

    IP: {source_ip}
    Confidence: {confidence*100:.2f}%
    Time: {datetime.now()}
    """

    msg = MIMEText(body)
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject

    try:
        print("EMAIL FUNCTION CALLED")
        print("SENDER:", SENDER_EMAIL)
        print("RECEIVER:", RECIPIENT_EMAIL)

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()

        print("Logging in...")
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        print("Login success ✅")

        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()

        print("Email sent successfully ✅")
        return True

    except smtplib.SMTPAuthenticationError as e:
        code = e.smtp_code
        if code == 534:
            print(
                "EMAIL AUTH ERROR (534): Gmail requires an App Password.\n"
                "  1. Enable 2-Step Verification at https://myaccount.google.com/security\n"
                "  2. Generate an App Password at https://myaccount.google.com/apppasswords\n"
                "  3. Set SENDER_APP_PASSWORD to the generated 16-character password."
            )
        elif code == 535:
            print("EMAIL AUTH ERROR (535): Incorrect App Password. Double-check the value.")
        else:
            print(f"EMAIL AUTH ERROR ({code}):", e)
        return False
    except Exception as e:
        print("EMAIL ERROR:", e)
        return False

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
