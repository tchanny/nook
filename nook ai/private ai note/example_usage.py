#!/usr/bin/env python3
"""
Example usage of Nook Engine for processing reference_user.wav
"""

import os
import sys
from pathlib import Path

# Add module path
sys.path.append(str(Path(__file__).parent))

from nook_engine import NookEngine


def main():
    """Main example function"""
    
    print("🎤 Nook Engine - Usage Example")
    print("=" * 50)
    
    # Check for audio file
    audio_file = "reference_user.wav"
    if not os.path.exists(audio_file):
        print(f"❌ File {audio_file} not found!")
        print("Make sure the file is in the current directory")
        return
    
    # Create engine instance
    print("🚀 Initializing Nook Engine...")
    engine = NookEngine(
        model_size="base.en",  # Can be changed to "small.en", "medium.en" for better quality
        device="auto",          # Auto-detect device
        compute_type="auto",    # Auto-detect computation type
        language="en",          # English language
        diarization_threshold=0.7  # Threshold for speaker separation
    )
    
    # Initialize engine
    if not engine.initialize():
        print("❌ Voice Engine initialization error")
        return
    
    print("✅ Nook Engine successfully initialized")
    
    # Show model information
    print("\n📊 Model information:")
    model_info = engine.get_model_info()
    for key, value in model_info.items():
        print(f"  {key}: {value}")
    
    # Step 1: Transcription
    print("\n🎵 Step 1: Audio transcription...")
    transcription = engine.transcribe_audio(audio_file, "json")
    
    if not transcription:
        print("❌ Transcription error")
        return
    
    print(f"✅ Transcription completed")
    print(f"📝 Number of segments: {len(transcription.get('segments', []))}")
    
    # Save transcription result
    engine.save_result(transcription, "reference_user_transcription.json", "json")
    
    # Step 2: Diarization with speaker separation
    print("\n🎤 Step 2: Diarization (speaker separation)...")
    
    # Use reference voice if available
    reference_speaker = audio_file  # Can specify separate file with reference voice
    
    diarization_result = engine.diarize_audio(audio_file, reference_speaker)
    
    if not diarization_result:
        print("❌ Diarization error")
        return
    
    print(f"✅ Diarization completed")
    print(f"👥 Speakers found: {len(diarization_result.get('speakers', []))}")
    print(f"📊 Total duration: {diarization_result.get('total_duration', 0):.2f} sec")
    
    # Save diarization result
    engine.save_result(diarization_result, "reference_user_dialogue.json", "json")
    
    # Show first few segments
    print("\n📋 First 5 dialogue segments:")
    segments = diarization_result.get('segments', [])
    for i, segment in enumerate(segments[:5]):
        print(f"{i+1}. [{segment['speaker']}] ({segment['start']:.1f}s - {segment['end']:.1f}s): {segment['text']}")
    
    # Save in various formats
    print("\n💾 Saving results...")
    
    # JSON format (complete)
    engine.save_result(diarization_result, "reference_user_dialogue.json", "json")
    
    # TXT format (readable)
    engine.save_result(diarization_result, "reference_user_dialogue.json", "txt")
    
    # SRT format (subtitles)
    engine.save_result(diarization_result, "reference_user_dialogue.json", "srt")
    
    print("✅ All results saved")
    
    # Show statistics
    print("\n📊 Processing statistics:")
    print(f"  Audio file: {audio_file}")
    print(f"  Duration: {diarization_result.get('total_duration', 0):.2f} sec")
    print(f"  Segments: {len(segments)}")
    print(f"  Speakers: {', '.join(diarization_result.get('speakers', []))}")
    print(f"  Diarization method: {diarization_result.get('metadata', {}).get('method', 'unknown')}")
    
    # Clean up resources
    print("\n🧹 Cleaning up resources...")
    engine.cleanup()
    
    print("\n🎉 Processing completed successfully!")
    print("📁 Results saved to:")
    print("  - reference_user_transcription.json (transcription)")
    print("  - reference_user_dialogue.json (diarization)")
    print("  - reference_user_dialogue.txt (text)")
    print("  - reference_user_dialogue.srt (subtitles)")


def process_realtime_example():
    """Real-time processing example"""
    
    print("\n🎙️  Real-time processing example")
    print("=" * 50)
    
    # Create engine
    engine = NookEngine(
        model_size="base.en",
        device="auto",
        language="en"
    )
    
    if not engine.initialize():
        print("❌ Initialization error")
        return
    
    print("✅ Engine initialized")
    print("🎤 To start real-time processing use:")
    print("   engine.process_realtime()")
    print("⏹️  Press Ctrl+C to stop")
    
    # Cleanup
    engine.cleanup()


if __name__ == "__main__":
    try:
        main()
        
        # Show real-time example
        process_realtime_example()
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
