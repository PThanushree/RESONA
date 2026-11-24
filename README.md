# RESONA: Accessible Programming & Audio-Based Code Comprehension System

[![KSCST 50th Series](https://img.shields.io/badge/KSCST-50th%20Series%20SPP-blue.svg)](https://kscst.org.in/)
[![Institution](https://img.shields.io/badge/College-JSS%20Science%20%26%20Technology%20University-gold.svg)](https://jssstuniv.in/)
[![Theme](https://img.shields.io/badge/Theme-AI%2C%20Data%20Science%20%26%20Digital%20Technologies-green.svg)]()
[![WCAG](https://img.shields.io/badge/Accessibility-WCAG%202.2%20AAA-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/Tests-19%20Passed%20%28100%25%29-success.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()

> **KSCST Student Project Programme (2026–2027)**  
> **Department of Computer Science and Engineering, JSS Science and Technology University, Mysuru**  
> **Project Guide:** Dr. Priyanka D  
> **Team Members:** Thanushree P (Team Leader), Prakruthi Prasad, Chinmayi A S, Sanjana R  

---

## 🌟 Overview

**RESONA** is an assistive programming environment and audio-augmented code comprehension and debugging system designed specifically for **blind and visually impaired (BVI) programmers**. 

While traditional screen readers (such as NVDA or JAWS) linearize source code into flat, tedious speech ("space space space space def..."), RESONA transforms code structure and runtime behavior into an intuitive **auditory soundscape**:
- **Acoustic Indentation Sonification:** Real-time musical pitch scaling (C4 to C5 pentatonic scale) conveying nesting depth as developers navigate code.
- **Syntactic Earcons:** Distinct musical motifs for functions, loops, branches, variable mutations, and runtime exceptions.
- **AST Structural Hierarchy:** Non-visual hierarchical tree navigation and instant outline summaries (`Alt+O`).
- **Time-Travel Auditory Debugger:** Controlled execution tracing (`sys.settrace`) with step-forward (`F10`), step-back (`Shift+F10`), and continuous audio soundscape playback (`Ctrl+Shift+P`).
- **Contextual AI Narrator:** Plain-English natural language code summaries and intelligent bug diagnostics explaining *why* an error occurred and suggesting the exact fix.
- **WCAG 2.2 AAA Compliant Interface:** High-contrast modes (Yellow-on-Black, Blue-on-Yellow, Dark High Contrast) with full ARIA live region support.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher installed on your system.

### 2. Installation
Clone the repository or navigate to the project directory:
```bash
cd resona
pip install -r requirements.txt
```

### 3. Launching RESONA
To launch the accessible web application and automatically open your default browser:

**On Windows:**
Double-click `run_resona.bat` or run:
```bash
python start.py
```
The application will launch and open in your accessible browser at **`http://127.0.0.1:8000`**.

### 4. Running the Accessible Terminal CLI
For terminal-only or headless workflows:
```bash
python -m resona.cli.resona_cli examples/01_binary_search.py
```
To step through code interactively with audio beeps in your terminal:
```bash
python -m resona.cli.resona_cli examples/01_binary_search.py --step
```

---

## ⌨️ Keyboard Shortcuts Reference

| Shortcut | Action | Description |
| :--- | :--- | :--- |
| **`F5`** or **`Ctrl + Enter`** | **Run & Sonify** | Analyzes AST hierarchy, traces execution, and sonifies code |
| **`F6`** | **Switch Pane Focus** | Cycles keyboard focus between Editor, AST Tree, Debugger, and Console |
| **`F10`** | **Step Forward** | Advances execution to the next line in the time-travel debugger |
| **`Shift + F10`** | **Step Backward** | Reverses execution to prior step (Time-Travel debugging) |
| **`Ctrl + Shift + P`** | **Play/Pause Soundscape**| Autoplays acoustic execution trace as a continuous audio sequence |
| **`Alt + O`** | **Hear Code Outline** | Speaks structural landmarks (functions, loops, classes) across the file |
| **`Alt + A`** | **AI Narration** | Announces natural language code explanation and bug diagnosis |
| **`Alt + T`** | **Cycle Theme** | Cycles between 4 high-contrast visual accessibility themes |
| **`Alt + H`** | **Audio Help** | Reads keyboard shortcuts help aloud via speech synthesis |
| **`Escape`** | **Cancel Audio** | Instantly stops ongoing speech narration or soundscape playback |
| **`Arrow Up / Down`** | **Editor Navigation** | Moves cursor; plays real-time indentation depth microtone |

---

## 🎶 Auditory Earcon Legend

| Acoustic Earcon | Musical Profile | Semantic Meaning in Code |
| :--- | :--- | :--- |
| **Indentation Depth 0–7** | Pentatonic scale (261 Hz – 659 Hz) | Indentation and nesting depth level |
| **Function Entry** | Ascending triad (C4 &rarr; E4 &rarr; G4) | Entering a function definition / call |
| **Class Entry** | Regal fourths (D4 &rarr; G4 &rarr; D5) | Entering a class structure |
| **Loop Iteration** | Rapid marimba double tap (440 Hz) | Loop cycling / repeating iteration |
| **Branch True** | High crisp bell (B5, 988 Hz) | Conditional evaluated to True |
| **Branch False** | Damped low blip (F4, 349 Hz) | Conditional evaluated to False |
| **Variable Mutation** | Water droplet pluck (G5, 784 Hz) | Variable created or mutated in memory |
| **Function Return** | Descending cadence (G4 &rarr; E4 &rarr; C4) | Returning value to caller frame |
| **Runtime Error** | Dissonant tritone chord (C3 + C4 + F#4) | Unhandled exception or runtime crash |
| **Execution Success** | Sparkling major chord (C4-E4-G4-C5) | Program cleanly completed execution |

---

## 📂 Repository Structure

```
resona/
├── core/                       # Core Architecture Engines
│   ├── ast_analyzer.py         # AST parser, scope hierarchy, syntax error guidance
│   ├── runtime_debugger.py     # sys.settrace debugger, variable deltas, time-travel
│   ├── sonification_engine.py  # Audio mapping engine (pitch, pan, earcons)
│   ├── ai_narrator.py          # Context engine & plain-English bug diagnostician
│   └── audio_synthesizer.py    # NumPy-accelerated 16-bit WAV audio generator
│
├── web/                        # WCAG 2.2 AAA Accessible Web Application
│   ├── static/css/             # High-contrast accessibility stylesheets
│   ├── static/js/              # Web Audio API synthesizer, ARIA announcer, AST tree
│   ├── static/sounds/          # Pre-rendered 16-bit PCM WAV earcon audio assets
│   ├── templates/index.html    # Keyboard-first accessible editor interface
│   └── server.py               # FastAPI backend with REST & audio streaming endpoints
│
├── cli/                        # Terminal-Based Accessible Interface
│   └── resona_cli.py           # Rich terminal UI with ASCII tree & audio alerts
│
├── examples/                   # Demonstration Algorithm Suite
│   ├── 01_binary_search.py     # Binary search (loops, branches, variable mutations)
│   ├── 02_recursion_factorial.py # Recursion (call stack pitch escalation)
│   ├── 03_nested_loops_bubblesort.py # Bubble sort (nested loop sonification)
│   ├── 04_buggy_off_by_one.py  # Off-by-one bug (AI bug diagnosis & fix guidance)
│   ├── 05_zero_division.py     # ZeroDivisionError (exception tritone chord)
│   └── 06_student_grading.py   # Multi-branch if/elif/else decision sonification
│
├── tests/                      # Automated Verification Suite
│   ├── run_tests.py            # Comprehensive test runner (19 tests, 100% pass)
│   ├── test_ast_analyzer.py    # AST structure & nesting tests
│   ├── test_runtime_debugger.py# Execution trace & variable delta tests
│   ├── test_sonification.py    # Frequency & audio buffer tests
│   ├── test_ai_narrator.py     # AI narrative & diagnosis tests
│   └── test_api.py             # FastAPI REST endpoint integration tests
│
├── docs/                       # Comprehensive Project Documentation
│   ├── KSCST_PRESENTATION_GUIDE.md # Panel presentation script & live demo sequence
│   ├── ACCESSIBILITY_GUIDE.md  # WCAG 2.2 AAA compliance & screen reader setup
│   ├── SYSTEM_ARCHITECTURE.md  # System diagrams & engineering design
│   └── EVALUATION_REPORT.md    # Quantitative benchmarks & usability report
│
├── start.py                    # Master application launcher
├── run_resona.bat              # Windows one-click batch launcher
├── requirements.txt            # System dependencies
└── README.md                   # Project documentation
```

---

## 🧪 Testing and Verification

To run the complete automated test suite:
```bash
python tests/run_tests.py
```
**Results:** 19 out of 19 tests passing with 100% success rate across AST analysis, runtime tracing, audio synthesis, AI bug diagnosis, and API endpoints.

---

## 🎓 Academic Accreditation

- **Project:** 50th Series Student Project Programme (2026–2027)
- **Sponsoring Body:** Karnataka State Council for Science and Technology (KSCST), Indian Institute of Science campus, Bengaluru – 560 012
- **Institution:** JSS Science and Technology University, Mysuru
- **Department:** Computer Science and Engineering
- **Focus Area:** Human–Computer Interaction (HCI) and Assistive Technology
- **UN Sustainable Development Goals:** SDG 4 (Quality Education), SDG 9 (Industry, Innovation & Infrastructure), SDG 10 (Reduced Inequalities)
