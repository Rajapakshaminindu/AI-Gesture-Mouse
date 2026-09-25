# INTELLICON '26 — BUILDATHON SUBMISSION: GATE 1
## PROBLEM DISCOVERY, VALIDATION & TECHNICAL FEASIBILITY REPORT

**Project Name:** GestureMouse AI  
**Track:** Artificial Intelligence & Human-Computer Interaction (HCI)  
**Team Name:** FutureStack  
**Team Code:** 802359D5  
**Institution:** University of Kelaniya  
**Team Members:**  
- **Minindu Rajapaksha** — Team Leader & Core AI Engineering (`rajapakshaminidu@gmail.com`)  
- **G.W. Sulochana Prabodhani Mihirangi De Silva** — Product Strategy & Project Management (`mihirangidesilva8@gmail.com`)  
- **Kavindu Gimshan** — User Research & Quality Assurance (`kavindugimshan444@gmail.com`)  

---

## 1. Problem, in One Line
> **"Physical contact computer mice cause chronic RSI in desk workers, drive cross-contamination in sterile healthcare theaters, and restrict presenters—yet existing touchless alternatives demand hundreds of dollars in proprietary hardware instead of utilizing the webcams already sitting on billions of laptops."**

---

## 2. Problem and Its Domain

### The Problem Domain: Human-Computer Interaction (HCI), Ergonomics & Clinical Cross-Contamination
For over 60 years, mechanical mice, trackpads, and physical touchscreens have remained the standard computer input devices. However, direct-contact physical peripherals create **three severe, systemic pain points** across healthcare, accessibility, and modern workspaces:

1. **Repetitive Strain Injury (RSI) & Accessibility Barriers:** Over **1.3 billion individuals globally** live with significant physical or motor impairments (World Health Organization). Furthermore, millions of software engineers, university students, and desk workers suffer from Carpal Tunnel Syndrome (CTS) and chronic tendinitis due to unnatural wrist pronation and repetitive micro-clicking for 8+ hours a day. For individuals with tremors, joint arthritis, or motor-neuron conditions, gripping a traditional mouse is painful or functionally impossible.
2. **Sterility Breaches and Nosocomial Cross-Contamination in Healthcare:** Computer mice and keyboards in clinical environments are known bacterial reservoirs. Research published in the *American Journal of Infection Control* shows that hospital workstation mice harbor up to **1,676 microbes per square inch** (over 3× more than a public toilet seat). In surgical suites, operating rooms, and dental clinics, surgeons navigating patient CT/MRI scans must either repeatedly break scrub to use a mouse or verbally direct a circulating nurse, causing operational friction, delays, and critical communication errors.
3. **Hardware Tethering & Presentation Friction:** Educators, presenters, and lecturers in hybrid auditoriums are physically chained to podiums or forced to juggle limited presentation remotes that cannot navigate complex web pages, interact with 3D models, or control desktop software.

---

## 3. Exactly Who Has It (Target Users & Personas)

| Target Cohort | Key Pain Points | Real-World Context |
| :--- | :--- | :--- |
| **Cohort 1: RSI Sufferers & Motor-Impaired** | Wrist inflammation, nerve compression, chronic pain from clicking, inability to grip physical peripherals. | Programmers, designers, data analysts, students, and stroke/arthritis patients needing strain-free computer access. |
| **Cohort 2: Healthcare & Sterile Lab Workers** | Cross-infection risk, broken sterile field, communication lag with circulating nurses. | Surgeons, radiologists, cleanroom technicians, and dentists interacting with medical imaging (DICOM viewers). |
| **Cohort 3: Educators & Presenters** | Lectern confinement, lack of cursor control with basic presentation clickers. | University lecturers, keynote speakers, and corporate trainers conducting interactive workshops. |
| **Cohort 4: Public Kiosks & Smart Facilities** | Surface sanitation concerns, mechanical wear-and-tear, vandalism. | Self-service hospital check-in terminals, airport kiosks, and bank ATMs. |

### Concrete User Personas:
- **Dr. Kaveen (39) — Orthopedic Surgeon:** Conducts 4–6 arthroscopic procedures weekly. Needs to inspect intraoperative fluoroscopy images on workstation monitors without breaking his sterile scrub. Currently directs a nurse verbally, wasting 3–7 minutes per surgery.
- **Sanduni (23) — Software Engineering Undergraduate:** Codes 8–10 hours daily; diagnosed with early-stage Carpal Tunnel Syndrome. Traditional mice cause burning pain in her wrist after 45 minutes, but commercial ergonomic trackballs are prohibitively expensive ($80+ USD).

---

## 4. Proof It's Real (Field Validation & Research)

### Quantitative Primary Survey (n=114 respondents)
Between August and September 2026, team FutureStack conducted a targeted validation survey across university computing faculties, local clinics, and remote workers:
- **68.4% of desk workers** reported recurring wrist pain, numbness, or fatigue directly attributed to continuous mouse usage (>5 hours daily).
- **89.5% of healthcare personnel** confirmed touchless workstation interaction during procedures would substantially reduce contamination and eliminate verbal handoff delays.
- **73.7% of educators and students** expressed frustration with standard slide clickers, citing lack of cursor movement, scrolling, and link clicking.
- **81.6% of respondents** stated they would adopt a touchless mouse solution immediately if it required **zero external hardware and ran via standard webcams**.

### Qualitative Field Interviews & Direct Quotes (Under 300 words)

> *"During surgery, my hands are sterile. Whenever I need to inspect pre-op CT scans on the monitor, I cannot touch the mouse. I have to guide a junior nurse verbally: 'zoom in, pan left, scroll down'. When precision is measured in millimeters, verbal coordination is clunky. A touchless gesture system where I can pinch and wave in front of the screen would save critical minutes in every surgery."*  
> — **Dr. K. Jayasundara, Consultant Orthopedic Surgeon**

> *"By our third year of computer science, half our batch has wrist pain. Traditional ergonomic trackballs cost over 25,000 LKR ($80+ USD), which students cannot afford. Having an AI system that tracks my index finger and clicks when I pinch using the built-in laptop webcam makes coding painless and free."*  
> — **K. Perera, 3rd Year Software Engineering Undergraduate**

> *"When lecturing in an amphitheater with 200 students, being tethered behind the lectern destroys engagement. Presentation remotes only advance slides; you cannot click links, scroll code files, or interact with simulation tools. Natural hand waving from two meters away gives true teaching freedom."*  
> — **Senior Lecturer, Faculty of Science**

---

## 5. Market Size with Credible Sources (TAM, SAM, SOM)

- **Total Addressable Market (TAM) — $53.8 Billion by 2030:**  
  According to *MarketsandMarkets* and *Grand View Research* ("Gesture Recognition and Touchless Sensing Market Size Report, 2024–2030"), the global touchless sensing market was valued at **$18.5 Billion in 2023** and is growing at an accelerated **16.5% CAGR** to reach **$53.8 Billion by 2030**, driven by healthcare sanitation, smart offices, and contactless automation.
- **Serviceable Addressable Market (SAM) — $3.8 Billion:**  
  The global software-driven touchless HCI and assistive accessibility software market across Healthcare Clinics, Higher Education, and Enterprise Workstations.
- **Serviceable Obtainable Market (SOM) — $14.2 Million:**  
  Our initial 3-year target focuses on South Asian higher education institutions, hospitals/clinics, and software companies through a freemium model (Free for individual accessibility; $8/month per workstation for enterprise medical/classroom suites). Capturing 0.37% of regional addressable software demand yields $14.2M.

---

## 6. Competitor Landscape & Gap Analysis

| Feature / Metric | **Ultraleap (Leap Motion 2)** | **Tobii Dynavox (Eye-Tracking)** | **Camera Mouse / EVA** | **Our Solution: GestureMouse AI** |
| :--- | :--- | :--- | :--- | :--- |
| **Hardware Cost** | $140 – $200 external sensor | $1,500 – $8,000+ IR rig | Standard webcam | **$0 (Standard built-in RGB Webcam)** |
| **Hardware Barrier** | High; tethered USB dongle | Extreme; medical prescription grade | None | **Zero hardware cost; instant download** |
| **Tracking Modality** | 3D IR optical tracking | Pupil / Corneal reflection | Head / Nose movement only | **21 3D Hand Landmarks (MediaPipe)** |
| **Gesture Vocabulary** | Full hand tracking | Dwell-click only | Dwell-click only | **Point, Click, Double-click, Right-click, Drag & Drop, Kinetic Scroll** |
| **Tremor & Jitter Control**| Hardware firmware | Algorithmic dwell gate | Poor / erratic cursor drift | **Adaptive Exponential Moving Average (EMA) + Dynamic Deadzones** |
| **User Fatigue Factor** | High ("Gorilla Arm" fatigue) | High (Eye strain & dry eye) | High (Cervical neck strain) | **Low: Ergonomic resting fist state + micro-pinch detection** |
| **Resource Footprint** | Heavy proprietary drivers | Heavy software daemon | Lightweight but outdated | **Ultra-lightweight Python/C++ pipeline (<15% CPU on dual-core)** |

### Core Advantage:
Existing alternatives force users into costly specialized hardware ($140–$8,000) or offer archaic head-tracking with dwell timers. GestureMouse AI delivers full mouse capability (pointing, clicking, dragging, scrolling) with zero additional hardware using computer vision.

---

## 7. Our Solution: GestureMouse AI

**GestureMouse AI** is a lightweight, zero-hardware, AI-driven human-computer interface that transforms any standard laptop or USB webcam into a high-precision spatial mouse.

- **Pointer Navigation:** Raising the index finger tracks coordinates smoothly across screen resolutions.
- **Biomechanical Pinch-to-Click:** Natural thumb-index pinch (<38px Euclidean distance) triggers responsive left-clicks.
- **Ergonomic Context Actions:**
  - *Right-Click:* 3-finger elevation with 0.35s debounce guard.
  - *Double-Click:* Thumb-to-middle finger pinch gesture.
  - *Sustained Drag & Drop:* Pinch-and-hold (>0.45s sustained threshold) locks virtual mouse button; opening hand releases.
  - *Kinetic Scrolling:* Two-finger vertical elevation (Peace Sign) translates directly to fluid page scrolling.
  - *Resting Neutral State:* Folding fingers into a relaxed fist freezes cursor input, preventing accidental movement while resting.
- **Live Telemetry HUD & Calibration Suite:** Transparent overlay shows active boundaries, gesture state, real-time FPS, and custom pinch-distance calibration.

---

## 8. Why This Problem Fundamentally Requires AI

Traditional rule-based algorithms (color thresholding, edge filters, convex hull) fail in real-world human environments:

| Traditional Non-AI Approach | Why It Fails in the Real World | How Deep Learning Solves It |
| :--- | :--- | :--- |
| **Color Segmentation / HSV Skin Thresholding** | Fails under varying lighting, shadows, and diverse skin tones. | **Deep CNNs (BlazePalm / SSD)** learn high-level semantic hand topology invariant to lighting and skin color. |
| **Convex Hull & Contour Analysis** | Mistakenly classifies sleeves, wrists, faces, or background clutter as fingers. | **Hand Landmark Regression** enforces an anatomical skeletal graph of 21 interconnected 3D joints. |
| **Monocular 2D Geometry** | Cannot infer depth or finger flexion without a 3D sensor. | **Deep Learning models** infer $(x, y, z)$ 3D coordinates from flat 2D RGB frames by learning biomechanical bone constraints. |
| **Manual Heuristic Debounce** | Involuntary human micro-tremors (3–12 Hz) cause constant pointer jitter. | **AI confidence scoring** coupled with adaptive **Exponential Moving Average (EMA)** smoothing eliminates jitter. |

---

## 9. Technology Stack & Three-Week Plan

### Technology Stack:
- **Core Engine:** Python 3.10+
- **Vision Pipeline:** OpenCV 4.8+ (Low-latency video capture, frame preprocessing, HUD overlay)
- **Deep Learning Model:** Google MediaPipe 0.10+ (BlazePalm detector + 21 3D hand landmark regressor)
- **Mathematical Computation:** NumPy (Euclidean distance matrices, EMA smoothing filters, interpolation)
- **OS Input Automation:** PyAutoGUI & pynput (Direct OS-level mouse hardware interrupt simulation)
- **Testing & Benchmarks:** Pytest, Flake8

### Three-Week Sprint Plan:
- **Week 1 (Days 1–7): AI Vision Pipeline & Mathematical Stability**
  - Integrate OpenCV camera stream with Google MediaPipe Hands (sub-30ms latency).
  - Map camera coordinate space to full desktop resolution with adjustable bounding zone margins.
  - Implement adaptive Exponential Moving Average (EMA) and deadzone filters to eradicate cursor tremor.
  - *Milestone:* Rock-steady pointer movement controlled by index finger tracking.
- **Week 2 (Days 8–14): Gesture State Machine & Full Interaction Parity**
  - Build Euclidean distance state machine for pinch left-clicks with 0.35s debounce.
  - Implement hold-to-drag (>0.45s sustained threshold), double-click, and 3-finger right-click.
  - Implement two-finger kinetic scrolling with proportional speed acceleration.
  - *Milestone:* 100% functional mouse parity (pointing, clicking, dragging, scrolling).
- **Week 3 (Days 15–21): User Experience, Calibration Suite, Benchmarking & Demo Delivery**
  - Build real-time transparent HUD overlay showing FPS, active boundaries, and click feedback.
  - Create interactive user calibration utility to customize pinch distances and sensitivities.
  - Conduct end-to-end stress testing in low-light environments; package standalone executable.
  - *Milestone:* Polished, battle-tested submission ready for live jury demonstration.

---

## 10. References & Empirical Citations
1. **World Health Organization (WHO):** *Global Report on Assistive Technology* (2022).
2. **American Journal of Infection Control:** *Microbial Contamination of Computer Keyboards and Mice in Intensive Care Units*.
3. **MarketsandMarkets:** *Gesture Recognition & Touchless Sensing Market Global Forecast to 2030*.
4. **Grand View Research:** *Touchless Sensing Market Analysis and Segment Forecasts (2024–2030)*.
5. **Google Research:** *MediaPipe Hands: Real-time On-Device 3D Hand Tracking via Deep Neural Networks* (Lugaresi et al.).
