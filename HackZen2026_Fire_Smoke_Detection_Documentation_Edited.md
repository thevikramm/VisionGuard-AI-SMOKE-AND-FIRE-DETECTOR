---

#  VisionGuard AI
### *Intelligent Real-Time Fire & Smoke Detection System using YOLOv8*

**HackZen 2026 — Open Challenge**

| | |
|---|---|
| **Team Name** | **VisionGuard AI** |
| **Team Members** | **Sujan Pranav P M – Team Lead & AI Developer**<br>**Tharun S M – Computer Vision & Testing**<br>**Pranesh P – Documentation & Project Integration** |
| **Institution** | **Bannari Amman Institute of Technology** |
| **Track** | Open Challenge |
| **Base Repository** | [`TalhaKarakoyunlu/Fire-and-Smoke-Detection`](https://github.com/TalhaKarakoyunlu/Fire-and-Smoke-Detection) |
| **License** | MIT |
| **Date** | **12 July 2026** |

---

## 1. Executive Summary

This project delivers a real-time fire and smoke detection system built on the **YOLOv8** object detection architecture. A single camera feed is analyzed frame-by-frame; when the model observes fire or smoke with sufficient confidence and persistence, the system automatically captures an annotated screenshot, plays an audible alarm, and dispatches an email alert with the evidence attached — without any human watching the feed.

The engineering value of this project is not a novel detection algorithm; it is the **decision layer wrapped around a proven detector**. Raw YOLO output is noisy on a frame-by-frame basis, so the system does not fire alerts off a single detection. Instead it enforces a **temporal persistence check** (a class must be seen continuously for a set duration before it is trusted) and **class-specific confidence gating** (fire and smoke are held to different confidence bars, since smoke's diffuse visual signature is more prone to false positives than fire's characteristic color/texture). This combination is what makes the system deployable rather than a demo that cries wolf.

For the HackZen 2026 Open Challenge, **Team VisionGuard AI** built upon an open-source YOLOv8-based fire and smoke detection system by improving the overall project presentation, documentation, deployment process, and usability. The project has been organized into a clean hackathon-ready solution with enhanced documentation, simplified installation, and a professional demonstration workflow while preserving proper attribution to the original work.

---

## 2. Problem Statement

### 2.1 The Current Problem
Fire outbreaks in homes, warehouses, forests, and industrial facilities are frequently detected too late — either by smoke alarms that require the fire to reach a physical sensor, or by human observation that depends on someone being present and paying attention. By the time visible smoke reaches a ceiling-mounted ionization/photoelectric sensor, the fire may already be well established.

### 2.2 Why It Matters
- Fire damage escalates exponentially with time; the first few minutes determine whether an incident is a minor event or a catastrophic loss.
- Traditional smoke detectors are **reactive** (particulate must physically reach the sensor) rather than **visual/predictive** (a camera can see flame or smoke plumes forming before they fill a room).
- Large or open spaces (warehouses, factory floors, forested land, parking structures) are poorly served by point sensors, which have limited coverage radius, but are naturally suited to camera-based monitoring.
- Remote or unattended sites (server rooms, storage yards, rural property) benefit from automated alerting that doesn't depend on a human being present to notice and call for help.

### 2.3 Limitations of Existing Approaches
| Approach | Limitation |
|---|---|
| Ionization/photoelectric smoke alarms | Point-sensor only; must wait for smoke to physically diffuse to the unit; blind to fire that hasn't yet produced enough smoke |
| Heat detectors | Even slower to trigger than smoke detectors; needs significant ambient temperature rise |
| Human CCTV monitoring | Requires continuous attention; fatigue and blind spots are inevitable over long shifts |
| Naive frame-by-frame CV detection | Prone to false positives from single noisy frames (reflections, sunset-colored lighting, steam, dust) if not paired with a persistence/confidence strategy |

---

## 3. Objectives

1. Detect fire and smoke visually, in real time, from a standard webcam/IP camera feed — no specialized thermal or particulate hardware required.
2. Suppress false positives through confidence thresholds tuned independently per class, plus a temporal debounce so momentary noise doesn't trigger an alert.
3. Notify a human immediately and remotely (email) the moment a real event is confirmed, with visual evidence (screenshot) attached, so the recipient doesn't have to take the system's word for it.
4. Keep the alerting pipeline lightweight enough to run on commodity hardware (a laptop/edge box), rather than requiring cloud GPU infrastructure for inference.
5. Develop a reliable, easy-to-deploy computer vision solution that demonstrates the practical application of AI for real-time fire safety monitoring during the HackZen 2026 Open Challenge.

---

## 4. Proposed Solution

The system pairs a YOLOv8 object detector — trained to recognize two classes, **fire** and **smoke** — with an application-layer alerting state machine written in Python. The detector alone only answers "what do I see in this frame?" On top of that, the system tracks *how long* a class has been continuously observed, and only escalates to a human once that duration crosses a class-specific threshold (fire: 2 continuous seconds above 0.55 confidence; smoke: 3 continuous seconds above 0.75 confidence). Once escalated, the system performs three parallel actions: it saves a timestamped, annotated screenshot to disk; it plays a local audio alarm via `pygame`; and it emails the screenshot to a configured recipient via Gmail SMTP. An `alert_sent` flag per class prevents the same continuous event from re-triggering the alert on every subsequent frame, while still allowing a *new* event (after the detection lapses and reappears) to trigger a fresh alert.

---

## 5. Features

- **Real-Time Detection** — Inference runs directly on live webcam frames (`cv2.VideoCapture`) using a YOLOv8 model (`model.predict(source=frame, imgsz=640, conf=0.5)`), with results rendered back onto the video window every frame.
- **Class-Specific Confidence Gating** — Rather than a single global confidence threshold, fire (class index `0`) requires confidence `> 0.55` and smoke (class index `1`) requires confidence `> 0.75`. Smoke is held to a stricter bar because its diffuse, low-texture appearance is inherently more ambiguous (fog, steam, dust, and shadows can resemble it) than fire's more distinctive color and flicker signature.
- **Temporal Persistence Filtering** — Detection duration counters (`detection_duration_fire`, `detection_duration_smoke`) accumulate by `1/30` second per qualifying frame (an assumed 30 FPS capture rate) and reset to zero the instant the class is absent from a frame. An alert only fires once the running duration crosses the configured threshold (2s for fire, 3s for smoke), which filters out one-off misclassifications and flicker artifacts.
- **Automated Screenshot Logging** — On a confirmed event, the current frame — with only the confidence-filtered bounding boxes drawn — is saved to disk as `fire_detected_<timestamp>.jpg` or `smoke_detected_<timestamp>.jpg`, giving a permanent, timestamped audit trail of every alert.
- **Email Alerts with Evidence Attached** — Using Python's built-in `smtplib` and `email.message.EmailMessage`, the system connects to Gmail over `SMTP_SSL` (port 465) and sends the screenshot as an attachment, so the recipient sees the actual detection, not just a text notification.
- **Local Audible Alarm** — `pygame.mixer` loads and plays `alert_sound.mp3` the moment an event is confirmed, useful for on-site personnel who may not have immediate access to email.
- **One-Shot-Per-Event Alerting** — The `alert_sent_fire` / `alert_sent_smoke` boolean flags stop the system from spamming an email/sound alert every single frame while a fire continues to burn in view; the alert resets only once the detection duration drops back below threshold (i.e., the event visually ends), so a genuinely new event still gets its own alert.
- **Configurable Sensitivity** — Confidence thresholds and duration thresholds are plain variables at the top of the detection loop, making it straightforward to re-tune sensitivity for a specific camera placement or lighting environment without touching the detection logic itself.
- **Standalone Test Harness** (`YOLOv8.py`) — A separate, simpler script for running the same model against a static image or a recorded video file, useful for validating a model checkpoint before deploying it to the live camera pipeline.

---

## 6. System Architecture

The current implementation is a **single-process, single-threaded pipeline** — everything described below executes sequentially inside one Python script (`YOLOv8LiveCam.py`), rather than as separate networked services. The "modules" below are logical stages within that one process, not independently deployed components. This is stated plainly rather than dressed up as a microservice architecture it is not, because that distinction matters for anyone evaluating scalability.

```
┌────────────────────┐
│   Camera Source     │   cv2.VideoCapture(index)
│  (webcam / USB cam) │
└─────────┬──────────┘
          │ raw frame (BGR)
          ▼
┌────────────────────┐
│  YOLOv8 Inference    │   model.predict(frame, imgsz=640, conf=0.5)
│   (Ultralytics)       │
└─────────┬──────────┘
          │ Results.boxes (cls, conf, xyxy)
          ▼
┌─────────────────────────────┐
│  Confidence Gating Layer      │   fire: cls==0 & conf>0.55
│  (per-class thresholds)        │   smoke: cls==1 & conf>0.75
└─────────┬───────────────────┘
          │ boolean: fire_detected / smoke_detected
          ▼
┌─────────────────────────────┐
│  Temporal Debounce Layer       │   duration += 1/30s while detected
│  (persistence tracking)          │   duration = 0 the instant it's absent
└─────────┬───────────────────┘
          │ duration ≥ threshold?
          ▼
┌─────────────────────────────┐        ┌──────────────────────┐
│   Alert Dispatcher              │──────▶│ Screenshot Writer      │  cv2.imwrite(...)
│  (fires once per event)          │      └──────────────────────┘
│                                        │──────▶┌──────────────────────┐
│                                        │       │ Audio Alarm (pygame)  │
│                                        │      └──────────────────────┘
│                                        │──────▶┌──────────────────────┐
│                                                │ Email (smtplib/SSL)   │
│                                                └──────────────────────┘
└─────────────────────────────┘
          │
          ▼
┌────────────────────┐
│  Live Display Window │   cv2.imshow(...) — annotated frame
└────────────────────┘
```

**Communication between stages** is entirely in-process function calls and shared local variables inside a single `while True` loop — there is no message queue, REST API, or database. `results[0].boxes` is mutated in place with the filtered box list so that the same filtered detections are used both for the alert screenshot and for the live on-screen annotation, ensuring what the operator sees on screen matches exactly what triggered any alert.

---

## 7. Workflow — Step by Step

1. **Initialization**: `pygame.mixer.init()` prepares audio playback; the YOLOv8 model is loaded once from `optimized150.pt`; the camera capture device is opened via `cv2.VideoCapture(index)`. If the camera fails to open, the script exits immediately with an error message.
2. **Frame Acquisition**: Inside the main loop, one frame is read from the capture device per iteration.
3. **Inference**: The frame is passed to `model.predict()` at a fixed input resolution of 640×640 with a base confidence filter of 0.5 (Ultralytics' own threshold — this is *before* the stricter application-level gating described below).
4. **Per-Detection Classification**: Every returned box is inspected — its class index and confidence are compared against the class-specific thresholds (fire > 0.55, smoke > 0.75). Boxes that pass are collected into `filtered_boxes`; boxes that don't are effectively discarded from anything the user sees or that can trigger an alert.
5. **Duration Accumulation**: If any qualifying fire box was found this frame, `detection_duration_fire` increases by `1/30` second; otherwise it resets to `0`. The same logic runs independently for smoke.
6. **Threshold Check & Alert**: Once `detection_duration_fire ≥ 2` (or smoke ≥ 3) **and** that class's alert hasn't already fired for the current continuous event, the system: draws only the filtered boxes onto the frame, writes it to disk as a timestamped JPEG, plays the alarm sound, and sends the alert email with the screenshot attached. The corresponding `alert_sent_*` flag is set to `True` so the same ongoing event doesn't re-alert every subsequent frame.
7. **Flag Reset**: The moment a class's duration drops back under its threshold (i.e., the detection lapses), its `alert_sent_*` flag resets to `False`, arming the system for the *next* event.
8. **Display**: The annotated frame (filtered boxes only) is shown in an OpenCV window titled `YOLOv8 Webcam`.
9. **Exit Condition**: The loop breaks if the `d` key is pressed or if a frame fails to read; on exit, the capture device is released and all OpenCV windows are destroyed.

---

## 8. Technology Stack

| Category | Choice | Notes |
|---|---|---|
| Programming Language | Python 3.12+ | Per repository README |
| Object Detection Framework | Ultralytics YOLOv8 | Pinned to `ultralytics==8.0.3` in `requirements.txt` |
| Computer Vision / Video I/O | OpenCV (`opencv-python==4.5.3`) | Frame capture, drawing, display, JPEG writing |
| Audio Alerting | Pygame (`pygame==2.0.1`) | `pygame.mixer` used solely for MP3 playback |
| Email Delivery | `smtplib` + `email.message.EmailMessage` (Python standard library) | Gmail SMTP over SSL, port 465 |
| Model Weights | `optimized150.pt` | Custom-trained YOLOv8 checkpoint; distributed via Git LFS in the upstream repo |
| Version Control / LFS | Git, Git LFS | `.gitattributes` designates the `.pt` file for LFS tracking |
| License | MIT | Author: Talha Bahadir Karakoyunlu (2024) |

> ⚠️ **Version currency note:** `ultralytics==8.0.3` and `opencv-python==4.5.3` are quite old pins relative to 2026. If this stack is reused as-is, verify these versions still install cleanly and consider testing against a current Ultralytics release, noting any breaking API changes in the `Results` object if you upgrade.

---

## 9. Dataset

> ⚠️ **INFO NEEDED — this entire section is not derivable from the repository.** The archive contains no dataset folder, no `data.yaml`, no annotation files, and no training notebook/script. Only the following can be *inferred*, not confirmed, from the inference code:
> - The model outputs exactly two classes, indexed `0` and `1`, which the application code treats as **fire** and **smoke** respectively.
> - The model was trained/exported to run at a `640×640` input resolution (matching the `imgsz=640` used at inference).
>
> Please supply the following so this section can be completed accurately rather than guessed:

| Field | Required Input |
|---|---|
| Source | `[e.g. Roboflow Universe "Fire and Smoke Detection" dataset, custom-collected + labeled images, D-Fire dataset, etc.]` |
| Number of images | `[total count, and per-class if imbalanced]` |
| Classes | `[confirm: Fire, Smoke — plus any background/negative class]` |
| Preprocessing | `[resizing, augmentation — flips/rotation/mosaic/HSV jitter, letterboxing, etc.]` |
| Data split | `[train/val/test ratio, e.g. 80/10/10]` |
| Annotation format | `[YOLO txt, COCO JSON, etc., and annotation tool used]` |

---

## 10. Model Architecture

- **Base Architecture**: YOLOv8 (Ultralytics implementation). `[INFO NEEDED: confirm exact scale — n/s/m/l/x — since this affects parameter count, speed, and accuracy tradeoffs. The checkpoint filename "optimized150" is not sufficient evidence of scale on its own.]`
- **Why YOLOv8**: YOLO's single-stage, single-pass detection design is well suited to this use case because the system needs low end-to-end latency on a live video stream rather than maximum possible accuracy at the cost of multi-stage processing. Ultralytics' YOLOv8 in particular offers a mature Python API (`ultralytics.YOLO`) that made the `model.predict()` integration in this codebase straightforward, along with built-in result objects (`.boxes`, `.plot()`) that the alerting logic depends on directly.
- **Checkpoint Naming**: The filename `optimized150.pt` and the code comment `# Best model selected from different epochs` suggest this checkpoint was chosen from a sweep of training runs/epochs (plausibly around epoch 150) as the best-performing snapshot — but the actual training run, validation curves, and selection criteria are not included in this archive and should be documented from your training logs.
- **Training Methodology**: `[INFO NEEDED: transfer learning from a pretrained COCO checkpoint? trained from scratch? number of epochs, batch size, image augmentation strategy, hardware used (GPU model), training framework command, e.g. `yolo detect train data=... model=yolov8n.pt epochs=150 imgsz=640`]`
- **Hyperparameters**: `[INFO NEEDED: learning rate/schedule, optimizer, batch size, image size during training, augmentation settings]`
- **Inference Pipeline** (this part *is* confirmed from code):
  1. `YOLO("optimized150.pt")` loads the checkpoint once at startup.
  2. Each captured frame is passed directly to `model.predict(source=frame, imgsz=640, conf=0.5, show=False)` — note this is an in-memory frame array, not a file path, so no disk I/O is incurred per frame for inference input.
  3. The returned `Results` object's `.boxes` are iterated in Python to apply the stricter, class-specific confidence gates described in Section 6/7 (this is an *application-level* second filter layered on top of Ultralytics' own `conf=0.5` cutoff — it is not part of the model itself).
  4. `results[0].plot()` renders the (filtered) boxes onto the frame for both the live display and any saved alert screenshot.

---

## 11. Installation Guide

```bash
# 1. Clone the repository
git clone https://github.com/TalhaKarakoyunlu/Fire-and-Smoke-Detection.git
cd Fire-and-Smoke-Detection

# 2. (Recommended) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Ensure the model weights are pulled via Git LFS
git lfs install
git lfs pull
# optimized150.pt should now be ~49.6 MB, not a small text pointer file

# 5. Configure email alerting
# Open YOLOv8LiveCam.py and replace:
#   your_email = "YOUR_GMAIL_HERE"
#   your_password = "YOUR_APP_PASSWORD_HERE"
# Use a Gmail App Password (not your main account password) —
# see: https://support.google.com/accounts/answer/185833

# 6. Confirm alert_sound.mp3 is present in the project root
#    (swap in your own .mp3 if you'd like a different alert tone)
```

> ⚠️ Never commit real Gmail credentials to source control. Use environment variables or a `.env` file (excluded via `.gitignore`) instead of hardcoding them in the script, especially for a public hackathon submission repo. `[INFO NEEDED: confirm whether your fork has already moved credentials to environment variables — if so, document that as an improvement in Section 17.]`

---

## 12. Project Structure

```
Fire-and-Smoke-Detection/
├── YOLOv8.py            # Standalone test harness: run the model against a
│                         # single static image (active) or a video file
│                         # (commented-out block) to sanity-check a checkpoint
│                         # before deploying it to the live pipeline.
├── YOLOv8LiveCam.py      # The core product: opens a webcam feed, runs live
│                         # YOLOv8 inference, applies confidence + temporal
│                         # gating, and dispatches sound + email alerts.
├── optimized150.pt       # Trained YOLOv8 checkpoint (Git LFS object,
│                         # ~49.6 MB actual size; a small pointer file in
│                         # the raw zip export).
├── alert_sound.mp3       # Audio file played on confirmed detection.
├── requirements.txt      # Pinned dependencies: ultralytics==8.0.3,
│                         # opencv-python==4.5.3, pygame==2.0.1.
├── .gitattributes        # Marks optimized150.pt for Git LFS tracking.
├── LICENSE               # MIT License (Talha Bahadir Karakoyunlu, 2024).
└── README.md             # Original project usage documentation.
```

> `[INFO NEEDED: if your team added new files/folders — e.g. a `dataset/`, `train.py`, `dashboard/`, `Dockerfile`, `.env.example` — list and describe each addition here.]`

---

## 13. Usage Guide

**Run live detection:**
```bash
python YOLOv8LiveCam.py
```
- Point the camera at the scene to monitor. If the wrong camera opens or none opens at all, change the device index in the script:
  ```python
  capture = cv2.VideoCapture(0)   # try 0, 1, 2... depending on your system
  ```
- Fire is flagged after ≥2 continuous seconds above 0.55 confidence; smoke after ≥3 continuous seconds above 0.75 confidence.
- Press `d` with the video window focused, or `Ctrl+C` in the terminal, to stop.

**Test the model on a single image:**
```bash
python YOLOv8.py
# by default predicts on test_pics/mumlar2.png and saves the annotated result
```
> Note: `test_pics/mumlar2.png` is referenced by the script but is **not included** in this archive — you will need to supply your own test image at that path, or edit the `source=` argument to point elsewhere. `[INFO NEEDED: confirm sample test images/videos your team is using and add them to the repo, or update the path.]`

**Tune sensitivity** by editing the constants at the top of `YOLOv8LiveCam.py`:
```python
detection_threshold_fire = 2    # seconds fire must persist before alerting
detection_threshold_smoke = 3   # seconds smoke must persist before alerting
# and inside the loop:
if class_index == 0 and confidence > 0.55:   # fire confidence gate
if class_index == 1 and confidence > 0.75:   # smoke confidence gate
```

---

## 14. Results

> ⚠️ **INFO NEEDED — no metrics artifacts (results.csv, confusion matrix, PR curves) or screenshots are present in this archive.** Please provide the following from your training run and live testing so this section reflects real, reportable numbers rather than placeholders:

| Metric | Value |
|---|---|
| Precision | `[INFO NEEDED]` |
| Recall | `[INFO NEEDED]` |
| F1 Score | `[INFO NEEDED]` |
| mAP@0.5 | `[INFO NEEDED]` |
| Inference speed (FPS / ms per frame) | `[INFO NEEDED — and specify the hardware it was measured on, e.g. CPU model or GPU]` |
| Test hardware | `[INFO NEEDED]` |

**Screenshots to include once available:**
- A live detection frame with a fire bounding box and confidence score visible.
- A live detection frame with a smoke bounding box and confidence score visible.
- The received email alert (subject line + attached screenshot).
- A terminal log snippet showing the "screenshot saved and alert triggered" console output.
- (Optional) A confusion matrix or PR curve exported from your training run, if you retrained/fine-tuned the model.

`[INFO NEEDED: attach actual screenshots here — I can embed them directly into this Markdown once provided, e.g. `![Fire detection example](screenshots/fire_example.jpg)`]`

---

## 15. Challenges Faced

`[INFO NEEDED — this section should reflect your team's actual experience. Some genuine technical challenges visible from the code that you may want to speak to, if they matched your experience:]`
- Balancing confidence thresholds per class so that smoke (visually ambiguous vs. fog/dust/steam) doesn't produce excessive false positives while still catching genuine smoke early.
- The duration counters assume a fixed ~30 FPS capture rate (`1/30` increment per frame); on hardware where the actual camera FPS differs, the real-world alert delay drifts from the intended 2s/3s — worth mentioning if you encountered or corrected this.
- Git LFS handling for the model weights when cloning/forking the repository for the hackathon submission (the archive you get from a plain "Download ZIP" contains LFS pointer files, not the real weights, which can be confusing on first setup).
- `[Add: labeling effort, class imbalance, lighting condition variance, hardware constraints, camera compatibility issues, SMTP/Gmail delivery hiccups, etc.]`

---

## 16. Improvements Made *(Compared to the Original Repository)*

> ⚠️ **This is the most important section for judging integrity, and it currently cannot be completed honestly — the code in this archive is, file-for-file, the unmodified upstream `Fire-and-Smoke-Detection` repository (confirmed by direct comparison of the README, both scripts, `requirements.txt`, and `LICENSE`).** Please specify exactly what your team changed, so this section documents *your* contribution rather than the original author's baseline. Examples of the kind of detail this section needs:

| Area | Original Repo | Your Modification |
|---|---|---|
| Dataset | `[unknown — see Sec. 9]` | `[e.g. expanded with N additional labeled images / new environment conditions]` |
| Model | `optimized150.pt`, checkpoint selection method unknown | `[e.g. retrained with X epochs, switched to yolov8s, improved mAP from X% to Y%]` |
| Alerting | Gmail SMTP hardcoded credentials, single recipient | `[e.g. moved credentials to environment variables, added multi-recipient support, added SMS/Telegram alerting]` |
| Detection logic | Fixed 30 FPS assumption for duration tracking | `[e.g. replaced with wall-clock `time.time()` deltas for FPS-independent timing]` |
| Interface | OpenCV window only | `[e.g. added a web dashboard, added a REST API, added logging to a database]` |
| Deployment | Local script | `[e.g. containerized with Docker, deployed to an edge device, added a config file]` |
| Robustness | No retry/error handling around email/camera failures | `[e.g. added reconnection logic, added try/except around SMTP calls]` |

Please fill this table in with your team's actual changes — it is the section that most directly demonstrates original engineering work for the Open Challenge.

---

## 17. Future Scope

- Replace the fixed `1/30`-second-per-frame duration assumption with wall-clock timestamp deltas, making the persistence check accurate regardless of actual camera FPS.
- Move Gmail credentials out of source code and into environment variables or a secrets manager.
- Add support for multiple simultaneous camera feeds/zones with per-zone alert routing.
- Add a lightweight web dashboard for remote monitoring, alert history, and live stream viewing, instead of a local OpenCV window only.
- Expand notification channels beyond email (SMS, push notification, Telegram/Slack webhook) for faster human response.
- Introduce automatic retry/backoff for transient SMTP or camera-read failures rather than silently continuing or exiting.
- Evaluate a smaller/quantized YOLOv8 export (ONNX/TensorRT) for deployment on constrained edge hardware (e.g., Raspberry Pi, Jetson Nano).
- `[INFO NEEDED: any roadmap items specific to your team's vision for this project]`

---

## 18. References

1. Ultralytics YOLOv8 — official documentation and repository: https://docs.ultralytics.com/
2. OpenCV — Open Source Computer Vision Library: https://opencv.org/
3. Pygame — Python game/multimedia library (`pygame.mixer`): https://www.pygame.org/
4. Python Standard Library — `smtplib`, `email.message`: https://docs.python.org/3/library/smtplib.html
5. Base repository — Talha Bahadir Karakoyunlu, *Fire and Smoke Detection*: https://github.com/TalhaKarakoyunlu/Fire-and-Smoke-Detection
6. Git LFS — Large File Storage: https://git-lfs.github.com/
7. Gmail SMTP / App Passwords setup: https://support.google.com/accounts/answer/185833
8. `[INFO NEEDED: dataset source citation — see Section 9]`
9. `[INFO NEEDED: any paper or blog post that informed your specific threshold/tuning choices, if applicable]`

---

## 19. Conclusion

This project takes a well-understood building block — YOLOv8 object detection — and applies it correctly to a problem where the interesting engineering is in the layer *around* the model rather than the model itself: per-class confidence calibration, temporal persistence filtering to reject noise, and a multi-channel human alerting path (visual, audible, and remote) that fires exactly once per real event. The result is a small, understandable, and honestly-scoped system: a single-camera, single-process pipeline that is good at doing one thing — telling a human, fast and reliably, that a fire or smoke event is genuinely happening.

**Team VisionGuard AI successfully developed and presented a practical AI-powered fire and smoke detection system for the HackZen 2026 Open Challenge. The project demonstrates how modern computer vision can be applied to improve early hazard detection, reduce response time, and enhance public safety through an accessible, real-time monitoring solution.**

---

## 20. Appendix

### A. Full `requirements.txt`
```
ultralytics==8.0.3
opencv-python==4.5.3
pygame==2.0.1
```

### B. Key Tunable Constants (from `YOLOv8LiveCam.py`)
```python
detection_threshold_fire = 2      # seconds
detection_threshold_smoke = 3     # seconds
# confidence gates (inline in the detection loop):
#   fire:  class_index == 0 and confidence > 0.55
#   smoke: class_index == 1 and confidence > 0.75
# base Ultralytics confidence filter: conf=0.5
# inference resolution: imgsz=640
```

### C. Model File Verification
The `optimized150.pt` file in this archive is a Git LFS pointer, not the binary weights:
```
version https://git-lfs.github.com/spec/v1
oid sha256:cbe5840f952adab362689edc00197a85ec7543841c9db5d91d3a09ace01c5e64
size 52026763
```
Run `git lfs pull` after cloning to retrieve the actual ~49.6 MB checkpoint before attempting inference.

---

### 📋 Summary — Information Needed to Finalize This Document

To turn this from a technically accurate draft into a complete hackathon submission, please provide:

1. Team name, member names/roles, institution, submission date (Cover Page)
2. Dataset source, image counts, class distribution, preprocessing, split ratios (Section 9)
3. Model scale (n/s/m/l/x), training methodology, hyperparameters (Section 10)
4. Actual precision/recall/F1/mAP/inference-speed numbers and test hardware (Section 14)
5. Real screenshots — detection frames, email alert, terminal logs (Section 14)
6. **A precise list of what your team changed vs. the original upstream repo** (Section 16 — currently the code matches upstream file-for-file)
7. Genuine challenges your team hit during the hackathon (Section 15)

Once you send these, I can drop them directly into this file (or regenerate a finalized version) without touching anything else.
