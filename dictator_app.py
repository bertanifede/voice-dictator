#!/usr/bin/env python3
"""
Voice Dictator Menu Bar App
- Hold Control key to record, release to transcribe and paste
- Shift+Control to start continuous recording, Control to stop
- Menu bar shows last 10 transcriptions
"""

import sys
import os
import subprocess
import tempfile
import threading
from datetime import datetime
import numpy as np
import sounddevice as sd
import whisper
import pyperclip
import rumps
from pynput import keyboard
from pynput.keyboard import Key, Controller
from collections import deque

# Hide Dock icon (only show in menu bar)
from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)

# Config
MODEL_SIZE = "medium"  # tiny, base, small, medium, large
SAMPLE_RATE = 16000
HOLD_KEY = Key.ctrl  # Control key (hold to record)
MAX_HISTORY = 10
MIN_AUDIO_DURATION = 0.5  # Minimum seconds of audio required
MIN_AUDIO_ENERGY = 0.001  # Minimum RMS energy (filters silence)

# Colors
class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

# State
recording = False
toggle_mode = False
shift_held = False
audio_data = []
model = None
kb = Controller()
history = deque(maxlen=MAX_HISTORY)  # Stores (timestamp, text) tuples
app = None


def load_model():
    global model
    print(f"{C.GRAY}Loading model...{C.RESET}", end="", flush=True)
    model = whisper.load_model(MODEL_SIZE)
    print(f" {C.GREEN}ready!{C.RESET}")


def start_recording():
    global recording, audio_data
    if recording:
        return
    recording = True
    audio_data = []
    update_icon("recording")
    print(f"{C.RED}🎤 Recording...{C.RESET}", end="", flush=True)

    def callback(indata, frames, time, status):
        if recording:
            audio_data.append(indata.copy())

    global stream
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.float32,
        callback=callback
    )
    stream.start()


def stop_recording():
    global recording, stream
    if not recording:
        return
    recording = False
    stream.stop()
    stream.close()
    update_icon("idle")
    print(f" {C.YELLOW}transcribing...{C.RESET}", end="", flush=True)

    if not audio_data:
        print(f" {C.GRAY}✗{C.RESET}")
        return

    # Combine audio chunks
    audio = np.concatenate(audio_data, axis=0).flatten()

    # Check minimum duration
    duration = len(audio) / SAMPLE_RATE
    if duration < MIN_AUDIO_DURATION:
        print(f" {C.GRAY}✗ (too short){C.RESET}")
        return

    # Check minimum energy (filter silence)
    rms_energy = np.sqrt(np.mean(audio ** 2))
    if rms_energy < MIN_AUDIO_ENERGY:
        print(f" {C.GRAY}✗ (no sound){C.RESET}")
        return

    # Transcribe
    result = model.transcribe(audio, fp16=False)
    text = result["text"].strip()

    if text:
        # Truncate display if too long
        display = text[:60] + "..." if len(text) > 60 else text
        print(f" {C.GREEN}✓{C.RESET}")
        print(f"  {C.GRAY}\"{display}\"{C.RESET}")
        # Add to history with timestamp
        timestamp = datetime.now().strftime("%I:%M %p")
        history.appendleft((timestamp, text))
        update_menu()
        # Copy to clipboard and paste
        pyperclip.copy(text)
        # Simulate Cmd+V to paste
        kb.press(Key.cmd)
        kb.press('v')
        kb.release('v')
        kb.release(Key.cmd)
    else:
        print(f" {C.GRAY}✗ (no speech){C.RESET}")


def update_icon(state):
    if app:
        if state == "recording":
            app.title = "rec"
        else:
            app.title = "mic"


def update_menu():
    if not app:
        return
    # Rebuild menu with history
    app.menu.clear()

    if history:
        for timestamp, text in history:
            # Truncate long texts for menu display
            display_text = text[:50] + "..." if len(text) > 50 else text
            item = rumps.MenuItem(f"{timestamp}  {display_text}", callback=make_copy_callback(text))
            app.menu.add(item)
        app.menu.add(rumps.separator)
        app.menu.add(rumps.MenuItem("Open in TextEdit", callback=open_in_textedit))

    app.menu.add(rumps.MenuItem("Clear History", callback=clear_history))
    app.menu.add(rumps.separator)
    app.menu.add(rumps.MenuItem("Quit", callback=quit_app))


def make_copy_callback(text):
    def copy_callback(_):
        pyperclip.copy(text)
        rumps.notification("Voice Dictator", "Copied!", text[:50] + "..." if len(text) > 50 else text)
    return copy_callback


def open_in_textedit(_):
    if not history:
        return

    # Format history nicely
    lines = []
    lines.append("=" * 50)
    lines.append("  VOICE DICTATOR - History")
    lines.append(f"  {datetime.now().strftime('%B %d, %Y')}")
    lines.append("=" * 50)
    lines.append("")

    for i, (timestamp, text) in enumerate(history, 1):
        lines.append(f"[{timestamp}]")
        lines.append(text)
        lines.append("")
        lines.append("-" * 30)
        lines.append("")

    content = "\n".join(lines)

    # Create temp file and open in TextEdit
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    subprocess.run(["open", "-a", "TextEdit", temp_path])


def clear_history(_):
    history.clear()
    update_menu()


def quit_app(_):
    rumps.quit_application()


def on_press(key):
    global toggle_mode, shift_held

    if key == Key.shift:
        shift_held = True

    if key == HOLD_KEY:
        if toggle_mode:
            # Control stops continuous recording
            toggle_mode = False
            threading.Thread(target=stop_recording).start()
        elif shift_held:
            # Shift+Control: start continuous recording
            toggle_mode = True
            start_recording()
        else:
            # Control only: hold to record
            start_recording()


def on_release(key):
    global shift_held

    if key == Key.shift:
        shift_held = False

    if key == HOLD_KEY and not toggle_mode and not shift_held:
        threading.Thread(target=stop_recording).start()


class DictatorApp(rumps.App):
    def __init__(self):
        super(DictatorApp, self).__init__("mic", quit_button=None)
        update_menu()


def run_keyboard_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


def main():
    global app

    print(f"{C.BOLD}🎙️  Voice Dictator{C.RESET}")
    print(f"{C.GRAY}{'─' * 36}{C.RESET}")
    load_model()
    print()
    print(f"  {C.BLUE}^{C.RESET}       Hold to record")
    print(f"  {C.BLUE}⇧+^{C.RESET}     Continuous mode")
    print()
    print(f"{C.GRAY}{'─' * 36}{C.RESET}")

    # Start keyboard listener in background thread
    kb_thread = threading.Thread(target=run_keyboard_listener, daemon=True)
    kb_thread.start()

    # Run menu bar app (blocks main thread)
    app = DictatorApp()
    app.run()


if __name__ == "__main__":
    main()
