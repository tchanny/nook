#!/usr/bin/env python3
"""
Example of continuous transcription mode
This mode creates one continuous text where speakers change only when interrupting each other
"""

import sys
import json
from pathlib import Path

# Add the nook_engine to path
sys.path.append(str(Path(__file__).parent / "nook_engine"))

from nook_engine import NookEngine

def example_continuous_transcription():
    """Example of continuous transcription"""
    
    print("🎤 Nook Engine - Continuous Transcription Example")
    print("=" * 50)
    
    # Initialize engine with continuous mode
    engine = NookEngine(
        model_size="base.en",
        continuous_mode=True,  # Enable continuous mode
        interruption_gap=1.0   # 1 second gap to detect interruptions
    )
    
    # Initialize
    print("🔄 Initializing engine...")
    if not engine.initialize():
        print("❌ Failed to initialize engine")
        return
    
    print("✅ Engine initialized successfully")
    print(f"🔄 Continuous mode: {'ON' if engine.continuous_mode else 'OFF'}")
    print(f"⏱️  Interruption gap: {engine.interruption_gap}s")
    
    # Example audio file (replace with your file)
    audio_file = "example_dialogue.wav"
    
    if not Path(audio_file).exists():
        print(f"⚠️  Audio file not found: {audio_file}")
        print("Please provide an audio file with dialogue to test")
        return
    
    print(f"\n🎵 Processing: {audio_file}")
    
    # Perform diarization with continuous mode
    result = engine.diarize_audio(audio_file)
    
    if not result:
        print("❌ Failed to process audio")
        return
    
    print("\n✅ Processing completed!")
    print(f"📊 Total duration: {result.total_duration:.2f}s")
    print(f"👥 Speakers detected: {result.metadata.get('speakers', [])}")
    
    # Display results
    print("\n📝 Continuous Transcription:")
    print("-" * 50)
    
    for i, segment in enumerate(result.segments):
        print(f"\n{i+1}. {segment['speaker']} ({segment['start']:.1f}s - {segment['end']:.1f}s):")
        print(f"   {segment['text']}")
    
    # Save result
    output_file = "continuous_transcription.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'segments': result.segments,
            'speakers': result.metadata.get('speakers', []),
            'total_duration': result.total_duration,
            'metadata': result.metadata
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Result saved to: {output_file}")
    
    # Show comparison with regular mode
    print("\n🔄 Comparison with regular mode:")
    print("-" * 30)
    
    # Create engine with regular mode
    regular_engine = NookEngine(
        model_size="base.en",
        continuous_mode=False  # Regular mode
    )
    
    if regular_engine.initialize():
        regular_result = regular_engine.diarize_audio(audio_file)
        if regular_result:
            print(f"Regular mode segments: {len(regular_result.segments)}")
            print(f"Continuous mode segments: {len(result.segments)}")
            print(f"Reduction: {len(regular_result.segments) - len(result.segments)} segments")
    
    engine.cleanup()

if __name__ == "__main__":
    example_continuous_transcription()
