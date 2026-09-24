# System Architecture & Technical Design

## 📐 Architecture Overview

AI Gesture Mouse is engineered as an end-to-end, real-time computer vision pipeline written in Python. It captures input frames through an ordinary consumer webcam, processes 21 3D hand landmarks via MediaPipe, classifies discrete ergonomic gestures, and automates operating-system cursor movements and mouse clicks through PyAutoGUI.

```mermaid
graph TD
    A[Webcam Video Stream] -->|cv2.VideoCapture| B[Frame Preprocessing & Mirroring]
    B --> C[MediaPipe Hands Model]
    C -->|21 3D Coordinates| D[Landmark Extraction & Finger State]
    D --> E[Gesture Recognizer & State Machine]
    D --> F[Coordinate Interpolation & Smoothing]
    E -->|Click / Drag / Scroll Events| G[PyAutoGUI OS Event Dispatcher]
    F -->|Smoothed (X, Y) Coordinates| G
    G --> H[Host Operating System Desktop]
    E --> I[HUD Visualizer & Overlay Engine]
    B --> I
    I -->|Interactive Video Stream| J[User Display Window]
```

---

## 🧩 Core Modules

| Module | File | Role & Responsibility |
| :--- | :--- | :--- |
| **Configuration** | `src/config.py` | Centralized dataclass storing camera parameters, margin bounds, smoothing factor, distance thresholds, and JSON load/save methods. |
| **Hand Detector** | `src/hand_detector.py` | MediaPipe Hands wrapper providing landmark indexing, pixel conversion, finger extension tests, and Euclidean distance computation. |
| **Mouse Controller** | `src/mouse_controller.py` | Coordinates interpolation with Exponential Moving Average (EMA) jitter suppression, screen margin boundary clamps, and PyAutoGUI triggers. |
| **Gesture Recognizer** | `src/gesture_recognizer.py` | Multi-state machine detecting Pointing, Pinching, 3-Finger pose, Double click, Scroll and Drag with hysteresis and debounce cooldowns. |
| **Calibration Tool** | `src/calibration.py` | Interactive utility measuring rest pinch distance and tuning smoothing factor in real-time, outputting to `config.json`. |
| **Main Pipeline** | `src/main.py` | Orchestrates the video capture loop, coordinates calculations, dispatches actions, and renders real-time HUD graphics. |

---

## ⚡ Jitter Reduction & Coordinate Mapping

Raw computer vision detections often suffer from micro-tremors and frame-to-frame landmark jitter. The system uses a two-stage filter:

1. **Deadzone Filtering**:
   If the Euclidean distance between successive mapped points is below the deadzone radius ($d < \delta$), the movement is suppressed:
   $$\Delta = \sqrt{(x_t - x_{t-1})^2 + (y_t - y_{t-1})^2}$$

2. **Exponential Moving Average (EMA)**:
   For movements exceeding the deadzone, coordinates are smoothed using:
   $$x_{\text{smooth}} = x_{t-1} + \frac{x_{\text{target}} - x_{t-1}}{\alpha}$$
   where $\alpha \ge 1.0$ is the configurable smoothing factor.
