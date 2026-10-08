import os
import ssl
import sys
import threading
import time
import tkinter as tk

try:
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
except ImportError:
    pass

from google import genai
from google.genai import types

# --- CONFIGURATION ---
API_KEYS = [
    "YOUR_API_KEY_HERE",
    "YOUR_API_KEY_HERE",
    "YOUR_API_KEY_HERE",
    "YOUR_API_KEY_HERE",
    "YOUR_API_KEY_HERE",
]

MODEL_NAME = "models/gemini-3.1-flash-lite"
MAX_TOKENS_LIMIT = 4000

SYSTEM_INSTRUCTION = (
    "Respond exclusively in plain text. Never use Markdown formatting "
    "(no asterisks, hashes, bullet points with hyphens, or code blocks)."
)

# Color Scheme
BG_COLOR = "#1E2A22"
CHAT_BG_COLOR = "#243329"
PANEL_BG_COLOR = "#19221C"
ENTRY_BG_COLOR = "#2C3D32"
TEXT_COLOR = "#FFFFFF"

FONT_TEXT = ("Helvetica", 15)
FONT_BOLD = ("Helvetica", 15, "bold")
FONT_NAME = ("Helvetica", 16, "bold")

# Key Manager and Initialization
current_key_index = 0
client = genai.Client(api_key=API_KEYS[current_key_index])
chat = client.chats.create(
    model=MODEL_NAME,
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION
    )
)


def switch_to_next_key():
    global current_key_index, client, chat
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    new_key = API_KEYS[current_key_index]
    
    # Preserve conversation history when switching clients
    previous_history = chat.get_history()
    client = genai.Client(api_key=new_key)
    chat = client.chats.create(
        model=MODEL_NAME,
        history=previous_history,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION
        )
    )
    insert_text("System", f"Switched to API Key #{current_key_index + 1}\n")


def get_token_count():
    try:
        history = chat.get_history()
        if not history:
            return 0
        response = client.models.count_tokens(
            model=MODEL_NAME,
            contents=history
        )
        return response.total_tokens
    except Exception:
        return 0


def compact_history():
    global chat
    insert_text("System", "Automatic history compaction in progress...\n")

    compression_prompt = (
        "Summarize the entire conversation so far into a concise overview. "
        "Preserve essential facts, decisions, and technical details."
    )

    previous_history = chat.get_history()
    request_contents = previous_history + [
        types.Content(role="user", parts=[types.Part.from_text(text=compression_prompt)])
    ]

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=request_contents
    )
    summary = response.text

    new_context = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"[Context of previous conversation]: {summary}")]
        ),
        types.Content(
            role="model",
            parts=[types.Part.from_text(text="Understood, let's continue.")]
        )
    ]
    chat = client.chats.create(
        model=MODEL_NAME,
        history=new_context,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION
        )
    )
    insert_text("System", "Compaction complete.\n")


# --- GUI INTERFACE ---
root = tk.Tk()
root.title("Gemini Chat")
root.geometry("1100x700")
root.configure(bg=BG_COLOR)

top_frame = tk.Frame(root, bg=PANEL_BG_COLOR, pady=10, padx=16)
top_frame.pack(side="top", fill="x")

lbl_status = tk.Label(
    top_frame,
    text=f"Gemini Chat (Key #{current_key_index + 1})",
    fg=TEXT_COLOR,
    bg=PANEL_BG_COLOR,
    font=("Helvetica", 14, "bold")
)
lbl_status.pack(side="left")

lbl_tokens = tk.Label(
    top_frame,
    text="Tokens: 0 / 4000",
    fg="#A8C5B2",
    bg=PANEL_BG_COLOR,
    font=("Helvetica", 13)
)
lbl_tokens.pack(side="right")

bottom_frame = tk.Frame(root, bg=PANEL_BG_COLOR, pady=12, padx=16)
bottom_frame.pack(side="bottom", fill="x")

chat_frame = tk.Frame(root, bg=BG_COLOR)
chat_frame.pack(side="top", fill="both", expand=True, padx=14, pady=10)

scrollbar = tk.Scrollbar(chat_frame)
scrollbar.pack(side="right", fill="y")

chat_area = tk.Text(
    chat_frame,
    wrap=tk.WORD,
    bg=CHAT_BG_COLOR,
    fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR,
    font=FONT_TEXT,
    padx=16,
    pady=16,
    yscrollcommand=scrollbar.set,
    borderwidth=0,
    highlightthickness=0
)
chat_area.pack(side="left", fill="both", expand=True)
scrollbar.config(command=chat_area.yview)
chat_area.config(state="disabled")

chat_area.tag_config("user_tag", foreground="#8ED1A8", font=FONT_NAME)
chat_area.tag_config("gemini_tag", foreground="#B8E3C6", font=FONT_NAME)
chat_area.tag_config("sys_tag", foreground="#E6C280", font=("Helvetica", 13, "italic"))
chat_area.tag_config("err_tag", foreground="#E57373", font=("Helvetica", 14, "bold"))


def insert_text(sender, text):
    chat_area.config(state="normal")
    if sender == "You":
        chat_area.insert(tk.END, f"\n{sender}:\n", "user_tag")
    elif sender == "Gemini":
        chat_area.insert(tk.END, f"\n{sender}:\n", "gemini_tag")
    elif sender == "System":
        chat_area.insert(tk.END, f"\n[{sender}]: ", "sys_tag")
    else:
        chat_area.insert(tk.END, f"\n[{sender}]: ", "err_tag")

    chat_area.insert(tk.END, f"{text}\n")
    chat_area.see(tk.END)
    chat_area.config(state="disabled")


def update_token_count():
    tokens = get_token_count()
    lbl_tokens.config(text=f"Tokens: {tokens} / {MAX_TOKENS_LIMIT}")
    lbl_status.config(text=f"Gemini Chat (Key #{current_key_index + 1})")


entry_box = tk.Entry(
    bottom_frame,
    bg=ENTRY_BG_COLOR,
    fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR,
    font=FONT_TEXT,
    relief="flat"
)
entry_box.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=6)


def send_message(event=None):
    message = entry_box.get().strip()
    if not message:
        return

    entry_box.delete(0, tk.END)
    insert_text("You", message)

    def worker():
        attempts = len(API_KEYS)
        success = False

        for _ in range(attempts):
            try:
                response = chat.send_message(message)
                root.after(0, lambda: insert_text("Gemini", response.text))

                tokens = get_token_count()
                root.after(0, update_token_count)
                if tokens >= MAX_TOKENS_LIMIT:
                    root.after(0, compact_history)
                success = True
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower() or "exhausted" in error_str.lower():
                    root.after(0, switch_to_next_key)
                    time.sleep(1)
                else:
                    root.after(0, lambda: insert_text("Error", error_str))
                    break

        if not success:
            root.after(0, lambda: insert_text("System", "All API keys have exceeded their quota limits."))

    threading.Thread(target=worker, daemon=True).start()


entry_box.bind("<Return>", send_message)

btn_send = tk.Button(
    bottom_frame,
    text="Send",
    bg="#3B5342",
    fg=TEXT_COLOR,
    font=FONT_BOLD,
    relief="flat",
    command=send_message,
    padx=16,
    pady=4
)
btn_send.pack(side="right")

root.mainloop()