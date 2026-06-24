# GymGenie — System Architecture

## 1. High-Level Architecture

GymGenie is a single-process Streamlit application composed of six conceptual layers. Each layer has a single, well-defined responsibility.

```mermaid
graph TD
    A["🌐 Browser (User)"]
    B["Streamlit UI Layer\napp.py"]
    C["Services Layer"]
    D["Core / Detectors Layer"]
    E["ML Model Layer\nMediaPipe Pose Landmarker"]
    F["External APIs\nGroq LLM · Google TTS"]
    G["Persistence Layer\nSQLite data.db"]

    A -->|"WebRTC video stream"| B
    A -->|"HTTP (sidebar inputs)"| B
    B --> C
    C --> D
    D --> E
    C --> F
    C --> G
```

---

## 2. Component Map

```mermaid
graph LR
    subgraph app["app.py — Entry Point"]
        MAIN["main()"]
    end

    subgraph auth["services/auth"]
        LOGIN["login_form()"]
    end

    subgraph state["services/state"]
        SESS["initial_session_defaults()"]
    end

    subgraph config["services/config"]
        CFG["workout_config.py\nEXERCISE_OPTIONS · POSE_CONNECTIONS\nMETRICS_FIELDS · PROMPT"]
    end

    subgraph vision["services/vision"]
        VP["VideoProcessorClass\nVideoProcessorBase"]
    end

    subgraph tracking["services/tracking"]
        METRICS["sync_metrics_update()"]
    end

    subgraph coaching["services/coaching"]
        PIPE["VoicePipeline"]
        LLM["LLMCoach\nGroq · LLaMA 3.3 70B"]
        TTS["TextToSpeech\ngTTS"]
    end

    subgraph persist["services/persistence"]
        REPO["exercise_repository.py\nSQLite CRUD"]
    end

    subgraph ui["services/ui"]
        STYLE["style_loader.py\nCSS · Font · WebRTC patch"]
    end

    subgraph core["core/"]
        BASE["BaseExercise ABC\ncalculate_angle() · get_point()"]
    end

    subgraph detectors["detectors/"]
        SQ["SquatDetector"]
        PU["PushUpDetector"]
        BC["BicepsCurlDetector"]
        SP["ShoulderPressDetector"]
        LU["LungesDetector"]
    end

    MAIN --> LOGIN
    MAIN --> SESS
    MAIN --> VP
    MAIN --> METRICS
    MAIN --> PIPE
    MAIN --> STYLE

    VP --> CFG
    VP --> SQ & PU & BC & SP & LU

    SQ & PU & BC & SP & LU --> BASE

    METRICS --> REPO
    METRICS --> PIPE
    METRICS --> CFG

    PIPE --> LLM
    PIPE --> TTS
    LLM --> CFG
```

---

## 3. Per-Frame Data Flow

Every frame from the user's webcam passes through this pipeline:

```mermaid
sequenceDiagram
    participant Browser
    participant WebRTC as streamlit-webrtc
    participant VPC as VideoProcessorClass.recv()
    participant MP as MediaPipe Landmarker
    participant Det as Exercise Detector
    participant CV as OpenCV Overlay
    participant ST as Streamlit Main Thread

    Browser->>WebRTC: Raw video frame (BGR24)
    WebRTC->>VPC: av.VideoFrame
    VPC->>VPC: Flip horizontally (mirror)
    VPC->>MP: mp.Image (SRGB)
    MP-->>VPC: PoseLandmarkerResult (33 landmarks)
    alt Pose detected
        VPC->>CV: _draw_skeleton() — green lines + blue dots
        VPC->>Det: detector.process(landmarks)
        Det-->>VPC: metrics dict {reps, angles, statuses}
        VPC->>CV: _draw_overlays() — status text at bottom
        VPC->>VPC: set_latest_metrics(metrics) [Lock]
    else No pose
        VPC->>CV: _draw_no_pose_warnings()
        VPC->>VPC: set pose_detected=False [Lock]
    end
    VPC-->>WebRTC: av.VideoFrame (annotated)
    WebRTC-->>Browser: Rendered video

    loop every 250 ms
        ST->>VPC: get_latest_metrics() [Lock]
        ST->>ST: sync_metrics_update()
    end
```

---

## 4. AI Coaching Event Flow

```mermaid
flowchart TD
    A["sync_metrics_update()"] --> B{New set\ncompleted?}
    B -- Yes --> C["add_exercise() → SQLite"]
    C --> D["VoicePipeline.process_event\nevent='set_completed'"]

    A --> E{Workout\ncompleted?}
    E -- Yes --> F["VoicePipeline.process_event\nevent='workout_completed'"]
    F --> G["workout_started = False"]

    A --> H{No pose\ndetected?}
    H -- Yes --> I["VoicePipeline.process_event\nevent='no_pose_detected'"]

    A --> J["VoicePipeline.process_event\nevent='ongoing_form_check'"]

    D & F & I & J --> K["_find_form_issue(exercise, metrics)"]
    K --> L{Issue\nfound?}
    L -- No, major event --> M["LLMCoach.give_feedback(event, None)"]
    L -- Yes --> M2["LLMCoach.give_feedback(event, issue_text)"]
    L -- No, minor event --> N["⏭ Skip (cooldown or no issue)"]

    M & M2 --> O["Groq API\nLLaMA 3.3 70B\ntemp=0.4\nlast 10 turns"]
    O --> P["TextToSpeech.speak(text)\ngTTS → MP3 bytes"]
    P --> Q["st.audio(autoplay=True)\nHidden HTML audio player"]
    Q --> R["st.success() — Coach text displayed"]
```

---

## 5. Threading Model

```mermaid
graph LR
    subgraph main["Main Thread (Streamlit)"]
        A["Renders UI\nevery 250 ms rerun"]
        B["sync_metrics_update()"]
        C["VoicePipeline / Groq / gTTS"]
        D["SQLite writes"]
    end

    subgraph bg["Background Thread (WebRTC / aiortc)"]
        E["VideoProcessorClass.recv()"]
        F["MediaPipe inference"]
        G["OpenCV drawing"]
    end

    LOCK["threading.Lock\n_latest_metrics"]

    E --> F --> G
    G -->|"set_latest_metrics()"| LOCK
    LOCK -->|"get_latest_metrics()"| B
    B --> C --> D
```

> **Key design decision**: All heavy ML inference (MediaPipe) runs in the WebRTC background thread. The Streamlit main thread only reads the pre-computed metrics snapshot, keeping the UI responsive.

---

## 6. Exercise Detector Design

All detectors share a common abstract base:

```mermaid
classDiagram
    class BaseExercise {
        +int reps
        +str stage
        +calculate_angle(a, b, c) float
        +get_point(landmarks, idx) tuple
        +process(landmarks)* dict
        +reset()* None
    }

    class SquatDetector {
        DOWN_THRESHOLD = 100
        UP_THRESHOLD = 160
        +process(landmarks) dict
    }

    class PushUpDetector {
        DOWN_THRESHOLD = 90
        UP_THRESHOLD = 160
        HIP_SAG_TOLERANCE = 0.08
        +process(landmarks) dict
    }

    class BicepsCurlDetector {
        UP_THRESHOLD = 50
        DOWN_THRESHOLD = 160
        ELBOW_DRIFT_TOLERANCE = 0.06
        SWING_THRESHOLD = 15
        +process(landmarks) dict
        -_safe_angle(dx, dy) float
    }

    class ShoulderPressDetector {
        DOWN_THRESHOLD = 90
        UP_THRESHOLD = 150
        +process(landmarks) dict
    }

    class LungesDetector {
        DOWN_THRESHOLD = 100
        UP_THRESHOLD = 160
        BALANCE_TOLERANCE = 0.10
        +process(landmarks) dict
    }

    BaseExercise <|-- SquatDetector
    BaseExercise <|-- PushUpDetector
    BaseExercise <|-- BicepsCurlDetector
    BaseExercise <|-- ShoulderPressDetector
    BaseExercise <|-- LungesDetector
```

### Angle Calculation

The `calculate_angle(a, b, c)` method computes the **interior angle at vertex B** using dot-product / arc-cosine:

```
cos(θ) = (BA⃗ · BC⃗) / (|BA⃗| · |BC⃗|)
θ = arccos(cos(θ))   (clamped to [-1, 1] to avoid floating-point errors)
```

### Rep-Counting State Machine (common to all detectors)

```mermaid
stateDiagram-v2
    [*] --> IDLE : stage = None
    IDLE --> DOWN : angle crosses DOWN_THRESHOLD
    DOWN --> UP : angle crosses UP_THRESHOLD
    UP --> DOWN : angle crosses DOWN_THRESHOLD again
    UP --> UP : reps += 1 on transition from DOWN
```

> **Biceps Curl** uses the inverse convention — `UP` state first (curl up), then `DOWN` (extend).

---

## 7. Persistence Layer

```mermaid
erDiagram
    users {
        INTEGER id PK
        TEXT username UK
        TIMESTAMP created_at
    }

    exercises {
        INTEGER id PK
        INTEGER user_id FK
        TEXT exercise_name
        INTEGER reps
        INTEGER sets
        INTEGER time
        TIMESTAMP created_at
    }

    users ||--o{ exercises : "has"
```

### Upsert Strategy

When a set is completed, `add_exercise()` checks if a record already exists for `(user_id, exercise_name, DATE('now'))`. If yes, it **increments** `reps`, `sets`, and `time`; otherwise it inserts a new row. This keeps one row per exercise per day per user.

### Schema Migration

`init_db()` runs a `PRAGMA table_info` check on startup and renames `duration → time` if the column exists from an older schema version.

---

## 8. Service Dependency Graph

```mermaid
graph TD
    app --> auth/login
    app --> state/session_defaults
    app --> ui/style_loader
    app --> vision/exercise_video_processor
    app --> tracking/metrics
    app --> coaching/voice_pipeline
    app --> persistence/exercise_repository

    tracking/metrics --> persistence/exercise_repository
    tracking/metrics --> config/workout_config
    tracking/metrics --> coaching/voice_pipeline

    coaching/voice_pipeline --> coaching/llm
    coaching/voice_pipeline --> coaching/tts

    coaching/llm --> config/workout_config

    vision/exercise_video_processor --> config/workout_config
    vision/exercise_video_processor --> detectors/*

    auth/login --> persistence/exercise_repository

    detectors/* --> core/base_exercise
```

---

## 9. Key Design Decisions

| Decision | Rationale |
|---|---|
| **Streamlit + streamlit-webrtc** | Enables a fully browser-based app with real-time video without a custom frontend |
| **MediaPipe Tasks API (VIDEO mode)** | Provides frame-timestamp-aware inference and more stable landmark tracking than LIVE_STREAM |
| **threading.Lock for metrics** | Prevents race conditions between the WebRTC background thread and the Streamlit main thread |
| **Groq LLaMA 3.3 70B** | Ultra-low latency LLM inference (<1 s) essential for real-time voice coaching |
| **gTTS over local TTS** | Zero model download overhead; suitable for cloud deployment with internet access |
| **SQLite (no ORM)** | Lightweight, zero-config persistence; sufficient for a single-server Streamlit deployment |
| **Per-exercise detector classes** | Open/Closed Principle — adding a new exercise only requires a new detector subclass |
| **Dominant-side selection** | Each detector picks the more visible side (left vs. right) automatically, handling any camera angle |
| **5-second coaching cooldown** | Prevents TTS audio from overlapping and the Groq API from being spammed |
| **Last-10-turns LLM history** | Provides coaching continuity while bounding token cost per request |
