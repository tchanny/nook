# 🎤 Nook Engine

**Local engine for high-quality speech transcription and diarization**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/nook-engine.svg)](https://badge.fury.io/py/nook-engine)

Nook Engine is a powerful, cross-platform speech processing engine that works **completely locally** without sending data to the cloud. Supports macOS, iOS, Linux and Windows through a unified API.

## 🎯 **Why Nook Engine?**

- 🔒 **100% Privacy** - all data stays on your device
- 🚀 **High Quality** - uses the best Whisper models
- 🎤 **Diarization** - automatic speaker separation
- ⚡ **Real-time** - processing in real-time with low latency
- 🌍 **Cross-platform** - works everywhere
- 🛠️ **Simplicity** - simple API for integration

## ✨ Features

### 🎵 Speech Transcription
- **Local Processing** - all computations performed on your device
- **High Quality** - uses the best Whisper models
- **Multiple Backends** - whisper.cpp, faster-whisper, whisper-ctranslate2
- **Auto-detection** - automatically selects the best available backend
- **Various Models** - from tiny to large for quality and speed balance

### 🎤 Diarization (Speaker Separation)
- **Automatic Separation** - detects when different people speak
- **Reference Voice** - can identify specific speakers
- **High Quality** - supports pyannote.audio, Resemblyzer
- **Smart Clustering** - automatically determines number of speakers
- **Continuous Mode** - creates one continuous text with speaker changes only on interruptions

### 🎙️ Real-time Processing
- **Microphone Recording** - support for various audio devices
- **Streaming Processing** - audio processing in chunks
- **Auto-save** - intermediate and final results
- **Cross-platform** - works on macOS, iOS, Linux, Windows

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install nook-engine

# Or install from source
git clone https://github.com/nook-ai/nook-engine.git
cd nook-engine
pip install -e .
```

### Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Simple Usage Example

```python
from nook_engine import NookEngine

# Create engine
engine = NookEngine(
    model_size="base.en",  # Whisper model
    language="en"           # Language
)

# Initialize
engine.initialize()

# Transcribe audio
transcription = engine.transcribe_audio("audio.wav")

# Diarize (separate speakers)
dialogue = engine.diarize_audio("audio.wav")

# Save result
engine.save_result(dialogue, "output.json", "json")
```

### Continuous Transcription Mode

Nook Engine now supports a **continuous transcription mode** that creates one flowing text where speakers change only when interrupting each other. This is perfect for natural dialogue transcription.

```python
from nook_engine import NookEngine

# Create engine with continuous mode
engine = NookEngine(
    model_size="base.en",
    continuous_mode=True,      # Enable continuous mode
    interruption_gap=1.0       # 1 second gap to detect interruptions
)

# Initialize and process
engine.initialize()
result = engine.diarize_audio("dialogue.wav")

# Result will have fewer segments with longer, continuous text
for segment in result.segments:
    print(f"{segment['speaker']}: {segment['text']}")
```

**Benefits of Continuous Mode:**
- 📝 **Natural Flow** - text reads like a natural conversation
- 🔄 **Fewer Segments** - reduces fragmentation
- 🎯 **Interruption Detection** - speakers change only when interrupting
- ⚙️ **Configurable** - adjust interruption gap threshold

### Command Line Interface (CLI)

```bash
# Transcribe file
nook-engine transcribe audio.wav

# Diarization with speaker separation
nook-engine diarize audio.wav

# Continuous transcription mode (recommended for dialogues)
nook-engine diarize audio.wav --continuous

# Custom interruption gap
nook-engine diarize audio.wav --continuous --interruption-gap 0.5

# Real-time processing
nook-engine realtime

# Low-latency stream (like Granola)
nook-engine stream

# Help
nook-engine --help
```

### Process Your File

```bash
# Run example
python example_usage.py
```

## 📁 Project Structure

```
nook_engine/
├── __init__.py           # Main module
├── core.py               # Main NookEngine class
├── transcriber.py        # Transcription module
├── diarizer.py           # Diarization module
└── audio_processor.py    # Audio processing module

examples/
├── example_usage.py      # Usage example
└── realtime_example.py   # Real-time example

requirements.txt           # Dependencies
README.md                 # Documentation
```

## 🔧 Configuration

### NookEngine Parameters

```python
engine = NookEngine(
    model_size="base.en",           # tiny, base, small, medium, large
    device="auto",                  # cpu, gpu, auto
    compute_type="auto",            # int8, float16, float32
    language="en",                  # Recognition language
    diarization_threshold=0.7,      # Speaker separation threshold
    continuous_mode=True,           # Enable continuous transcription
    interruption_gap=1.0            # Gap threshold for interruption detection
)
```

### Whisper Models

| Model  | Size   | Quality | Speed   | Memory |
|--------|--------|---------|---------|---------|
| tiny   | 39 MB  | ⭐⭐     | ⚡⚡⚡⚡⚡ | 💾💾    |
| base   | 74 MB  | ⭐⭐⭐    | ⚡⚡⚡⚡   | 💾💾💾  |
| small  | 244 MB | ⭐⭐⭐⭐   | ⚡⚡⚡     | 💾💾💾💾 |
| medium | 769 MB | ⭐⭐⭐⭐⭐  | ⚡⚡       | 💾💾💾💾💾 |
| large  | 1550 MB| ⭐⭐⭐⭐⭐  | ⚡         | 💾💾💾💾💾💾 |

## 🎯 Usage Examples

### 1. File Transcription

```python
# Simple transcription
result = engine.transcribe_audio("audio.wav", "json")
print(f"Text: {result['text']}")

# Save in different formats
engine.save_result(result, "output.json", "json")
engine.save_result(result, "output.txt", "txt")
engine.save_result(result, "output.srt", "srt")
```

### 2. Dialogue Diarization

```python
# Speaker separation
dialogue = engine.diarize_audio("audio.wav")

# Analyze result
for segment in dialogue.segments:
    print(f"[{segment.speaker}] {segment.text}")
    print(f"Time: {segment.start:.1f}s - {segment.end:.1f}s")
```

### 3. Real-time Processing

```python
# Start microphone recording
engine.process_realtime(
    output_file="live_dialogue.json",
    chunk_duration=10,  # 10 seconds per chunk
    save_audio=True     # Save audio files
)

# Stop
engine.audio_processor.stop_recording()
```

### 4. Working with Reference Voice

```python
# Diarization with specific speaker identification
dialogue = engine.diarize_audio(
    "audio.wav",
    reference_speaker="my_voice.wav"  # Reference voice
)

# Result will contain USER/OTHER labels
```

## 🔍 Implementation Details

### Transcriber

- **whisper.cpp** - fast C++ implementation for CPU
- **faster-whisper** - optimized version for GPU/CPU
- **whisper-ctranslate2** - alternative optimization

### Diarizer

- **pyannote.audio** - highest quality (requires token)
- **Resemblyzer** - local processing without external dependencies
- **speaker-diarization** - alternative algorithm

### Audio Processor

- **sounddevice** - recommended for macOS
- **pyaudio** - cross-platform
- **av** - for audio decoding

## 📊 Output Formats

### JSON (main)

```json
{
  "segments": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.0,
      "end": 2.5,
      "text": "Hello, how are you?",
      "confidence": 0.95
    }
  ],
  "speakers": ["SPEAKER_00", "SPEAKER_01"],
  "total_duration": 30.5,
  "metadata": {
    "method": "resemblyzer",
    "threshold": 0.7
  }
}
```

### TXT (readable)

```
[SPEAKER_00] Hello, how are you?
[SPEAKER_01] I'm fine, thank you!
```

### SRT (subtitles)

```
1
00:00:00,000 --> 00:00:02,500
[SPEAKER_00] Hello, how are you?

2
00:00:02,500 --> 00:00:05,000
[SPEAKER_01] I'm fine, thank you!
```

## 🚀 Performance

### Optimization for Different Devices

- **macOS Intel** - uses whisper.cpp with optimizations
- **macOS Apple Silicon** - automatically uses MPS (Metal Performance Shaders)
- **iOS** - optimized models and computations
- **Linux** - CUDA support for GPU acceleration

### Quality Recommendations

- **Fast processing**: `model_size="tiny"` or `"base"`
- **High quality**: `model_size="small"` or `"medium"`
- **Maximum quality**: `model_size="large"`

## 🔧 Troubleshooting

### Common Issues

1. **Initialization Error**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Audio Issues**
   ```python
   # Check available devices
   devices = engine.audio_processor.get_audio_devices()
   print(devices)
   ```

3. **Low Diarization Quality**
   ```python
   # Reduce threshold
   engine = NookEngine(diarization_threshold=0.6)
   ```

### Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for Whisper
- Resemblyzer for diarization
- pyannote.audio for high quality
- Open source community

---

**🎯 Project Goal**: Create a local, high-quality speech processing engine that can be easily integrated into any applications.

**💡 Development Ideas**: 
- Support for more languages
- Web interface
- REST API
- Docker containers
- Mobile applications
