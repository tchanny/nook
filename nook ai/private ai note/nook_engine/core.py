"""
Main NookEngine class - unified entry point for all operations
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict

from .transcriber import WhisperTranscriber
from .diarizer import SpeakerDiarizer
from .audio_processor import AudioProcessor


@dataclass
class TranscriptionSegment:
    """Transcription segment with metadata"""
    start: float
    end: float
    text: str
    confidence: float
    speaker: Optional[str] = None
    language: Optional[str] = None


@dataclass
class DialogueResult:
    """Dialogue diarization result"""
    segments: List[TranscriptionSegment]
    speakers: List[str]
    total_duration: float
    audio_file: str
    metadata: Dict


class NookEngine:
    """
    Main engine for speech transcription and diarization
    
    Supports:
    - Local transcription with high quality
    - Speaker separation (diarization)
    - Cross-platform (macOS/iOS)
    - Various Whisper models
    """
    
    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "auto",
        compute_type: str = "auto",
        language: str = "en",
        diarization_threshold: float = 0.7,
        interruption_gap: float = 1.0,
        continuous_mode: bool = True
    ):
        """
        Initialize the engine
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Computing device (cpu, gpu, auto)
            compute_type: Computation type (int8, float16, float32)
            language: Recognition language
            diarization_threshold: Threshold for speaker separation
            interruption_gap: Maximum gap in seconds to consider as interruption
            continuous_mode: Enable continuous transcription mode
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.diarization_threshold = diarization_threshold
        self.interruption_gap = interruption_gap
        self.continuous_mode = continuous_mode
        
        # Initialize components
        self.transcriber = WhisperTranscriber(
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            language=language
        )
        
        self.diarizer = SpeakerDiarizer(
            threshold=diarization_threshold,
            interruption_gap=interruption_gap,
            continuous_mode=continuous_mode
        )
        
        self.audio_processor = AudioProcessor()
        
        # State
        self.is_initialized = False
        self.current_session = None
        
    def initialize(self) -> bool:
        """Initialize engine and load models"""
        try:
            print("🔄 Initializing Nook Engine...")
            
            # Initialize transcriber
            if not self.transcriber.initialize():
                print("❌ Transcriber initialization error")
                return False
            
            # Initialize diarizer
            if not self.diarizer.initialize():
                print("❌ Diarizer initialization error")
                return False
            
            # Initialize audio processor (optional)
            try:
                if not self.audio_processor.initialize():
                    print("⚠️  Audio processor not initialized (microphone unavailable)")
                    print("   This is not critical for file processing")
            except Exception as e:
                print(f"⚠️  Audio processor unavailable: {e}")
                print("   This is not critical for file processing")
            
            self.is_initialized = True
            print("✅ Nook Engine successfully initialized")
            return True
            
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            return False
    
    def transcribe_audio(
        self,
        audio_file: Union[str, Path],
        output_format: str = "json"
    ) -> Optional[Dict]:
        """
        Transcribe audio file
        
        Args:
            audio_file: Path to audio file
            output_format: Output format (json, txt, srt)
            
        Returns:
            Dictionary with transcription result
        """
        if not self.is_initialized:
            if not self.initialize():
                return None
        
        try:
            print(f"🎵 Transcribing: {audio_file}")
            
            # Check file existence
            if not os.path.exists(audio_file):
                print(f"❌ File not found: {audio_file}")
                return None
            
            # Transcribe
            result = self.transcriber.transcribe(audio_file, output_format)
            
            if result:
                print(f"✅ Transcription completed")
                return result
            else:
                print("❌ Transcription error")
                return None
                
        except Exception as e:
            print(f"❌ Error during transcription: {e}")
            return None
    
    def diarize_audio(
        self,
        audio_file: Union[str, Path],
        reference_speaker: Optional[str] = None
    ) -> Optional[DialogueResult]:
        """
        Perform audio diarization with speaker separation
        
        Args:
            audio_file: Path to audio file
            reference_speaker: Path to reference voice of main speaker
            
        Returns:
            Diarization result with speaker separation
        """
        if not self.is_initialized:
            if not self.initialize():
                return None
        
        try:
            print(f"🎤 Diarizing: {audio_file}")
            
            # First transcribe
            transcription = self.transcriber.transcribe(audio_file, "json")
            if not transcription:
                print("❌ Failed to get transcription for diarization")
                return None
            
            # Perform diarization
            diarization_result = self.diarizer.diarize(
                audio_file,
                transcription,
                reference_speaker
            )
            
            if diarization_result:
                print(f"✅ Diarization completed")
                return diarization_result
            else:
                print("❌ Diarization error")
                return None
                
        except Exception as e:
            print(f"❌ Error during diarization: {e}")
            return None
    
    def process_realtime(
        self,
        output_file: str = "realtime_dialogue.json",
        chunk_duration: int = 10,
        save_audio: bool = True
    ) -> bool:
        """
        Start real-time processing
        
        Args:
            output_file: File to save results
            chunk_duration: Chunk duration in seconds
            save_audio: Whether to save audio chunks
            
        Returns:
            True if successfully started
        """
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        try:
            print(f"🎙️  Starting real-time processing...")
            print(f"📁 Output file: {output_file}")
            print(f"⏱️  Chunk duration: {chunk_duration} sec")
            print("⏹️  Press Ctrl+C to stop")
            
            # Start real-time processing
            return self.audio_processor.start_realtime_processing(
                self,
                output_file,
                chunk_duration,
                save_audio
            )
            
        except Exception as e:
            print(f"❌ Error starting real-time processing: {e}")
            return False

    def process_realtime_low_latency(
        self,
        output_json: str = "transcripts/realtime_diarized.json",
        output_jsonl: str = "transcripts/realtime_stream.jsonl",
        partial_interval: float = 1.0,
        vad_aggressiveness: int = 2,
        min_speech_ms: int = 300,
        post_silence_ms: int = 400,
        max_segment_ms: int = 8000,
    ) -> bool:
        """
        Start low-latency mode with VAD and streaming JSONL.

        - output_json: aggregated final JSON (with final segments)
        - output_jsonl: streaming JSONL (each line is an update, is_final true/false)
        - partial_interval: how often to publish intermediate segments (sec)
        - vad_aggressiveness: 0..3 (3 is more aggressive)
        - min_speech_ms: minimum speech duration to capture segment
        - post_silence_ms: silence to close segment
        - max_segment_ms: maximum duration of one segment
        """
        if not self.is_initialized:
            if not self.initialize():
                return False

        try:
            print("🎙️  Starting low-latency stream (VAD + JSONL)...")
            return self.audio_processor.start_low_latency_processing(
                voice_engine=self,
                output_json=output_json,
                output_jsonl=output_jsonl,
                partial_interval=partial_interval,
                vad_aggressiveness=vad_aggressiveness,
                min_speech_ms=min_speech_ms,
                post_silence_ms=post_silence_ms,
                max_segment_ms=max_segment_ms,
            )
        except Exception as e:
            print(f"❌ Error starting low-latency mode: {e}")
            return False
    
    def save_result(
        self,
        result: Union[Dict, DialogueResult],
        output_file: str,
        format: str = "json"
    ) -> bool:
        """
        Save result to file
        
        Args:
            result: Result to save
            output_file: Path to output file
            format: Save format (json, txt, srt)
            
        Returns:
            True if successfully saved
        """
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            
            if format == "json":
                if hasattr(result, '__dict__'):
                    data = asdict(result)
                else:
                    data = result
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            elif format == "txt":
                with open(output_file, 'w', encoding='utf-8') as f:
                    if hasattr(result, 'segments'):
                        for seg in result.segments:
                            f.write(f"[{seg.speaker or 'UNKNOWN'}] {seg.text}\n")
                    else:
                        f.write(str(result))
                        
            elif format == "srt":
                with open(output_file, 'w', encoding='utf-8') as f:
                    if hasattr(result, 'segments'):
                        for i, seg in enumerate(result.segments):
                            f.write(f"{i+1}\n")
                            f.write(f"{self._format_time(seg.start)} --> {self._format_time(seg.end)}\n")
                            f.write(f"[{seg.speaker or 'UNKNOWN'}] {seg.text}\n\n")
                    else:
                        f.write(str(result))
            
            print(f"💾 Result saved to: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False
    
    def _format_time(self, seconds: float) -> str:
        """Format time to SRT format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def get_model_info(self) -> Dict:
        """Return information about loaded models"""
        return {
            "whisper_model": self.transcriber.get_model_info(),
            "diarization_model": self.diarizer.get_model_info(),
            "devicehawk": self.device,
            "compute_type": self.compute_type,
            "language": self.language
        }
    
    def cleanup(self):
        """Clean up resources"""
        if self.transcriber:
            self.transcriber.cleanup()
        if self.diarizer:
            self.diarizer.cleanup()
        if self.audio_processor:
            self.audio_processor.cleanup()
        
        self.is_initialized = False
        print("🧹 Resources cleaned up")
