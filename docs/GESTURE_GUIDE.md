# AI Gesture Mouse - Gesture & Control Guide

This guide details all supported hand gestures, triggers, and practical tips for operating the **AI Gesture Mouse**.

---

## 🖐️ Gesture Reference Map

| Gesture Action | Hand Landmark Pose | Trigger Mechanism | Visual Cue |
| :--- | :--- | :--- | :--- |
| **Move Cursor** | **Index finger UP**, other fingers folded | Real-time tracking of landmark `8` (Index Tip) with Exponential Moving Average (EMA) smoothing | Cyan / Green crosshair dot following index finger |
| **Left Click** | **Thumb & Index finger pinch** | Euclidean distance between landmark `4` and `8` drops below pinch threshold (< 38px) | Green flash & ring indicator at cursor |
| **Right Click** | **3 Fingers UP** (Index, Middle, Ring UP; Pinky down) | Finger state `[*, 1, 1, 1, 0]` with 0.35s cooldown | Blue ring pulse & "RIGHT_CLICK" HUD badge |
| **Double Click** | **Thumb & Middle finger pinch** | Euclidean distance between landmark `4` and `12` < 38px while Index is extended | Magenta flash & "DOUBLE_CLICK" status |
| **Drag & Drop** | **Pinch & Hold** (> 0.45s) | Holding thumb and index finger together enters drag mode; release to drop | Orange box with "DRAG" status badge |
| **Scroll Up / Down** | **2 Fingers UP** (Index & Middle UP - "Peace" sign) | Vertical movement of two fingers calculates scroll delta | Yellow double-arrow indicator on HUD |
| **Idle / Neutral** | Closed fist or no fingers extended | System pauses cursor movement to prevent accidental input | Gray status dot |

---

## 🎯 Best Practices for Accurate Tracking

1. **Camera Position**:
   - Ensure your webcam is positioned directly facing your upper torso and hands.
   - Maintain a distance of 0.5 to 1.2 meters from the camera lens.

2. **Lighting Conditions**:
   - Work in a well-illuminated room. Avoid harsh backlighting (e.g. sitting with a bright window directly behind you).
   - Ensure your hand is clearly differentiated from the background.

3. **Active Interaction Zone**:
   - The HUD displays an orange active bounding box. Moving your hand within this box maps directly across your entire monitor screen without forcing your hand to reach the far edges of the camera frame.

4. **Fine-Tuning Sensitivity**:
   - Run the calibration utility:
     ```bash
     python -m src.calibration
     ```
   - Adjust the smoothing factor (`+` / `-`) to balance latency versus jitter.
  
   markdown
# ✋ AI Gesture Mouse - Comprehensive User Guide

Touchless computer interaction powered by Computer Vision and Hand Landmark Detection.

---

## 🖥️ Modern HUD Interface Overview

The on-screen Head-Up Display (HUD) provides live visual telemetry without cluttering your interaction space:

1. **Top Dashboard Panel**: Displays live operating mode, real-time FPS counter, and current smoothing dynamic.
2. **Gesture State Color Coding**:
   - 🟢 `MOVE` (Green): Index pointing, guiding mouse movement.
   - 🟡 `LEFT_CLICK` (Yellow): Pinch detected & executed.
   - 🟠 `RIGHT_CLICK` (Orange): Two-finger secondary click.
   - 🟣 `DOUBLE_CLICK` (Magenta): Rapid double pinch.
   - 🔶 `DRAG` (Deep Orange): Maintained pinch gesture to grab & move items.
   - 🔵 `SCROLL` (Cyan): Two fingers separated moving vertically.
   - ⚪ `IDLE` (White): Hand resting or low landmark confidence.
3. **Animated Click Ring**: An expanding radial indicator flashes on the index fingertip when a click triggers.
4. **Interaction Boundary**: Dashed frame margin indicating the active cursor zone.

---

## 🎯 Step-by-Step Calibration Workflow

To tailor gesture sensitivity to your hand size and camera distance:

1. Launch calibration:
   bash
   python -m src.calibration
   
2. **Set Pinch Threshold**: Pinch your index finger and thumb together, then press `[C]` to capture your personal threshold distance.
3. **Tune Smoothing**: Use `[+]` to reduce cursor jitter, or `[-]` for snappier cursor response.
4. **Save Profile**: Press `[S]` to store preferences to `config.json`.
5. Press `[Q]` or `[Esc]` to return to normal operation.


---
