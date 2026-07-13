# VisionGuard AI

**Intelligent Real-Time Fire & Smoke Detection System using YOLOv8**

**HackZen 2026 — Open Challenge**

| | |
|---|---|
| **Team Name** | VisionGuard AI |
| **Team Members** | Sujan Pranav P M, Tharun S M, Pranesh P |
| **Institution** | Bannari Amman Institute of Technology |
| **Date** | 12 July 2026 |

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white">
  <img alt="YOLOv8" src="https://img.shields.io/badge/Model-YOLOv8-00FFFF?logo=yolo&logoColor=black">
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-4.5.3-5C3EE8?logo=opencv&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg">
  <img alt="Status" src="https://img.shields.io/badge/Status-Active-brightgreen">
</p>

---

## Overview

Fire and Smoke Detection is a computer-vision system that watches a live camera feed and flags fire or smoke the moment it appears. It's built around a custom-trained **YOLOv8** object detection model that classifies two categories — `fire` and `smoke` — and raises an alert when either is detected consistently over a short time window.

**Why this exists:** Traditional smoke/heat detectors rely on particles or heat reaching a physical sensor, which means there's often a delay before an alarm triggers — especially in large, open, or well-ventilated spaces (warehouses, workshops, forests, parking garages) where smoke may disperse before it reaches a sensor. A camera-based system can visually catch fire or smoke starting to form anywhere in its field of view, often earlier and over a much wider area.

**The problem it solves:** It gives any standard webcam or IP camera the ability to act as an intelligent fire watchman — continuously analyzing frames, filtering out false positives with confidence thresholds and duration checks, and notifying someone the moment a real event is confirmed.

**Real-world applications:**
- Early-warning fire monitoring for warehouses, workshops, and server rooms
- Supplementary safety monitoring for homes, garages, and small businesses
- Outdoor/forest camera monitoring for early wildfire smoke detection
- Educational and research reference for building alert-driven computer vision pipelines

---

## Features

-  **Real-Time Detection** — Runs a YOLOv8 model on a live webcam feed frame-by-frame using OpenCV.
-  **Sound Alerts** — Plays a local audio file (`alert_sound.mp3`) via Pygame the moment an event is confirmed.
-  **Email Notifications** — Automatically emails a screenshot of the detected event using Gmail SMTP.
-  **Independent Confidence Thresholds** — Fire and smoke each have their own detection confidence cutoff (fire: `>0.55`, smoke: `>0.75`) to reduce false positives, since smoke is visually harder to distinguish from background clutter.
-  **Duration-Based Confirmation** — An alert only fires after fire/smoke has been detected continuously for a set number of seconds (fire: 2s, smoke: 3s by default), avoiding one-off misdetections triggering false alarms.
-  **Automatic Screenshot Logging** — Every confirmed event saves a timestamped, annotated JPEG (with bounding boxes drawn) to the project directory.
-  **Self-Resetting Alerts** — Once detection drops below the threshold, the alert state resets so a new event can be detected and reported again.
-  **Standalone Inference Script** — A separate script (`YOLOv8.py`) lets you run the same model against static images or pre-recorded video files, outside of the live-alerting pipeline.

---

## Screenshots / Demo

>  *Add your own screenshots and demo GIFs here — none are currently included in the repository.*

| Live Detection Window | Fire Alert Screenshot | Smoke Alert Screenshot |
|---|---|---|
| `docs/demo_live.gif` | `docs/fire_detected_example.jpg` | `docs/smoke_detected_example.jpg` |

```
[ Placeholder: screen recording of YOLOv8LiveCam.py running, showing bounding boxes on a test fire/smoke source ]
```

---

## Tech Stack

| Category | Technology |
|---|---|
| **Language** | Python 3.12+ |
| **Object Detection Model** | YOLOv8 ([Ultralytics](https://github.com/ultralytics/ultralytics)) |
| **Computer Vision** | OpenCV (`opencv-python`) |
| **Audio Playback** | Pygame (`pygame.mixer`) |
| **Email Notifications** | `smtplib`, `email.message` (Python standard library) |
| **Model Storage** | Git LFS (`optimized150.pt` is tracked via LFS, see `.gitattributes`) |

---

## Project Architecture

The project follows a simple, linear detect → filter → confirm → alert pipeline:

```
┌────────────────┐     ┌───────────────┐     ┌────────────────────┐
│  Camera Feed     │ →  │  YOLOv8 Model   │ →  │  Confidence Filter    │
│ (cv2.VideoCapture)│     │ (per-frame      │     │ fire > 0.55           │
└────────────────┘     │  inference)    │     │ smoke > 0.75           │
                        └───────────────┘     └────────────┬───────┘
                                                              │
                                                              ▼
                                               ┌───────────────────────────┐
                                               │  Duration Tracker            │
                                               │  fire ≥ 2s / smoke ≥ 3s       │
                                               │  continuous detection         │
                                               └────────────┬──────────────┘
                                                              │ threshold met
                                                              ▼
                              ┌──────────────────────────────────────────────┐
                              │  Alert Pipeline                                  │
                              │  1. Save annotated, timestamped screenshot        │
                              │  2. Play alert_sound.mp3 (Pygame)                 │
                              │  3. Send email with screenshot attached (SMTP)    │
                              └──────────────────────────────────────────────┘
```

**How it works internally:**
1. `YOLOv8LiveCam.py` opens a video capture device and continuously reads frames.
2. Each frame is passed to the YOLOv8 model (`optimized150.pt`) for inference (`imgsz=640`, base `conf=0.5`).
3. Detected boxes are re-filtered in code by class-specific confidence thresholds (fire vs. smoke), since the two classes need different sensitivity to avoid false positives.
4. A running duration counter accumulates time (in seconds, assuming ~30 FPS) while a class remains detected; it resets to zero the instant detection stops.
5. Once a class's duration counter crosses its threshold **and** no alert has already been sent for that ongoing event, the script saves an annotated screenshot, plays the alert sound, and emails the screenshot.
6. The alert flag resets once detection drops below threshold again, allowing future events to trigger new alerts.
7. The annotated frame (with only the filtered, high-confidence boxes drawn) is shown live in an OpenCV window until the `d` key is pressed to exit.

---

## Folder Structure

```
Fire-and-Smoke-Detection/
├── YOLOv8LiveCam.py      # Main application: live webcam detection + alerting (email + sound)
├── YOLOv8.py              # Standalone script for running inference on a single image or video file
├── optimized150.pt        # Trained YOLOv8 model weights (Git LFS — best checkpoint from training epochs)
├── alert_sound.mp3         # Audio file played when a fire/smoke alert is triggered
├── requirements.txt        # Python dependencies (ultralytics, opencv-python, pygame)
├── LICENSE                  # MIT License
├── .gitattributes            # Configures Git LFS tracking for the .pt model file
└── README.md                  # Project documentation
```

> **Note:** `YOLOv8.py` references `test_pics/` and `test_videos/` directories for sample inputs. These folders are **not included** in the repository — you'll need to supply your own test images/videos at those paths (or update the paths in the script) before running it.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/TalhaKarakoyunlu/Fire-and-Smoke-Detection.git
cd Fire-and-Smoke-Detection

# 2. (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

>  `optimized150.pt` is tracked with **Git LFS**. Make sure you have [Git LFS](https://git-lfs.com/) installed (`git lfs install`) *before* cloning, or run `git lfs pull` afterward, otherwise you'll end up with a small pointer file instead of the actual model weights.

**requirements.txt:**
```
ultralytics==8.0.3
opencv-python==4.5.3
pygame==2.0.1
```

---

## Usage

### 1. Live webcam detection with alerts

```bash
python YOLOv8LiveCam.py
```

This opens your camera feed, runs continuous fire/smoke detection, and:
- Draws bounding boxes on-screen in real time
- Plays `alert_sound.mp3` when an event is confirmed
- Saves a timestamped screenshot (`fire_detected_<timestamp>.jpg` / `smoke_detected_<timestamp>.jpg`) to the project root
- Sends an email with the screenshot attached (see [Configuration](#configuration) to set this up)

Press **`d`** to exit the live detection loop and close the window.

### 2. Testing the model on a static image

```bash
python YOLOv8.py
```

By default this runs inference on `test_pics/mumlar2.png` and saves the annotated result via Ultralytics' built-in `save=True` output. Update the `source` path in `YOLOv8.py` to point to your own image.

### 3. Testing the model on a video file

`YOLOv8.py` also contains a commented-out block for running inference on a video file (`test_videos/smoke.mp4`) frame-by-frame with the same confidence filtering logic used in the live script. Uncomment and adjust the `source` path to use it.

---

## Model Information

| | Details |
|---|---|
| **Architecture** | YOLOv8 (Ultralytics), object detection |
| **Weights file** | `optimized150.pt` — described in code comments as "Best model selected from different epochs" |
| **Classes** | `0`: fire, `1`: smoke (inferred from `class_index` handling in the detection scripts) |
| **Input size** | 640×640 (`imgsz=640`) |
| **Base inference confidence** | `0.5` (further filtered per-class after inference) |
| **Dataset / Training details** | Not included in this repository — no training scripts, dataset, or training configuration are present. If you trained this model yourself, consider documenting the dataset source, number of epochs, and augmentation strategy here. |
| **Performance / Benchmarks** | Not available in the repository. No accuracy, mAP, precision/recall, or FPS benchmarks are included — run your own evaluation on your target hardware and data before relying on this in production. |

---

## Configuration

All configuration currently lives directly in the Python scripts. Key settings you'll likely want to change:

**Email credentials** — `YOLOv8LiveCam.py`, inside `send_email()`:
```python
your_email = "YOUR_GMAIL_HERE"
your_password = "YOUR_APP_PASSWORD_HERE"  # Use a Gmail App Password, not your main password
```
And the recipient address, passed into `send_email(...)`:
```python
send_email("YOUR_GMAIL@gmail.com", "Fire Detected!", email_body, screenshot_path)
```

**Camera source** — `YOLOv8LiveCam.py`:
```python
capture = cv2.VideoCapture(1)  # 0 = default/built-in camera, 1/2/3 = external cameras
```

**Detection duration thresholds** (how long fire/smoke must be seen before alerting):
```python
detection_threshold_fire = 2   # seconds
detection_threshold_smoke = 3  # seconds
```

**Confidence thresholds** (per-class sensitivity):
```python
if class_index == 0 and confidence > 0.55:  # fire
if class_index == 1 and confidence > 0.75:  # smoke
```

**Alert sound file**:
```python
pygame.mixer.music.load('alert_sound.mp3')
```

>  **Security note:** Credentials are currently hardcoded directly in `YOLOv8LiveCam.py`. Before committing changes or sharing your copy of this project, move these to environment variables or a `.env` file (e.g. using `python-dotenv`) instead of leaving them in source code.

---

## Results

>  *No result images, logs, or metrics are currently included in the repository. Add sample outputs here once available — for example:*

```
[ Placeholder: annotated screenshot showing a correctly boxed fire event ]
[ Placeholder: annotated screenshot showing a correctly boxed smoke event ]
[ Placeholder: console output / log snippet showing an alert being triggered ]
```

---

## Future Improvements

- Move email credentials and thresholds into a config file or environment variables instead of hardcoding them
- Add a `test_pics/` and `test_videos/` sample folder (or clear instructions for sourcing your own) so `YOLOv8.py` runs out of the box
- Support alternative/multiple notification channels (SMS, push notifications, Slack/Discord webhooks)
- Add multi-camera support for monitoring more than one feed at once
- Package the live-detection loop behind a lightweight web dashboard for remote monitoring
- Add automated evaluation scripts/metrics (precision, recall, mAP) so model performance can be tracked over time
- Containerize the app (Dockerfile) for easier, dependency-free deployment
- Add unit tests around the detection-filtering and duration-tracking logic

---

## Contributing

Contributions are welcome! If you'd like to improve this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and test them locally
4. Commit with a clear message (`git commit -m "Add: your feature"`)
5. Push to your fork and open a Pull Request

For larger changes (e.g. retraining the model, restructuring the alert pipeline), please open an issue first to discuss the approach.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2024 Talha Bahadır Karakoyunlu

---

## Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) — the object detection framework this project is built on
- [OpenCV](https://opencv.org/) — video capture and image processing
- [Pygame](https://www.pygame.org/) — alert sound playback
- Python's built-in `smtplib` / `email` libraries — email alert delivery

---

<p align="center">Built to catch fire and smoke before they get out of hand. </p>
