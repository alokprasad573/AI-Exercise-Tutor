# 🏋️ GymGenie — AI Exercise Tutor

> Real-time pose detection with proactive AI voice coaching, powered by MediaPipe, Groq LLM, and Streamlit.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.54.0-FF4B4B?logo=streamlit&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.14-00A86B?logo=google&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA--3.3--70B-F54F29?logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## 📖 Overview

**GymGenie** is a browser-based AI personal trainer that watches your workout through your webcam in real time. Using Google's MediaPipe Pose Landmarker model, it detects 33 body keypoints per frame, analyses your exercise form, counts your reps and sets, and delivers live voice coaching cues via a Groq-powered LLM and Google Text-to-Speech.

### ✨ Key Features

| Feature | Description |
|---|---|
| **Real-Time Pose Detection** | MediaPipe Full Pose Landmarker (float16) at ≥ 0.7 confidence threshold |
| **5 Exercise Types** | Squats, Push-ups, Biceps Curls, Shoulder Press, Lunges |
| **Automatic Rep Counting** | State-machine logic (UP/DOWN) per exercise with angle thresholds |
| **Form Analysis** | Per-exercise biomechanical checks (depth, alignment, arch, swing, balance) |
| **AI Voice Coaching** | LLaMA 3.3 70B (via Groq) generates 10–15 word spoken coaching cues |
| **Proactive TTS** | gTTS converts coaching text to MP3; auto-plays in the browser |
| **Workout Planning** | Set target exercises, sets, and reps before each session |
| **History Tracking** | SQLite-backed workout log aggregated by exercise and date |
| **Multi-User Auth** | Username-based session management with automatic user creation |
| **Custom Branding** | Adobe Clean font + dark-theme CSS injected into the Streamlit UI |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A [Groq API key](https://console.groq.com/) (free tier available)
- Webcam accessible by the browser

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/AI-Exercise-Tutor.git
cd AI-Exercise-Tutor
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

> **Linux users**: Also install the system packages listed in `packages.txt` before installing Python deps:
> ```bash
> sudo apt-get install -y libgl1 libglib2.0-0t64 libsm6 libxext6
> ```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Alternatively, if deploying on **Streamlit Community Cloud**, add `GROQ_API_KEY` to your app's Secrets.

### 5. Run the App

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🗂️ Project Structure

```
AI-Exercise-Tutor/
│
├── app.py                               # Main Streamlit entry point
├── requirements.txt                     # Python dependencies
├── packages.txt                         # Linux system-level packages
├── data.db                              # SQLite workout database (auto-created)
│
├── core/
│   └── base_exercise.py                 # Abstract base class for all exercise detectors
│
├── detectors/                           # Exercise-specific pose analysis modules
│   ├── squats.py                        # SquatDetector
│   ├── pushups.py                       # PushUpDetector
│   ├── bieceps_curl.py                  # BicepsCurlDetector
│   ├── shoulder_press.py                # ShoulderPressDetector
│   └── lunges.py                        # LungesDetector
│
├── ml_models/
│   └── pose_landmarker_full.task        # MediaPipe Pose Landmarker model (~9 MB)
│
├── services/
│   ├── auth/
│   │   └── login.py                     # Username-based session login
│   ├── coaching/
│   │   ├── llm.py                       # Groq LLM client (LLaMA 3.3 70B)
│   │   ├── tts.py                       # gTTS text-to-speech wrapper
│   │   └── voice_pipeline.py            # Form-issue detection + coaching orchestration
│   ├── config/
│   │   └── workout_config.py            # Exercise options, pose connections, metrics schema, LLM prompt
│   ├── persistence/
│   │   └── exercise_repository.py       # SQLite CRUD + schema migration
│   ├── state/
│   │   └── session_defaults.py          # Streamlit session_state initialisation
│   ├── tracking/
│   │   └── metrics.py                   # Rep/set counting, DB persistence, coaching triggers
│   ├── ui/
│   │   └── style_loader.py              # CSS injection + WebRTC iframe font patching
│   └── vision/
│       └── exercise_video_processor.py  # VideoProcessorBase: landmark detection + overlay rendering
│
├── static/
│   ├── style.css                        # Global dark-theme styles
│   └── AdobeClean.otf                   # Custom font
│
└── .streamlit/
    └── config.toml                      # Streamlit dark-theme configuration
```

---

## 🏋️ Supported Exercises & Metrics

### Squats

| Metric | Description |
|---|---|
| Knee Angle | Hip → Knee → Ankle angle (dominant side by visibility) |
| Back Angle | Shoulder → Hip → Knee (forward lean check) |
| Depth Status | `GOOD DEPTH` (≤ 100°) / `TOO HIGH` / `STANDING` |

**Rep logic:** stage = `down` when knee angle < 100° → stage = `up` (rep counted) when knee angle ≥ 160°

---

### Push-ups

| Metric | Description |
|---|---|
| Elbow Angle | Shoulder → Elbow → Wrist |
| Body Alignment | `Straight` (> 160°) / `Slight Bend` (> 140°) / `Poor Form` |
| Hip Position | `LEVEL` / `SAGGING` / `PIKED UP` (± 8% midpoint tolerance) |

**Rep logic:** stage = `down` when elbow < 90° → stage = `up` (rep counted) when elbow > 160°

---

### Biceps Curls (Dumbbell)

| Metric | Description |
|---|---|
| Elbow Angle | Shoulder → Elbow → Wrist |
| Shoulder Stability | `STABLE` / `ELBOW DRIFTING` (6% lateral tolerance) |
| Swing Detection | `NO SWING` / `SWINGING` (torso atan2 angle > 15°) |

**Rep logic:** stage = `up` when elbow < 50° → stage = `down` (rep counted) when elbow > 160°

---

### Shoulder Press

| Metric | Description |
|---|---|
| Elbow Angle | Shoulder → Elbow → Wrist |
| Arm Extension | `FULL` (> 160°) / `PARTIAL` (> 140°) / `LOW` |
| Back Arch | `GOOD` / `ARCHED` (shoulder–hip atan2 > 15°) |

**Rep logic:** stage = `down` when elbow < 90° → stage = `up` (rep counted) when elbow > 150°

---

### Lunges

| Metric | Description |
|---|---|
| Front Knee Angle | Hip → Knee → Ankle (leading leg — whichever knee is more bent) |
| Torso Angle | Shoulder → Hip → Knee (upright posture check) |
| Balance Status | `BALANCED` / `OFF BALANCE` (shoulder–hip lateral offset > 10%) |

**Rep logic:** stage = `down` when front knee < 100° → stage = `up` (rep counted) when front knee > 160°

---

## 🤖 AI Coaching Pipeline

```
Per Frame (WebRTC async background thread)
   │
   ▼
MediaPipe detects 33 body landmarks
   │
   ▼
Exercise Detector processes landmarks → metrics dict
   │
   ▼
Set latest_metrics (thread-safe via threading.Lock)

Main Thread (Streamlit rerun every 250 ms)
   │
   ▼
sync_metrics_update() reads latest_metrics and evaluates:
   ├── Rep count updated in session_state
   ├── Set completed?  → save to DB, fire "set_completed" event
   ├── Workout done?   → auto-end session, fire "workout_completed" event
   ├── No pose?        → fire "no_pose_detected" event
   └── Form issue?     → fire "ongoing_form_check" event (5 s cooldown)
         │
         ▼
   VoicePipeline.process_event()
         │
         ├── _find_form_issue() → human-readable issue description
         │
         ├── LLMCoach.give_feedback(event, issue)
         │     └── Groq API: LLaMA 3.3 70B, temp=0.4, last 10 turns history
         │
         └── TextToSpeech.speak(text)
               └── gTTS → MP3 bytes → st.audio(autoplay=True) → hidden player
```

### Coaching Events

| Event | Trigger |
|---|---|
| `workout_started` | User clicks **Start Workout** |
| `set_completed` | Rep counter crosses a full set boundary |
| `workout_completed` | All target sets finished |
| `no_pose_detected` | Pose landmarks absent from frame |
| `ongoing_form_check` | Every render cycle with a detected form issue (5 s cooldown) |

---

## 🗄️ Database Schema

SQLite database (`data.db`) is auto-created on first run.

```sql
CREATE TABLE users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exercises (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    exercise_name TEXT    NOT NULL,
    reps          INTEGER NOT NULL DEFAULT 0,
    sets          INTEGER NOT NULL DEFAULT 0,
    time          INTEGER NOT NULL DEFAULT 0,   -- seconds elapsed
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

> Records are **upserted** by `(user_id, exercise_name, DATE)` — the same exercise performed on the same day accumulates into a single row.

---

## ⚙️ Configuration

### `services/config/workout_config.py`

| Constant | Purpose |
|---|---|
| `EXERCISE_OPTIONS` | List of exercises shown in the sidebar dropdown |
| `POSE_CONNECTIONS` | MediaPipe landmark index pairs used to draw the skeleton overlay |
| `METRICS_FIELDS` | Per-exercise fields and their defaults synced into `session_state` |
| `PROMPT` | System prompt defining the AI coach's persona and response style |

### `.streamlit/config.toml`

```toml
[theme]
primaryColor             = "#444"
backgroundColor          = "#0E1117"
secondaryBackgroundColor = "#1e232B"
textColor                = "#FFF"
```

---

## 🔌 Technology Stack

| Layer | Technology |
|---|---|
| **UI Framework** | [Streamlit](https://streamlit.io/) 1.54.0 |
| **Video Streaming** | [streamlit-webrtc](https://github.com/whitphx/streamlit-webrtc) 0.64.5 |
| **Pose Estimation** | [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) 0.10.14 — Pose Landmarker Full (float16) |
| **Video Processing** | [OpenCV Headless](https://pypi.org/project/opencv-python-headless/) 4.10.0 + PyAV |
| **LLM** | [Groq](https://groq.com/) API — LLaMA 3.3 70B Versatile |
| **Text-to-Speech** | [gTTS](https://gtts.readthedocs.io/) 2.5.3 (Google TTS) |
| **Database** | SQLite 3 (Python built-in `sqlite3`) |
| **Data Processing** | [Pandas](https://pandas.pydata.org/) 2.2.3 |
| **Environment Config** | [python-dotenv](https://pypi.org/project/python-dotenv/) 1.2.2 |

---

## 🌐 Deployment (Streamlit Community Cloud)

1. Push your repository to GitHub. Ensure `data.db`, `.env`, and `.streamlit/config.toml` are in `.gitignore`.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your GitHub repo.
3. Set the **main file path** to `app.py`.
4. Add your `GROQ_API_KEY` under **Advanced settings → Secrets**.
5. The `packages.txt` file is automatically detected and used to install system-level dependencies.
6. The `pose_landmarker_full.task` model is automatically downloaded on first boot if not present.

---

## 🧪 Development Notes

- The WebRTC video stream requires **HTTPS** in production or **localhost** for local development.
- Voice coaching enforces a **5-second cooldown** between form-correction cues.
- The LLM retains the **last 10 turns** of conversation history for coaching continuity.
- Pose landmarks require a minimum **visibility score of 0.7** before any metric is calculated.
- The video processor runs in an **async background thread**; metrics are safely shared via a `threading.Lock`.

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 🙏 Acknowledgements

- [Google MediaPipe](https://ai.google.dev/edge/mediapipe) — Pose Landmarker model
- [Groq](https://groq.com/) — Ultra-fast LLM inference
- [Streamlit](https://streamlit.io/) & [streamlit-webrtc](https://github.com/whitphx/streamlit-webrtc) — Browser-based real-time video pipeline
