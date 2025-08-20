#!/usr/bin/env python3
"""
Nook Engine - Low Latency Real-time Streaming
Starts low-latency stream (like Granola)
"""

from nook_engine import NookEngine
import time
import os
import json

def main():
    print("🎤 Nook Engine - Low Latency Real-time Streaming")
    print("=" * 50)
    
    # Create engine
    engine = NookEngine(
        model_size="base.en",  # Can be changed to "small.en" for better quality
        language="en"
    )
    
    # Initialize
    if not engine.initialize():
        print("❌ Initialization error")
        return
    
    print("✅ Engine initialized")
    
    # Show available devices
    devices = engine.audio_processor.get_audio_devices()
    if devices:
        print(f"\n🎧 Found {len(devices)} audio devices:")
        for device in devices[:3]:
            print(f"  [{device['id']}] {device['name']} (inputs: {device['max_inputs']})")
        
        # Select first device with inputs
        input_devices = [d for d in devices if d['max_inputs'] > 0]
        if input_devices:
            engine.audio_processor.set_audio_device(input_devices[0]['id'])
            print(f"✅ Selected device: {input_devices[0]['name']}")
        else:
            print("⚠️  No devices with inputs")
    else:
        print("⚠️  No audio devices found")
    
    # Create directories
    os.makedirs("transcripts", exist_ok=True)
    os.makedirs("audio_chunks", exist_ok=True)
    
    print("\n🚀 Starting low-latency stream...")
    print("📁 Results:")
    print("  - transcripts/live_stream.jsonl (update stream)")
    print("  - transcripts/live_dialogue.json (final dialogue)")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    # Start low-latency mode
    success = engine.process_realtime_low_latency(
        output_json="transcripts/live_dialogue.json",
        output_jsonl="transcripts/live_stream.jsonl",
        partial_interval=0.7,      # Updates every 0.7 sec
        vad_aggressiveness=2,      # VAD aggressiveness (0-3)
        min_speech_ms=250,         # Minimum speech for segment
        post_silence_ms=300,       # Silence to close segment
        max_segment_ms=8000        # Maximum segment length
    )
    
    if not success:
        print("❌ Error starting stream")
        return
    
    print("🎙️  Listening... Speak!")
    print("\n💡 In another terminal watch the stream:")
    print("   tail -f transcripts/live_stream.jsonl | cat")
    
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
        if os.path.exists("transcripts/live_dialogue.json"):
            print("\n📊 Final dialogue:")
            try:
                with open("transcripts/live_dialogue.json", "r", encoding="utf-8") as f:
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
