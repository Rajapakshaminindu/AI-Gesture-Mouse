# 📖 AI Gesture Mouse — Complete User Guide

Welcome to **AI Gesture Mouse**, a touchless, AI-powered computer navigation system that transforms your standard webcam into a high-precision, natural gesture controller.

---

## ⚡ Quick Start: How to Run

### Step 1: Open Terminal
Open **PowerShell** or **Command Prompt** in the project folder:
```powershell
cd AI-Gesture-Mouse
```

### Step 2: Run the Application
Use your virtual environment Python to launch:

```powershell
# Using default built-in laptop camera:
.venv\Scripts\python src/main.py

# Using an external / USB webcam (camera #1):
.venv\Scripts\python src/main.py --camera 1
```

> **Tip:** The webcam preview window will appear pinned in the bottom-right corner of your screen. It automatically floats on top of other apps (browsers, PDF readers, documents) so you can always see your gesture feedback!

---

## 🖐️ Hand Gesture Controls & Actions

| Action | Hand Gesture | How to Perform |
| :--- | :--- | :--- |
| **Move Pointer** | ☝️ **Point with Index Finger** | Extend **only your Index finger**. Move your hand to guide the cursor smoothly across the entire screen. |
| **Left Click** | 👆 **Tap Index Finger Down** | While pointing, simply **bend/tap your index finger tip down briefly** (like clicking a real mouse button) and release. |
| **Drag & Drop** | ✊ **Hold Index Finger Bent** | Keep your **Index finger bent down for 0.4+ seconds**. Move your hand to drag items/windows, then straighten your finger to drop. |
| **Scroll Up / Down** | ✌️ **Two Fingers Up** (Index + Middle) | Hold up your **Index and Middle fingers** (like 2-finger laptop trackpad):<br>• **Glide Up:** Hold fingers slightly above starting position.<br>• **Glide Down:** Hold fingers slightly below starting position.<br>• **Flick:** Move hand up or down for fast scrolling. |
| **Right Click** | 🖐️ **Open Palm (Front of Hand)** | Show all **5 fingers open** with your **palm facing the camera**. Alternatively, raise 3 fingers (Index + Middle + Ring). |
| **Double Click** | 🤚 **Open Hand (Back of Hand)** | Turn your hand around and show all **5 fingers open** with the **back of your hand facing the camera**. |

---

## 🖥️ Window Controls & Shortcuts

| Key / Action | Result |
| :--- | :--- |
| **Esc Key** | **Emergency Exit** — Works instantly anywhere on Windows, even if another app has focus. |
| **'q' Key** | Exit the application while the camera window is active. |
| **'X' Button** | Click the red close button on the preview window to exit. |
| **'m' Key** | Toggle between **Compact Mode** (small corner preview) and **Full Size**. |
| **'h' Key** | Snap the window back to its default bottom-right corner position. |

---

## 💡 Best Practices for Smooth Experience

1. **Camera Position & Distance**:
   - Sit **1.5 to 3 feet (50–90 cm)** away from the camera.
   - Keep your hand within the camera frame boundary shown by the dashed box.
2. **Lighting**:
   - Ensure your room is well-lit. Avoid bright lights directly behind you (backlighting).
3. **Resting Your Hand**:
   - To pause interaction without moving the cursor, simply close your hand into a loose fist or lower it out of the camera view.
4. **Scrolling PDFs & Browsers**:
   - When entering Scroll Mode (2 fingers up), the mouse cursor automatically locks in place so you can read and scroll documents comfortably without accidentally clicking or moving windows.
