#!/usr/bin/env python3
"""
Nook Engine CLI - Command line interface for transcription and diarization
"""

import argparse
import sys
import os
from pathlib import Path

from . import NookEngine


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Nook Engine - Local engine for speech transcription and diarization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:

  # Transcribe file
  nook-engine transcribe audio.wav

  # Diarization with speaker separation
  nook-engine diarize audio.wav

  # Real-time processing
  nook-engine realtime

  # Low-latency mode
  nook-engine stream
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Transcribe command
    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe audio file")
    transcribe_parser.add_argument("audio_file", help="Path to audio file")
    transcribe_parser.add_argument("--output", "-o", default="transcription.json", help="Output file")
    transcribe_parser.add_argument("--model", "-m", default="base.en", help="Whisper model")
    transcribe_parser.add_argument("--language", "-l", default="en", help="Language")
    
    # Diarization command
    diarize_parser = subparsers.add_parser("diarize", help="Diarization with speaker separation")
    diarize_parser.add_argument("audio_file", help="Path to audio file")
    diarize_parser.add_argument("--reference", "-r", help="Reference voice for identification")
    diarize_parser.add_argument("--output", "-o", default="dialogue.json", help="Output file")
    diarize_parser.add_argument("--model", "-m", default="base.en", help="Whisper model")
    diarize_parser.add_argument("--threshold", "-t", type=float, default=0.7, help="Diarization threshold")
    diarize_parser.add_argument("--continuous", "-c", action="store_true", help="Enable continuous transcription mode")
    diarize_parser.add_argument("--interruption-gap", "-g", type=float, default=1.0, help="Maximum gap for interruption detection (seconds)")
    
    # Real-time command
    realtime_parser = subparsers.add_parser("realtime", help="Real-time processing")
    realtime_parser.add_argument("--output", "-o", default="realtime.json", help="Output file")
    realtime_parser.add_argument("--chunk-duration", "-c", type=int, default=10, help="Chunk duration")
    realtime_parser.add_argument("--model", "-m", default="base.en", help="Whisper model")
    
    # Low-latency stream command
    stream_parser = subparsers.add_parser("stream", help="Low-latency stream (like Granola)")
    stream_parser.add_argument("--output-json", default="stream_dialogue.json", help="Final JSON")
    stream_parser.add_argument("--output-jsonl", default="stream_updates.jsonl", help="Update stream")
    stream_parser.add_argument("--model", "-m", default="base.en", help="Whisper model")
    
    # Common parameters
    for subparser in [transcribe_parser, diarize_parser, realtime_parser, stream_parser]:
        subparser.add_argument("--device", default="auto", help="Device (cpu/gpu/auto)")
        subparser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Create engine
        engine = NookEngine(
            model_size=getattr(args, 'model', 'base.en'),
            device=getattr(args, 'device', 'auto'),
            language=getattr(args, 'language', 'en'),
            diarization_threshold=getattr(args, 'threshold', 0.7),
            continuous_mode=getattr(args, 'continuous', True),
            interruption_gap=getattr(args, 'interruption_gap', 1.0)
        )
        
        if not engine.initialize():
            print("❌ Engine initialization error")
            return 1
        
        print("✅ Nook Engine initialized")
        
        # Execute command
        if args.command == "transcribe":
            return handle_transcribe(engine, args)
        elif args.command == "diarize":
            return handle_diarize(engine, args)
        elif args.command == "realtime":
            return handle_realtime(engine, args)
        elif args.command == "stream":
            return handle_stream(engine, args)
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        if 'engine' in locals():
            engine.cleanup()


def handle_transcribe(engine, args):
    """Handle transcribe command"""
    print(f"🎵 Transcribing: {args.audio_file}")
    
    result = engine.transcribe_audio(args.audio_file, "json")
    if not result:
        print("❌ Transcription error")
        return 1
    
    # Save result
    engine.save_result(result, args.output, "json")
    print(f"✅ Result saved to: {args.output}")
    
    # Show statistics
    segments = result.get('segments', [])
    print(f"📝 Segments: {len(segments)}")
    print(f"⏱️  Duration: {result.get('duration', 0):.1f} sec")
    
    return 0


def handle_diarize(engine, args):
    """Handle diarization command"""
    print(f"🎤 Diarizing: {args.audio_file}")
    
    # Show mode information
    if engine.continuous_mode:
        print(f"🔄 Continuous mode: ON (interruption gap: {engine.interruption_gap}s)")
    else:
        print("🔄 Continuous mode: OFF")
    
    result = engine.diarize_audio(args.audio_file, args.reference)
    if not result:
        print("❌ Diarization error")
        return 1
    
    # Save result
    engine.save_result(result, args.output, "json")
    print(f"✅ Result saved to: {args.output}")
    
    # Show statistics
    segments = result.get('segments', [])
    speakers = result.get('speakers', [])
    print(f"👥 Speakers: {len(speakers)}")
    print(f"📝 Segments: {len(segments)}")
    print(f"⏱️  Duration: {result.get('total_duration', 0):.1f} sec")
    
    # Show first segments
    if segments:
        print("\n📋 First segments:")
        for i, seg in enumerate(segments[:3]):
            print(f"  {i+1}. [{seg.get('speaker', '?')}] {seg.get('text', '')}")
    
    return 0


def handle_realtime(engine, args):
    """Handle real-time command"""
    print("🎙️  Starting real-time processing...")
    print(f"📁 Output file: {args.output}")
    print("⏹️  Press Ctrl+C to stop")
    
    success = engine.process_realtime(
        output_file=args.output,
        chunk_duration=args.chunk_duration,
        save_audio=True
    )
    
    if not success:
        print("❌ Error starting real-time mode")
        return 1
    
    return 0


def handle_stream(engine, args):
    """Handle low-latency stream command"""
    print("🎙️  Starting low-latency stream...")
    print(f"📁 Final file: {args.output_json}")
    print(f"📁 Update stream: {args.output_jsonl}")
    print("⏹️  Press Ctrl+C to stop")
    
    success = engine.process_realtime_low_latency(
        output_json=args.output_json,
        output_jsonl=args.output_jsonl,
        partial_interval=0.7,
        vad_aggressiveness=2
    )
    
    if not success:
        print("❌ Error starting stream")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
