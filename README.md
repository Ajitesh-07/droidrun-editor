<<<<<<< HEAD
# DroidRun Editor: The Autonomous Video Editor

> **An autonomous multimodal agent that analyzes video context using Gemini Vision and physically controls the InShot app to execute professional edits.**

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.10+-blue.svg) ![Platform](https://img.shields.io/badge/platform-Android-green.svg) ![Powered By](https://img.shields.io/badge/AI-Gemini%202.5%20Pro-orange)

## The Problem
Creators face a gap between **Creative Intent** and **Technical Execution**. Mobile editing is tedious, and current AI tools are "blind" scripts that can't see the footage they are editing.

## The Solution
**DroidRun Editor** is an agentic workflow that bridges this gap. It doesn't just write code; it has **eyes and hands**.
1.  **It Sees:** Uses **Gemini** to watch raw footage and understand mood (e.g., "Sad", "Hype", "Cinematic").
2.  **It Plans:** Generates a frame-perfect editing script (JSON) with specific effects and timings.
3.  **It Acts:** Uses **DroidRun** to physically click, swipe, and drag inside the **InShot** Android app, executing the edit like a human.

---

## Architecture

The system operates in three distinct phases:

### 1. The Director (Brain)
* **Input:** Raw images/video paths + User Prompt (e.g., "Make a glitchy hype edit").
* **Model:** Gemini 2.5 Pro
* **Output:** A structured `Execution Plan` containing tool calls (e.g., `apply_effect("Glitch")`, `cut_clip(2.5s)`).

### 2. The Dashboard
* A **Tkinter-based GUI** that manages the workflow.
* Handles **ADB File Ingestion** (syncing PC images to Android Gallery).
* Live **State Tracking** (Planning -> Setup -> Editing).

### 3. The Operator
* **Engine:** `DroidRun` (Custom ADB/UIAutomator wrapper).
* **Capabilities:**
    * **Robust Navigation:** Uses UI tree analysis to find buttons.
    * **Coordinate Tapping:** Bypasses "unclickable" ghost elements.
    * **Robust to screen width and height:** Does auto calibration at start to figure out optimal scroll amount so that edits can be done quick

## Installation & Setup

### Prerequisites
* **Python 3.10+**
* **uv** installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
* **Android Phone** with:
    * Developer Options & USB Debugging **ENABLED**.
    * **InShot Video Editor** installed.
* **ADB** (Android Debug Bridge) installed and in System PATH.

### 1. Clone & Sync
```bash
git clone https://github.com/Ajitesh-07/droidrun-editor.git
cd droidrun_editor

# Sync dependencies
uv sync
# Go to the venv and install droidrun
.\.venv\Scripts\activate
uv pip install https://github.com/droidrun/droidrun.git
```

## 🕹️ Usage

1. **Set the enviornment variables**
   * You have to make .env with GEMINI_API_KEY="" your key

2. **Start Redis**
   * It uses Redis to store its internal mappings, make sure to start it on port 6379
     ```bash
     docker run -d --name redis-server -p 6379:6379 redis
     ```

2.  **Launch the Dashboard**
    ```bash
    python main.py
    ```

3.  **Ingest Footage**
    * Click **"Select Images"** and choose your raw photos/videos on PC.
    * Click **"Upload & Sync"**. The tool will push files to `/sdcard/Pictures/droidrun/` and force the Gallery to update.

4.  **Direct the AI**
    * Enter a prompt: *"Make a fast-paced edit with a cyberpunk vibe."*
    * Click **"MAKE EDIT"**.

5.  **Make edit**
    * The agent will open InShot. (Install it first and use it once so that no weird tutorials come in between edits)
    * It will select your images.
    * It will apply durations, effects, and transitions autonomously.
---



=======
# DroidRun Editor: The Autonomous Video Editor

> **An autonomous multimodal agent that analyzes video context using Gemini Vision and physically controls the InShot app to execute professional edits.**

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.10+-blue.svg) ![Platform](https://img.shields.io/badge/platform-Android-green.svg) ![Powered By](https://img.shields.io/badge/AI-Gemini%202.5%20Pro-orange)

## The Problem
Creators face a gap between **Creative Intent** and **Technical Execution**. Mobile editing is tedious, and current AI tools are "blind" scripts that can't see the footage they are editing.

## The Solution
**DroidRun Editor** is an agentic workflow that bridges this gap. It doesn't just write code; it has **eyes and hands**.
1.  **It Sees:** Uses **Gemini** to watch raw footage and understand mood (e.g., "Sad", "Hype", "Cinematic").
2.  **It Plans:** Generates a frame-perfect editing script (JSON) with specific effects and timings.
3.  **It Acts:** Uses **DroidRun** to physically click, swipe, and drag inside the **InShot** Android app, executing the edit like a human.

---

## Architecture

The system operates in three distinct phases:

### 1. The Director (Brain)
* **Input:** Raw images/video paths + User Prompt (e.g., "Make a glitchy hype edit").
* **Model:** Gemini 2.5 Pro
* **Output:** A structured `Execution Plan` containing tool calls (e.g., `apply_effect("Glitch")`, `cut_clip(2.5s)`).

### 2. The Dashboard
* A **Tkinter-based GUI** that manages the workflow.
* Handles **ADB File Ingestion** (syncing PC images to Android Gallery).
* Live **State Tracking** (Planning -> Setup -> Editing).

### 3. The Operator
* **Engine:** `DroidRun` (Custom ADB/UIAutomator wrapper).
* **Capabilities:**
    * **Robust Navigation:** Uses UI tree analysis to find buttons.
    * **Coordinate Tapping:** Bypasses "unclickable" ghost elements.
    * **Robust to screen width and height:** Does auto calibration at start to figure out optimal scroll amount so that edits can be done quick

## Installation & Setup

### Prerequisites
* **Python 3.10+**
* **uv** installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
* **Android Phone** with:
    * Developer Options & USB Debugging **ENABLED**.
    * **InShot Video Editor** installed.
* **ADB** (Android Debug Bridge) installed and in System PATH.

### 1. Clone & Sync
```bash
git clone https://github.com/Ajitesh-07/droidrun-editor.git
cd droidrun_editor

# Sync dependencies
uv sync
# Go to the venv and install droidrun
.\.venv\Scripts\activate
uv pip install https://github.com/droidrun/droidrun.git
```

## 🕹️ Usage

1. **Set the enviornment variables**
   * You have to make .env with GEMINI_API_KEY="" your key

2. **Start Redis**
   * It uses Redis to store its internal mappings, make sure to start it on port 6379
     ```bash
     docker run -d --name redis-server -p 6379:6379 redis
     ```

2.  **Launch the Dashboard**
    ```bash
    python main.py
    ```

3.  **Ingest Footage**
    * Click **"Select Images"** and choose your raw photos/videos on PC.
    * Click **"Upload & Sync"**. The tool will push files to `/sdcard/Pictures/droidrun/` and force the Gallery to update.

4.  **Direct the AI**
    * Enter a prompt: *"Make a fast-paced edit with a cyberpunk vibe."*
    * Click **"MAKE EDIT"**.

5.  **Make edit**
    * The agent will open InShot. (Install it first and use it once so that no weird tutorials come in between edits)
    * It will select your images.
    * It will apply durations, effects, and transitions autonomously.
---



>>>>>>> 52c5d1262155c899244aba5968ff6253184ba613
