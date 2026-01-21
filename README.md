# Voice Dictator

A simple macOS menu bar app for voice-to-text using OpenAI Whisper. Hold a key to record, release to transcribe and paste.

<img width="1103" height="345" alt="Screenshot 2026-01-21 at 8 54 27 AM" src="https://github.com/user-attachments/assets/d74ff70b-73c1-4336-9424-b90678d3c70c" />


![Menu Bar](https://img.shields.io/badge/macOS-Menu%20Bar%20App-blue)

## Features

- **Hold Control (^)** to record, release to transcribe and auto-paste
- **Shift+Control** for continuous recording mode
- Menu bar icon with last 10 transcriptions
- Click any transcription to copy to clipboard
- Open history in TextEdit
- Auto language detection (works with any language)

## Requirements

- macOS (tested on macOS 14+)
- Python 3.10+
- Microphone access
- Accessibility permissions (for keyboard shortcuts)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/bertanifede/voice-dictator.git
cd voice-dictator
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Grant permissions in **System Settings > Privacy & Security**:
   - **Microphone**: Allow Terminal (or your terminal app)
   - **Accessibility**: Allow Terminal
   - **Input Monitoring**: Allow Terminal

## Usage

```bash
source venv/bin/activate
python dictator_app.py
```

Or add an alias to your `~/.zshrc`:
```bash
alias dictator="source ~/path/to/voice-dictator/venv/bin/activate && python ~/path/to/voice-dictator/dictator_app.py"
```

Then just run:
```bash
dictator
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Hold **^** (Control) | Record while held, transcribe on release |
| **⇧+^** (Shift+Control) | Start continuous recording |
| **^** (while recording) | Stop continuous recording |

## Configuration

Edit `dictator_app.py` to change:

```python
MODEL_SIZE = "medium"  # tiny, base, small, medium, large
```

| Model | Accuracy | Speed | Size |
|-------|----------|-------|------|
| tiny | ⭐ | Fastest | ~75MB |
| base | ⭐⭐ | Fast | ~140MB |
| small | ⭐⭐⭐ | Medium | ~460MB |
| medium | ⭐⭐⭐⭐ | Slow | ~1.5GB |
| large | ⭐⭐⭐⭐⭐ | Slowest | ~3GB |

## License

MIT
