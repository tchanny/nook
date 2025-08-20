#!/usr/bin/env python3
"""
Demo script showing the difference between regular and continuous transcription modes
"""

import sys
import json
from pathlib import Path

# Add the nook_engine to path
sys.path.append(str(Path(__file__).parent / "nook_engine"))

from nook_engine import NookEngine

def demo_continuous_mode():
    """Demonstrate continuous vs regular mode"""
    
    print("🎤 Nook Engine - Continuous Mode Demo")
    print("=" * 50)
    
    # Test audio file
    audio_file = "mic_test.wav"
    
    if not Path(audio_file).exists():
        print(f"⚠️  Audio file not found: {audio_file}")
        print("Please provide an audio file to test")
        return
    
    print(f"🎵 Using audio file: {audio_file}")
    
    # Test 1: Regular mode
    print("\n" + "="*30)
    print("🔄 TEST 1: REGULAR MODE")
    print("="*30)
    
    regular_engine = NookEngine(
        model_size="base.en",
        continuous_mode=False  # Regular mode
    )
    
    if regular_engine.initialize():
        regular_result = regular_engine.diarize_audio(audio_file)
        if regular_result:
            print(f"✅ Regular mode completed")
            print(f"📊 Segments: {len(regular_result.get('segments', []))}")
            print(f"👥 Speakers: {regular_result.get('speakers', [])}")
            
            # Show segments
            segments = regular_result.get('segments', [])
            for i, seg in enumerate(segments):
                print(f"  {i+1}. [{seg['speaker']}] {seg['text']}")
        else:
            print("❌ Regular mode failed")
        
        regular_engine.cleanup()
    
    # Test 2: Continuous mode
    print("\n" + "="*30)
    print("🔄 TEST 2: CONTINUOUS MODE")
    print("="*30)
    
    continuous_engine = NookEngine(
        model_size="base.en",
        continuous_mode=True,      # Continuous mode
        interruption_gap=1.0       # 1 second gap
    )
    
    if continuous_engine.initialize():
        continuous_result = continuous_engine.diarize_audio(audio_file)
        if continuous_result:
            print(f"✅ Continuous mode completed")
            print(f"📊 Segments: {len(continuous_result.get('segments', []))}")
            print(f"👥 Speakers: {continuous_result.get('speakers', [])}")
            
            # Show segments
            segments = continuous_result.get('segments', [])
            for i, seg in enumerate(segments):
                print(f"  {i+1}. [{seg['speaker']}] {seg['text']}")
        else:
            print("❌ Continuous mode failed")
        
        continuous_engine.cleanup()
    
    # Comparison
    print("\n" + "="*30)
    print("📊 COMPARISON")
    print("="*30)
    
    if 'regular_result' in locals() and 'continuous_result' in locals():
        regular_segments = len(regular_result.get('segments', []))
        continuous_segments = len(continuous_result.get('segments', []))
        
        print(f"Regular mode segments: {regular_segments}")
        print(f"Continuous mode segments: {continuous_segments}")
        
        if continuous_segments < regular_segments:
            reduction = regular_segments - continuous_segments
            print(f"✅ Reduction: {reduction} segments ({reduction/regular_segments*100:.1f}% fewer)")
        elif continuous_segments == regular_segments:
            print("ℹ️  Same number of segments (likely single speaker)")
        else:
            print("⚠️  Continuous mode has more segments (unusual)")
    
    print("\n" + "="*30)
    print("💡 EXPLANATION")
    print("="*30)
    print("• Regular mode: Creates separate segments for each speaker change")
    print("• Continuous mode: Merges segments of the same speaker")
    print("• Interruption detection: Speakers change only when interrupting")
    print("• Result: More natural, readable transcriptions")

if __name__ == "__main__":
    demo_continuous_mode()
