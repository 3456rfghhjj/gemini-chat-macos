# Gemini Desktop Chat

A simple desktop GUI client for Google Gemini built with Python and Tkinter.

## What it does

- Rotates through multiple Gemini API keys automatically when rate limits (429 / quota errors) are hit
- Tracks token count after every prompt
- Compresses conversation history once it hits 4,000 tokens so context stays intact without breaking limits
- Threaded API calls so the window never freezes while waiting for an answer
- Clean dark theme interface

## Installation

You need Python 3.10 or newer.

```bash
pip install google-genai certifi
```

## Running the app

1. Open `gemini_chat.py`.
2. Put your API keys here:
```python
API_KEYS = [
    "your_key_1",
    "your_key_2",
]
```
3. Launch it:
```bash
python gemini_chat.py
```
