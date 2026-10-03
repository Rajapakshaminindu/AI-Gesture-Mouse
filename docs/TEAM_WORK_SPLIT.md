# 👥 Team Work Distribution & Task Split

This document outlines the division of development tasks for **AI Gesture Mouse** (HackX 11.0 / IntelliCon '26 Project) across three core team members/collaborators.

---

## 🎯 Overview & Architectural Responsibility Split

```
                              ┌─────────────────────────────────────────┐
                              │           AI GESTURE MOUSE              │
                              └─────────────────────────────────────────┘
                                                   │
         ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
         │                                         │                                         │
         ▼                                         ▼                                         ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│     MEMBER 1: CORE AI & ENG     │   │     MEMBER 2: SYSTEM & QA       │   │    MEMBER 3: UX/UI & KIOSK     │
│    (R.G.M.J. Rajapaksha)        │   │    (T.W. Dulana Chathurma)      │   │   (G.W.S.P. Mihirangi De Silva) │
├─────────────────────────────────┤   ├─────────────────────────────────┤   ├─────────────────────────────────┤
│ • Advanced Gesture Engine       │   │ • Multi-Monitor Geometry        │   │ • Control Panel GUI Dashboard   │
│ • Custom Keybinding & Actions   │   │ • Performance Benchmarking Tool │   │ • Cyberpunk/Clean HUD Themes    │
│ • Adaptive Velocity Smoothing   │   │ • Automated QA & Test Runner    │   │ • Smart Presentation Laser Mode │
│ • Gesture Analytics Telemetry   │   │ • System Tray Daemon            │   │ • Touchless Kiosk Security Lock │
└─────────────────────────────────┘   └─────────────────────────────────┘   └─────────────────────────────────┘
```

---

## 👤 Member 1: R.G.M.J. Rajapaksha (Core AI Developer & AI Engineering) — *[IMPLEMENTED]*

### 📌 Focus Area: AI Landmark Analytics, Custom Gesture Actions, Adaptive Smoothing & Telemetry
**Status**: 🟢 Completed & Integrated into `main`

### Assigned Tasks & Modules:
1. **Dynamic Action Mapping Engine (`src/action_mapper.py`)**:
   - Implemented configurable action mapping layer to bind recognized gestures to system actions, keyboard shortcuts (`Ctrl+C`, `Ctrl+V`, `Alt+Tab`), media controls, and custom OS triggers.
2. **Advanced Gesture Recognition Extensions (`src/gesture_recognizer.py`)**:
   - Expanded gesture vocabulary: `PALM_STOP` (Safety Pause), `SWIPE_LEFT` / `SWIPE_RIGHT` (Page navigation), and `ZOOM_IN` / `ZOOM_OUT` (Pinch distance expansion).
3. **Adaptive Velocity-Based Smoothing (`src/mouse_controller.py`)**:
   - Dynamic Exponential Moving Average (EMA) smoothing factor based on Instantaneous Hand Velocity. Uses high smoothing for fine precision during micro-movements and low smoothing during fast flicks.
4. **Session Analytics & Telemetry Engine (`src/analytics.py`)**:
   - Real-time logging of active gesture frequency, stroke speed, landmark confidence tracking, and session report exporter (`analytics_report.json`).
5. **AI Engine Unit Tests (`tests/test_action_mapper.py`, `tests/test_adaptive_smoothing.py`, `tests/test_analytics.py`)**:
   - Full unit test coverage for action dispatching, dynamic velocity scaling, and metrics collection.

---

## 👤 Member 2: T.W. Dulana Chathurma (System Design, Performance Optimization & QA)

### 📌 Focus Area: Gesture Confidence & Debounce QA, Multi-Monitor Geometry & Benchmarks
**Status**: 🟢 Core gesture validation tests integrated into `main` (`tests/test_gesture_enhancements.py`)

### Assigned Tasks & Modules:
1. **Gesture Filtering & Debouncing QA (`tests/test_gesture_enhancements.py`)**:
   - Automated test suite verifying per-gesture debounce intervals, confidence thresholds, and directional swipe dynamics.
2. **Configuration Validation & Robust JSON Loading (`src/config.py`)**:
   - Schema filtering and parameter clamping to prevent crashes from unrecognised settings.
3. **Multi-Monitor Screen Mapping (`src/screen_manager.py`)**:
   - Multi-display coordinate bounds resolver for multi-monitor desktop workspaces.

---

## 👤 Member 3: G.W.S.P. Mihirangi De Silva / A.P.K. Gimshan (UX/UI, HUD Dashboard & Presentation Mode)

### 📌 Focus Area: Live Camera HUD Overlay, Cursor Diagnostics & Calibration
**Status**: 🟢 Integrated into `main` (`src/main.py`, `src/calibration.py`)

### Assigned Tasks & Modules:
1. **HUD Overlay & Live Diagnostics (`src/main.py`)**:
   - Real-time gesture state badges, active bounding box guide, cursor preview, and FPS counter.
2. **Webcam Landmark Calibration Tool (`src/calibration.py`)**:
   - Interactive pinch and scroll threshold measurement tool with visual progress bars.

---

## 🛠️ Git Workflow & Repository Health

- **`main`**: Single unified, clean, tested production branch.
- Automated test coverage passes with **100% green status** across all test suites.
