# 🤖 AI Usage Report & Originality Declaration
**Project**: AI Gesture Mouse — Touchless Computer Control Interface  
**Competition**: IntelliCon 2026 (Gate 3 — Final Submission)  
**Date**: October 2026  
**Team**: Team New Moon (University of Kelaniya)  

---

## 1. Executive Summary & Overview
This report documents the extent, methodologies, and guidelines governing the use of Artificial Intelligence (AI) tools during the design, development, optimization, and documentation of **AI Gesture Mouse** for **IntelliCon 2026**.

Our team adopted a transparent, responsible, and ethical approach to AI tool usage. AI was utilized primarily as an engineering accelerator — assisting in architectural brainstorming, digital signal processing (DSP) filter tuning, unit test generation, and documentation refinement — while the core engineering, system architecture, UX design, problem formulation, and integration were conceived, directed, and verified by team members.

---

## 2. Inventory of AI Tools Utilized

| AI Tool / Model | Provider | Primary Application / Scope of Assistance |
| :--- | :--- | :--- |
| **Claude (Anthropic)** | Anthropic | Architectural review, refactoring assistance, coordinate mapping optimization |
| **Google Gemini / DeepMind** | Google | Mathematical formulation of 1-Euro filter parameters, state machine edge-case analysis |
| **GitHub Copilot** | GitHub / OpenAI | Code auto-completion, boilerplate test mock drafting |
| **MediaPipe Pretrained Models** | Google | Pre-trained deep learning landmark model (`hand_landmarker.task`) for on-device 21 3D point estimation |

---

## 3. How AI Tools Contributed to the Project

### A. Mathematical DSP & Filter Parameter Tuning
* **Challenge**: Human hand physiological micro-tremors and camera sensor noise cause rapid 1–3 pixel variations, resulting in jittery desktop cursor movement.
* **AI Contribution**: We consulted AI tools to mathematically model the **1-Euro Filter** (Casiez et al., CHI 2012) and adapt its dynamic cutoff equations for 30–60 FPS webcam frame rates. AI assisted in calculating appropriate baseline cutoff frequencies ($f_{c,\min} = 0.4\text{ Hz}$) and velocity response coefficients ($\beta = 0.05$).
* **Human Validation**: The final parameter weighting, 3-sample median rejection window, and screen-space cubic Hermite deadzone easing were empirically validated and calibrated on physical hardware across different lighting conditions and webcam resolutions.

### B. State Machine & Edge-Case Safeguards
* **Challenge**: Rapid transition between gestures (e.g. releasing a thumbs-up right click to move the cursor) caused intermediate finger uncurling to intermittently trigger unintended left clicks, dismissing right-click context menus.
* **AI Contribution**: Used AI reasoning to analyze state transition lifecycles, identifying that active-state latching needed continuous timestamp refreshing across held frames rather than one-shot event timestamps.
* **Human Validation**: Authored comprehensive test cases simulating multi-second gesture holds followed by rapid hand posture changes to verify 100% elimination of phantom clicks.

### C. Test Suite & Coverage Expansion
* **Challenge**: Ensuring zero regression across coordinate bounds, asymmetric margins, debounce cooldowns, and diverse handedness orientations.
* **AI Contribution**: AI tools assisted in drafting synthetic landmark geometry fixtures (simulating coordinates for wrists, PIP joints, and fingertips) across diverse hand configurations.
* **Human Validation**: All 37 automated tests in `tests/` were reviewed, executed, and validated using `pytest` on real Python 3.13 environments.

---

## 4. Declaration of Originality & Pre-Existing Work

1. **Originality of Architecture & Core Logic**:
   The architectural design, unified 5-gesture interaction paradigm, dual-API hand tracker bridge (supporting both legacy `mediapipe.solutions` and modern `MediaPipe Tasks API`), Tkinter Launcher UX, and action mapping system are original works developed by Team New Moon.

2. **Open-Source Components & Attribution**:
   * **OpenCV (`cv2`)**: Used for real-time video capture, frame flipping, and visual HUD rendering under Apache 2.0.
   * **Google MediaPipe**: Used as an on-device perception backbone for hand landmark inference under Apache 2.0.
   * **PyAutoGUI**: Used for cross-platform OS desktop mouse and keyboard event emulation under BSD 3-Clause.
   * **NumPy**: Used for vector mathematics under BSD 3-Clause.

3. **No Code Plagiarism**:
   No proprietary, unauthorized, or confidential third-party codebases were copied or reverse-engineered. All external dependencies are standard open-source libraries pinned in `requirements.txt`.

---

## 5. Data Privacy & Handling Declarations

* 🛡️ **100% On-Device Local Processing**: All video capture, landmark extraction, and coordinate translation occur strictly in local device RAM using on-device CPU/GPU acceleration.
* 🚫 **Zero Cloud Transmission**: No video feeds, biometric landmark data, or webcam images are ever uploaded, transmitted to external servers, or logged across networks.
* 🔒 **Zero Biometric Data Storage**: Hand landmarks are discarded frame-by-frame; only high-level anonymized session telemetry (gesture counts, frame rates) is saved locally to `analytics_report.json` if telemetry is explicitly enabled by the user.
* 📹 **Camera Privacy Indicators**: The software displays an explicit always-on-top preview HUD and releases the camera hardware handle immediately upon pressing `q` or closing the application.

---

## 6. Conclusion
The integration of AI development assistants adhered strictly to ethical, transparent engineering standards. AI served as an amplifier for our team's engineering velocity, enabling us to deliver a production-grade, robust, and accessible touchless computing solution for **IntelliCon 2026**.
