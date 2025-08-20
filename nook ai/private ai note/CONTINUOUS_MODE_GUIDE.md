# 🔄 Continuous Transcription Mode Guide

## Overview

The **Continuous Transcription Mode** in Nook Engine creates one flowing text where speakers change only when interrupting each other. This is perfect for natural dialogue transcription and eliminates the constant speaker switching that can make transcripts hard to read.

## How It Works

### Regular Mode vs Continuous Mode

**Regular Mode:**
```
SPEAKER_00: Hello, how are you?
SPEAKER_01: I'm doing well, thank you.
SPEAKER_00: That's great to hear.
SPEAKER_01: Yes, it's been a good day.
```

**Continuous Mode:**
```
SPEAKER_00: Hello, how are you? I'm doing well, thank you. That's great to hear.
SPEAKER_01: Yes, it's been a good day.
```

### Interruption Detection

The system detects interruptions based on:
- **Time gap** between segments (configurable, default: 1 second)
- **Speaker change** with small gaps
- **Natural flow** preservation

## Usage

### Python API

```python
from nook_engine import NookEngine

# Enable continuous mode
engine = NookEngine(
    model_size="base.en",
    continuous_mode=True,      # Enable continuous mode
    interruption_gap=1.0       # 1 second gap threshold
)

# Initialize and process
engine.initialize()
result = engine.diarize_audio("dialogue.wav")

# Process results
for segment in result.segments:
    print(f"{segment['speaker']}: {segment['text']}")
```

### Command Line

```bash
# Basic continuous mode
nook-engine diarize audio.wav --continuous

# Custom interruption gap (0.5 seconds)
nook-engine diarize audio.wav --continuous --interruption-gap 0.5

# With reference voice
nook-engine diarize audio.wav --continuous --reference voice.wav
```

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `continuous_mode` | `True` | Enable/disable continuous mode |
| `interruption_gap` | `1.0` | Maximum gap in seconds to consider as interruption |

## When to Use

### ✅ Use Continuous Mode For:
- **Natural dialogues** - conversations between people
- **Interviews** - Q&A sessions
- **Podcasts** - multi-speaker content
- **Meetings** - group discussions
- **Readability** - when you want flowing text

### ❌ Use Regular Mode For:
- **Structured content** - presentations, lectures
- **Precise timing** - when exact segment timing is important
- **Analysis** - when you need detailed speaker statistics
- **Debugging** - when troubleshooting diarization issues

## Examples

### Example 1: Natural Conversation

**Input Audio:** Two people having a casual conversation

**Continuous Mode Output:**
```json
{
  "segments": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.0,
      "end": 15.2,
      "text": "Hey, how was your weekend? I went hiking and it was amazing. The weather was perfect and we saw some incredible views."
    },
    {
      "speaker": "SPEAKER_01", 
      "start": 15.2,
      "end": 28.7,
      "text": "That sounds wonderful! I stayed home and caught up on some reading. What trail did you take?"
    }
  ]
}
```

### Example 2: Interview

**Input Audio:** Interview with interruptions

**Continuous Mode Output:**
```json
{
  "segments": [
    {
      "speaker": "INTERVIEWER",
      "start": 0.0,
      "end": 12.5,
      "text": "Tell us about your background and how you got started in this field."
    },
    {
      "speaker": "GUEST",
      "start": 12.5,
      "end": 45.2,
      "text": "Well, I started as a software engineer about 10 years ago. I was always interested in AI and machine learning, so I gradually moved into that area. It's been an incredible journey."
    }
  ]
}
```

## Tips for Best Results

1. **Adjust interruption gap** based on your content:
   - `0.5s` - for fast-paced conversations
   - `1.0s` - for normal conversations (default)
   - `2.0s` - for slower, more formal discussions

2. **Use reference voices** for better speaker identification:
   ```bash
   nook-engine diarize audio.wav --continuous --reference speaker1.wav
   ```

3. **Combine with high-quality models** for better accuracy:
   ```python
   engine = NookEngine(
       model_size="medium.en",  # Better quality
       continuous_mode=True
   )
   ```

4. **Post-process if needed** for specific formatting requirements

## Troubleshooting

### Too Many Segments
- **Problem:** Still getting many small segments
- **Solution:** Increase `interruption_gap` value

### Missing Speaker Changes
- **Problem:** Speakers not changing when they should
- **Solution:** Decrease `interruption_gap` value

### Poor Quality
- **Problem:** Low transcription quality
- **Solution:** Use larger Whisper model (`medium.en` or `large.en`)

## Performance Impact

Continuous mode has minimal performance impact:
- **Processing time:** Same as regular mode
- **Memory usage:** Slightly lower (fewer segments)
- **Output size:** Smaller JSON files

## Migration from Regular Mode

If you're currently using regular mode, simply add these parameters:

```python
# Before
engine = NookEngine(model_size="base.en")

# After  
engine = NookEngine(
    model_size="base.en",
    continuous_mode=True,
    interruption_gap=1.0
)
```

Your existing code will work the same way, but with better results for dialogue transcription.
