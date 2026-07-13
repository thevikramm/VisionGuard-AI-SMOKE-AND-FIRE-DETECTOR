# EMBERWATCH Dashboard — Setup & Run Guide

This adds a browser dashboard on top of the existing `Fire-and-Smoke-Detection`
project. **Nothing in `YOLOv8LiveCam.py`, `YOLOv8.py`, or the model file was
changed** — the dashboard lives entirely in a new `webapp/` folder and reuses
the same thresholds (fire conf > 0.55 / 2s, smoke conf > 0.75 / 3s).

```
Fire-and-Smoke-Detection-main/
├── YOLOv8LiveCam.py        ← untouched
├── YOLOv8.py                ← untouched
├── optimized150.pt          ← untouched (still needs git lfs pull, see step 2)
├── requirements.txt          ← untouched
└── webapp/                    ← new
    ├── app.py
    ├── requirements.txt
    ├── templates/index.html
    └── static/style.css, script.js
```

## 1. Prerequisites

- Python 3.9–3.12
- A webcam (built-in or USB), or an IP camera accessible via OpenCV
- Git + [Git LFS](https://git-lfs.com/) if you're cloning the original repo fresh

## 2. Get the real model weights

The `optimized150.pt` that ships with a plain "Download ZIP" is a **Git LFS
pointer file**, not the actual ~50 MB model. If your `optimized150.pt` is only
a few hundred bytes, pull the real weights before continuing:

```bash
git lfs install
git lfs pull
```

If you don't have access to the original LFS storage, you'll need to supply
your own trained YOLOv8 weights at that same path (or point `MODEL_PATH` in
`webapp/app.py` at your own file — this only requires editing the new file,
not the originals).

## 3. Create a virtual environment

```bash
cd Fire-and-Smoke-Detection-main
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

## 4. Install dependencies

Install the original project's dependencies, plus Flask for the dashboard:

```bash
pip install -r requirements.txt
pip install -r webapp/requirements.txt
```

## 5. (Optional) Configure email alerts

Email is **off by default** in the dashboard so you're never forced to
hardcode a Gmail password. To enable it, set these environment variables
before running (get a Gmail **App Password**, not your normal password:
https://support.google.com/accounts/answer/185833):

```bash
export ALERT_EMAIL_ENABLED=true
export ALERT_EMAIL_FROM="your_gmail@gmail.com"
export ALERT_EMAIL_PASSWORD="your_16_char_app_password"
export ALERT_EMAIL_TO="recipient@example.com"
```

(Windows PowerShell: use `$env:ALERT_EMAIL_ENABLED="true"` etc.)

## 6. (Optional) Pick your camera

By default the dashboard opens camera index `0`. If your fire/smoke camera is
a different device (as the original script used index `1`), set:

```bash
export CAMERA_INDEX=1
```

## 7. Run the dashboard

```bash
python webapp/app.py
```

You should see Flask start on port 5000. Open your browser to:

```
http://localhost:5000
```

You'll see:
- A live annotated video feed (same bounding boxes/logic as `YOLOv8LiveCam.py`)
- Two "fuse" gauges — one for fire, one for smoke — that fill up as the
  persistence timer counts toward its threshold, exactly mirroring
  `detection_duration_fire` / `detection_duration_smoke` in the original script
- An event log that fills in with a thumbnail, timestamp, and confidence the
  moment an alert is confirmed
- A footer strip showing the exact thresholds currently in effect

Screenshots are saved to `webapp/static/screenshots/` (instead of the project
root, so they're servable to the browser) using the same filename pattern as
the original script: `fire_detected_<timestamp>.jpg` / `smoke_detected_<timestamp>.jpg`.

## 8. Stopping it

`Ctrl+C` in the terminal running `python webapp/app.py`. Unlike the original
script, you don't need to click into an OpenCV window and press `d` — closing
the server releases the camera.

## Notes / gotchas

- Only **one** consumer of the camera at a time — don't run
  `YOLOv8LiveCam.py` and `webapp/app.py` simultaneously, they'll fight over
  the same device index.
- If `camera_connected` stays "offline" in the dashboard, double check
  `CAMERA_INDEX` and that no other application (Zoom, Teams, etc.) is holding
  the camera.
- The dashboard uses in-memory state, so the event log resets if you restart
  the server. For persistent history, point the `alerts` list in `app.py` at
  a small database — flagged as a future improvement, not built here since it
  would mean changing behavior beyond "add a UI."
