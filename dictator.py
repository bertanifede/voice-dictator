#!/usr/bin/env python3
"""
Voice Dictator - Personal voice-to-text tool
- Hold Option key to record, release to transcribe and paste
- Shift+Option to start continuous recording, Option to stop
"""

import sys
import threading
import numpy as np
import sounddevice as sd
import whisper
import pyperclip
from pynput import keyboard
from pynput.keyboard import Key, Controller

# Config
MODEL_SIZE = "base"  # tiny, base, small, medium, large
SAMPLE_RATE = 16000
HOLD_KEY = Key.alt  # Option/Alt key (hold to record)

# State
recording = False
toggle_mode = False  # True when using toggle recording
shift_held = False  # Track if shift is held
audio_data = []
model = None
kb = Controller()


def load_model():
    global model
    print(f"🔄 Loading Whisper model '{MODEL_SIZE}'...")
    model = whisper.load_model(MODEL_SIZE)
    print("✅ Model loaded. Ready to dictate.")


def start_recording():
    global recording, audio_data
    if recording:
        return
    recording = True
    audio_data = []
    print("🎤 Recording...")

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
    print("⏹️  Stopped. Transcribing...")

    if not audio_data:
        print("❌ No audio recorded")
        return

    # Combine audio chunks
    audio = np.concatenate(audio_data, axis=0).flatten()

    # Transcribe
    result = model.transcribe(audio, fp16=False)
    text = result["text"].strip()

    if text:
        print(f"📝 \"{text}\"")
        # Copy to clipboard and paste
        pyperclip.copy(text)
        # Simulate Cmd+V to paste
        kb.press(Key.cmd)
        kb.press('v')
        kb.release('v')
        kb.release(Key.cmd)
        print("✅ Pasted!")
    else:
        print("❌ No speech detected")


def on_press(key):
    global toggle_mode, shift_held

    if key == Key.shift:
        shift_held = True

    if key == HOLD_KEY:
        if toggle_mode:
            # Option stops continuous recording
            toggle_mode = False
            threading.Thread(target=stop_recording).start()
        elif shift_held:
            # Shift+Option: start continuous recording
            toggle_mode = True
            start_recording()
            print("🔴 Continuous recording (Option to stop)")
        else:
            # Option only: hold to record
            start_recording()


def on_release(key):
    global shift_held

    if key == Key.shift:
        shift_held = False

    if key == HOLD_KEY and not toggle_mode and not shift_held:
        threading.Thread(target=stop_recording).start()


def main():
    print("=" * 50)
    print("  VOICE DICTATOR - Personal Use")
    print("=" * 50)
    print()

    # Load model in background
    load_thread = threading.Thread(target=load_model)
    load_thread.start()
    load_thread.join()

    print()
    print("🎯 Hold OPTION (⌥) to record, release to transcribe")
    print("🔴 SHIFT+OPTION to start continuous, OPTION to stop")
    print("   Press Ctrl+C to quit")
    print()

    # Start keyboard listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("\n👋 Bye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
