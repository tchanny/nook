#!/usr/bin/env python3
"""
Test script for continuous transcription mode
"""

import sys
import os
from pathlib import Path

# Add the nook_engine to path
sys.path.append(str(Path(__file__).parent / "nook_engine"))

from nook_engine import NookEngine

def test_continuous_transcription():
    """Test continuous transcription mode"""
    
    # Initialize engine with continuous mode
    engine = NookEngine(
        model_size="base.en",
        continuous_mode=True,
        interruption_gap=1.0
    )
    
    # Initialize
    if not engine.initialize():
        print("❌ Failed to initialize engine")
        return
    
    # Test with audio file if available
    test_audio = "mic_test.wav"  # Use available test file
    
    if os.path.exists(test_audio):
        print(f"🎤 Testing continuous transcription with: {test_audio}")
        
        # Perform diarization
        result = engine.diarize_audio(test_audio)
        
        if result:
            print("✅ Continuous transcription completed!")
            print(f"📊 Total duration: {result.get('total_duration', 0):.2f}s")
            print(f"👥 Speakers detected: {result.get('speakers', [])}")
            
            # Print segments
            print("\n📝 Transcription segments:")
            segments = result.get('segments', [])
            for i, segment in enumerate(segments):
                print(f"\n{i+1}. {segment['speaker']} ({segment['start']:.1f}s - {segment['end']:.1f}s):")
                print(f"   {segment['text']}")
        else:
            print("❌ Failed to process audio")
    else:
        print(f"⚠️  Test audio file not found: {test_audio}")
        print("Please provide a test audio file to test the functionality")

if __name__ == "__main__":
    test_continuous_transcription()
