# Harvey: Privacy-Preserving Live Meeting Companion

Harvey is a lightweight, low-latency desktop utility designed to act as your real-time assistant during online presentations, technical calls, and live meetings.

By combining Windows-native OCR, loopback audio transcription, and LLM APIs, Harvey analyzes your local context to generate explanations, summaries, and answers on the fly. To protect presenter privacy, Harvey utilizes OS-level display affinity to remain **completely invisible** to meeting streams, screen sharing, and screenshots.

---

## Key Features

*   🔒 **Presenter-Privacy Overlay**: Leverages Windows API `SetWindowDisplayAffinity` to exclude the overlay window from all capture pipelines (Zoom, Teams, Google Meet, Snipping Tool, OBS). It is visible only to your physical eyes.
*   🎙️ **Dual-Channel Audio Capture**: 
    *   *Partner Mode* (`F2`): Captures meeting speaker audio directly from your system output (via WASAPI loopback, no virtual cables needed).
    *   *Self Mode* (`F3`): Captures your physical microphone input.
*   🖥️ **Native Local OCR** (`F4`): Uses Windows' built-in UWP OCR engine (`Windows.Media.Ocr`) to extract screen text locally in sub-seconds. No external vision API keys or network images are transmitted.
*   🎛️ **Live Settings Panel**: Adjust output style (e.g., *Concise & Direct*, *Detailed Explanatory*, *Code Only*, *Bullet Points*) and max word limits (50 to 500 words) on the fly during a call.
*   ⚡ **Single-Finger Triggers**: Global hotkeys map actions to simple function keys (`F2`, `F3`, `F4`, `F5`) for instant background executions.

---

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Aniket-Nikam/Harvey.git
   cd Harvey
   ```

2. **Initialize Environment**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Install Dependencies**:
   Run the setup script:
   ```bash
   build.bat
   ```

4. **Launch Harvey**:
   ```bash
   run.bat
   ```

---

## Controls & Usage

*   **`F2`**: Capture Loopback Audio (Partner speaking) -> Generates Answer.
*   **`F3`**: Capture Microphone Audio (You speaking) -> Generates Answer.
*   **`F4`**: Capture Screen Context (Local OCR) -> Generates Answer.
*   **`F5`**: Execute the selected mode on the GUI settings panel.
