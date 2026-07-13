"""
Web dashboard for the Fire and Smoke Detection project.

This file does NOT modify YOLOv8LiveCam.py or YOLOv8.py. It reuses the exact
same model, confidence thresholds (fire > 0.55, smoke > 0.75) and duration
thresholds (fire 2s, smoke 3s) and exposes them through a browser dashboard
instead of an OpenCV desktop window.

Run from the project root:
    python webapp/app.py
"""

import os
import time
import threading
from collections import deque
from email.message import EmailMessage
import smtplib

import cv2
from flask import Flask, Response, jsonify, render_template, send_from_directory
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Configuration (same defaults as YOLOv8LiveCam.py, overridable via env vars
# so credentials never have to be hardcoded in this file)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
MODEL_PATH = os.path.join(BASE_DIR, "optimized150.pt")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "webapp", "static", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))

CONF_FIRE = 0.55
CONF_SMOKE = 0.75
DURATION_THRESHOLD_FIRE = 2   # seconds
DURATION_THRESHOLD_SMOKE = 3  # seconds
ASSUMED_FPS = 30

EMAIL_ENABLED = os.environ.get("ALERT_EMAIL_ENABLED", "false").lower() == "true"
EMAIL_FROM = os.environ.get("ALERT_EMAIL_FROM", "")
EMAIL_APP_PASSWORD = os.environ.get("ALERT_EMAIL_PASSWORD", "")
EMAIL_TO = os.environ.get("ALERT_EMAIL_TO", "")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Shared state, updated by the detection thread, read by the Flask routes
# ---------------------------------------------------------------------------
state_lock = threading.Lock()
state = {
    "fire_detected": False,
    "smoke_detected": False,
    "fire_duration": 0.0,
    "smoke_duration": 0.0,
    "fire_confidence": 0.0,
    "smoke_confidence": 0.0,
    "camera_connected": False,
    "last_frame_time": None,
}
alerts = deque(maxlen=50)  # newest first
latest_jpeg = {"bytes": None}


def send_email(to_email, subject, body, screenshot_path):
    if not EMAIL_ENABLED:
        print("[email] Skipped - ALERT_EMAIL_ENABLED is not 'true'.")
        return
    if not (EMAIL_FROM and EMAIL_APP_PASSWORD and to_email):
        print("[email] Skipped - missing ALERT_EMAIL_FROM / ALERT_EMAIL_PASSWORD / ALERT_EMAIL_TO.")
        return
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    with open(screenshot_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="image", subtype="jpeg",
                            filename=os.path.basename(screenshot_path))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"[email] Sent to {to_email}")
    except Exception as exc:
        print(f"[email] Failed: {exc}")


def detection_loop():
    model = YOLO(MODEL_PATH)
    capture = cv2.VideoCapture(CAMERA_INDEX)

    if not capture.isOpened():
        with state_lock:
            state["camera_connected"] = False
        print("Error: Could not open video source. Set CAMERA_INDEX env var if needed.")
        return

    with state_lock:
        state["camera_connected"] = True

    detection_duration_fire = 0.0
    detection_duration_smoke = 0.0
    alert_sent_fire = False
    alert_sent_smoke = False

    while True:
        ok, frame = capture.read()
        if not ok:
            with state_lock:
                state["camera_connected"] = False
            break

        results = model.predict(source=frame, imgsz=640, conf=0.5, verbose=False)
        detections = results[0].boxes

        fire_detected = False
        smoke_detected = False
        best_fire_conf = 0.0
        best_smoke_conf = 0.0
        filtered_boxes = []

        for box in detections:
            class_index = int(box.cls)
            confidence = float(box.conf)
            if class_index == 0 and confidence > CONF_FIRE:
                fire_detected = True
                best_fire_conf = max(best_fire_conf, confidence)
                filtered_boxes.append(box)
            elif class_index == 1 and confidence > CONF_SMOKE:
                smoke_detected = True
                best_smoke_conf = max(best_smoke_conf, confidence)
                filtered_boxes.append(box)

        detection_duration_fire = detection_duration_fire + 1 / ASSUMED_FPS if fire_detected else 0.0
        detection_duration_smoke = detection_duration_smoke + 1 / ASSUMED_FPS if smoke_detected else 0.0

        results[0].boxes = filtered_boxes
        annotated_frame = results[0].plot()

        # Fire alert
        if detection_duration_fire >= DURATION_THRESHOLD_FIRE and not alert_sent_fire:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            path = os.path.join(SCREENSHOT_DIR, f"fire_detected_{timestamp}.jpg")
            cv2.imwrite(path, annotated_frame)
            send_email(EMAIL_TO, "Fire Detected!", "Fire has been detected. See the attached screenshot.", path)
            alerts.appendleft({
                "type": "fire",
                "timestamp": timestamp,
                "image": f"/static/screenshots/{os.path.basename(path)}",
                "confidence": round(best_fire_conf, 2),
            })
            alert_sent_fire = True

        # Smoke alert
        if detection_duration_smoke >= DURATION_THRESHOLD_SMOKE and not alert_sent_smoke:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            path = os.path.join(SCREENSHOT_DIR, f"smoke_detected_{timestamp}.jpg")
            cv2.imwrite(path, annotated_frame)
            send_email(EMAIL_TO, "Smoke Detected!", "Smoke has been detected. See the attached screenshot.", path)
            alerts.appendleft({
                "type": "smoke",
                "timestamp": timestamp,
                "image": f"/static/screenshots/{os.path.basename(path)}",
                "confidence": round(best_smoke_conf, 2),
            })
            alert_sent_smoke = True

        if detection_duration_fire < DURATION_THRESHOLD_FIRE:
            alert_sent_fire = False
        if detection_duration_smoke < DURATION_THRESHOLD_SMOKE:
            alert_sent_smoke = False

        ok, buf = cv2.imencode(".jpg", annotated_frame)
        if ok:
            latest_jpeg["bytes"] = buf.tobytes()

        with state_lock:
            state.update({
                "fire_detected": fire_detected,
                "smoke_detected": smoke_detected,
                "fire_duration": round(detection_duration_fire, 2),
                "smoke_duration": round(detection_duration_smoke, 2),
                "fire_confidence": round(best_fire_conf, 2),
                "smoke_confidence": round(best_smoke_conf, 2),
                "camera_connected": True,
                "last_frame_time": time.time(),
            })

    capture.release()


def mjpeg_stream():
    while True:
        frame = latest_jpeg["bytes"]
        if frame is not None:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(1 / ASSUMED_FPS)


@app.route("/")
def index():
    return render_template(
        "index.html",
        camera_index=CAMERA_INDEX,
        conf_fire=CONF_FIRE,
        conf_smoke=CONF_SMOKE,
        dur_fire=DURATION_THRESHOLD_FIRE,
        dur_smoke=DURATION_THRESHOLD_SMOKE,
        email_enabled=EMAIL_ENABLED,
    )


@app.route("/video_feed")
def video_feed():
    return Response(mjpeg_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/status")
def api_status():
    with state_lock:
        return jsonify(dict(state))


@app.route("/api/alerts")
def api_alerts():
    return jsonify(list(alerts))


@app.route("/static/screenshots/<path:filename>")
def screenshots(filename):
    return send_from_directory(SCREENSHOT_DIR, filename)


if __name__ == "__main__":
    t = threading.Thread(target=detection_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
