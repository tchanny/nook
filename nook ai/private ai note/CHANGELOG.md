# 📝 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CLI interface for command line
- Support for various output formats (JSON, TXT, SRT)
- Automatic detection of best available backend
- Fallback mode for cases without microphone

### Changed
- Renamed from Voice Engine to Nook Engine
- Improved initialization error handling
- Optimized real-time mode performance

### Fixed
- Fixed float16 compatibility on some devices
- Improved handling of cases without available audio devices

## [1.0.0] - 2024-01-XX

### Added
- 🎤 **Main NookEngine** - unified API for all operations
- 🎵 **Speech Transcription** - support for all Whisper models
- 👥 **Diarization** - automatic speaker separation
- ⚡ **Real-time Processing** - microphone recording in real-time
- 🚀 **Low-latency Stream** - minimal latency mode (like Granola)
- 🌍 **Cross-platform** - support for macOS, iOS, Linux, Windows
- 🔒 **100% Privacy** - all computations local

### Technical Features
- **Multiple Backends**: whisper.cpp, faster-whisper, whisper-ctranslate2
- **Auto-detection**: automatic selection of best available backend
- **Diarization**: Resemblyzer, pyannote.audio, speaker-diarization
- **Audio Processing**: sounddevice, pyaudio, av
- **Voice Activity Detection**: webrtcvad for real-time mode
- **Modular Architecture**: easily extensible code

### Supported Models
- **Whisper**: tiny, base, small, medium, large
- **Languages**: English (en), with expansion capability
- **Devices**: CPU, GPU (CUDA), Auto-detection

### Output Formats
- **JSON**: complete structure with metadata
- **TXT**: readable text
- **SRT**: subtitles
- **JSONL**: streaming updates for real-time

---

## 🔗 Links

- [GitHub Repository](https://github.com/nook-ai/nook-engine)
- [Documentation](https://github.com/nook-ai/nook-engine#readme)
- [Issues](https://github.com/nook-ai/nook-engine/issues)
- [Releases](https://github.com/nook-ai/nook-engine/releases)
