#!/usr/bin/env python3
"""
Nook Engine - Fallback Real-time (without microphone)
Uses chunked mode with low latency
"""

from nook_engine import NookEngine
import time
import os
import json

def main():
    print("🎤 Nook Engine - Fallback Real-time (Chunked Mode)")
    print("=" * 50)
    
    # Create engine
    engine = NookEngine(
        model_size="base.en",
        language="en"
    )
    
    # Initialize
    if not engine.initialize():
        print("❌ Initialization error")
        return
    
    print("✅ Engine initialized")
    
    # Create directories
    os.makedirs("transcripts", exist_ok=True)
    os.makedirs("audio_chunks", exist_ok=True)
    
    print("\n🚀 Starting fallback mode (chunked)...")
    print("📁 Results:")
    print("  - transcripts/realtime_diarized.json (final dialogue)")
    print("  - audio_chunks/ (audio chunks)")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    # Start fallback mode (chunked)
    success = engine.process_realtime(
        output_file="transcripts/realtime_diarized.json",
        chunk_duration=3,  # 3 seconds per chunk (lower latency)
        save_audio=True
    )
    
    if not success:
        print("❌ Error starting fallback mode")
        return
    
    print("🎙️  Listening... Speak!")
    print("\n💡 In another terminal watch results:")
    print("   tail -f transcripts/realtime_diarized.json | cat")
    
    # Main loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
        engine.audio_processor.stop_recording()
        engine.cleanup()
        print("✅ Stream stopped")
        
        # Show results
        if os.path.exists("transcripts/realtime_diarized.json"):
            print("\n📊 Final dialogue:")
            try:
                with open("transcripts/realtime_diarized.json", "r", encoding="utf-8") as f:
                    result = json.load(f)
                    print(f"  Segments: {len(result.get('segments', []))}")
                    print(f"  Speakers: {', '.join(result.get('speakers', []))}")
                    print(f"  Duration: {result.get('total_duration', 0):.1f} sec")
                    
                    # Show last segments
                    segments = result.get('segments', [])
                    if segments:
                        print("\n📝 Last segments:")
                        for seg in segments[-3:]:
                            print(f"  [{seg.get('speaker', '?')}] {seg.get('text', '')}")
            except Exception as e:
                print(f"⚠️  Error reading results: {e}")

if __name__ == "__main__":
    main()
