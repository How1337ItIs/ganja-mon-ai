# 🌿 Ganja Mon Translator Dashboard

This is a local web dashboard that uses the Grok API to translate English text into the "Ganja Mon" Jamaican Patois persona.

## Setup

1.  **Requirements:**
    *   Python 3.10+
    *   `pip install fastapi uvicorn python-dotenv openai pydantic`
    *   An `.env` file in this directory with `XAI_API_KEY=...`

2.  **Files:**
    *   `grok_translate_dashboard.py`: The main server script.
    *   `grok_chat_prompt.txt`: The system prompt defining the persona.
    *   `run_dashboard.bat`: Double-click this to start on Windows.

## Usage

1.  **Start the Dashboard:**
    *   **Windows:** Double-click `run_dashboard.bat`.
    *   **Command Line:** Run `python grok_translate_dashboard.py`.

2.  **Open in Browser:**
    *   Go to [http://localhost:8086](http://localhost:8086).
    *   You should see the purple/blue dashboard.

3.  **Translate:**
    *   Type your text in the top box.
    *   Click "Translate" (or press Ctrl+Enter).
    *   The Patois translation will appear below.

## Troubleshooting

*   **Server won't start?**
    *   Check if Python is installed and in your PATH.
    *   Check if dependencies are installed (`pip install -r requirements.txt` if available, or the command above).
    *   Check if port 8086 is used (the script will try 8087, 8088 automatically).

*   **Translation fails?**
    *   Check the console window for error messages.
    *   Verify your `XAI_API_KEY` is correct in `.env`.
    *   Check your internet connection.

## API Note

This dashboard connects directly to `https://api.x.ai/v1` using the `grok-3` model (configurable in code).
