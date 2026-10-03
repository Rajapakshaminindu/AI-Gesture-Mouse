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
│     MEMBER 1: CORE AI & ENG     │   │  MEMBER 2: GESTURES & QA        │   │    MEMBER 3: UX/UI & HUD        │
│    (R.G.M.J. Rajapaksha)        │   │  (G.W.S.P. Mihirangi De Silva)  │   │      (A.P.K. Gimshan)           │
│      @Rajapakshaminindu         │   │         @Mihirangi315           │   │        @kavindugimshan          │
├─────────────────────────────────┤   ├─────────────────────────────────┤   ├─────────────────────────────────┤
│ • Action Mapping Engine         │   │ • Gesture Recognition Filters   │   │ • HUD Live Dashboard Overlay    │
│ • Custom Hotkeys & Actions      │   │ • Per-Gesture Debounce Engine   │   │ • Landmark Calibration Tool     │
│ • Adaptive Velocity Smoothing   │   │ • Directional Swipe Dynamics    │   │ • Startup Splash Screen         │
│ • Gesture Analytics Telemetry   │   │ • Confidence Threshold Gating   │   │ • Interactive Visual Feedback   │
└─────────────────────────────────┘   └─────────────────────────────────┘   └─────────────────────────────────┘
```

---

## 👤 Member 1: R.G.M.J. Rajapaksha (@Rajapakshaminindu) — Core AI Developer & AI Engineering

### 📌 Focus Area: Action Mapping, Adaptive Smoothing, Configuration & Telemetry
**Status**: 🟢 Completed & Integrated into `main`

### Assigned Tasks & Modules:
1. **Dynamic Action Mapping Engine (`src/action_mapper.py`)**:
   - Implemented configurable action mapping layer to bind recognized gestures to system actions, keyboard shortcuts (`Ctrl+C`, `Ctrl+V`, `Alt+Tab`), media controls, and custom OS triggers.
2. **Adaptive Velocity-Based Smoothing (`src/mouse_controller.py`)**:
   - Dynamic Exponential Moving Average (EMA) smoothing factor based on Instantaneous Hand Velocity. Uses high smoothing for fine precision during micro-movements and low smoothing during fast flicks.
3. **Session Analytics & Telemetry Engine (`src/analytics.py`)**:
   - Real-time logging of active gesture frequency, stroke speed, landmark confidence tracking, and session report exporter (`analytics_report.json`).
4. **Configuration Validation Engine (`src/config.py`)**:
   - Schema filtering and parameter clamping to prevent crashes from unrecognized settings.
5. **AI Engine Unit Tests (`tests/test_action_mapper.py`, `tests/test_adaptive_smoothing.py`, `tests/test_analytics.py`, `tests/test_config.py`)**:
   - Full unit test coverage for action dispatching, dynamic velocity scaling, and metrics collection.

---

## 👤 Member 2: G.W.S.P. Mihirangi De Silva (@Mihirangi315) — Gesture Recognition & QA

### 📌 Focus Area: Gesture Detection Enhancement, Debounce Logic & Test QA
**Status**: 🟢 Completed & Merged into `main` (`src/gesture_recognizer.py`, `tests/test_gesture_enhancements.py`)

### Assigned Tasks & Modules:
1. **Confidence Threshold Gating (`src/gesture_recognizer.py`)**:
   - Implemented confidence verification to suppress false positives when hand detection quality is low.
2. **Per-Gesture Debounce & Cooldown Logic (`src/gesture_recognizer.py`)**:
   - Implemented cooldown timers per gesture type to prevent rapid unintentional double triggers.
3. **Horizontal Swipe Detection (`src/gesture_recognizer.py`)**:
   - Dynamic tracking of horizontal fingertip velocity for left/right browser page swipes.
4. **Gesture Test Suite (`tests/test_gesture_enhancements.py`)**:
   - Comprehensive automated unit tests for swipe detection, debounce cooldowns, and confidence gating.

---

## 👤 Member 3: A.P.K. Gimshan (@kavindugimshan) — UX/UI, Dashboard & Calibration

### 📌 Focus Area: Live Camera HUD Overlay, Cursor Diagnostics & Calibration
**Status**: 🟢 Completed & Merged into `main` (`src/main.py`, `src/calibration.py`)

### Assigned Tasks & Modules:
1. **HUD Overlay & Live Diagnostics (`src/main.py`)**:
   - Real-time gesture state badges, active bounding box guide, cursor preview, and FPS counter.
2. **Webcam Landmark Calibration Tool (`src/calibration.py`)**:
   - Interactive pinch and scroll threshold measurement tool with visual progress bars.
3. **Startup Splash Screen (`src/main.py`)**:
   - Alpha-blended onboarding splash screen displaying instructions on startup.

---

## 🛠️ Repository Architecture & Status

- **`main`**: Single unified, authoritative production branch.
- **Test Coverage**: **28 / 28 unit tests passing (100% green)**.
- **Collaborators**: All team member commits are preserved in the git history of `main`.
