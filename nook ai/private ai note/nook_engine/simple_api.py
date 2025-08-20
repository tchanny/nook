"""
Simple API for embedding Nook Engine into iOS/macOS applications
Optimized for mobile devices with simplified interface
"""

import os
import json
import time
import threading
from typing import Dict, List, Optional, Callable, Union
from pathlib import Path
import logging

from .core import NookEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleNookEngine:
    """
    Simplified API for embedding Nook Engine into applications
    
    Features:
    - Easy-to-use interface
    - Mobile-optimized
    - Real-time streaming
    - Speaker diarization
    - Privacy-first (local processing)
    """
    
    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "auto",
        language: str = "en",
        optimize_for_mobile: bool = True,
        continuous_mode: bool = True,
        interruption_gap: float = 1.0
    ):
        """
        Initialize Simple Nook Engine
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cpu, gpu, auto, mobile)
            language: Language for transcription
            optimize_for_mobile: Enable mobile optimizations
            continuous_mode: Enable continuous transcription mode
            interruption_gap: Gap threshold for interruption detection (seconds)
        """
        self.model_size = model_size
        self.device = "cpu" if optimize_for_mobile else device
        self.language = language
        self.optimize_for_mobile = optimize_for_mobile
        self.continuous_mode = continuous_mode
        self.interruption_gap = interruption_gap
        
        # Initialize core engine with continuous mode
        self.engine = NookEngine(
            model_size=model_size,
            device=self.device,
            language=language,
            continuous_mode=continuous_mode,
            interruption_gap=interruption_gap
        )
        
        # State
        self.is_initialized = False
        self.is_listening = False
        self.current_session = None
        
        # Callbacks
        self.on_transcription_update: Optional[Callable] = None
        self.on_speaker_change: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Mobile optimizations
        if optimize_for_mobile:
            self._apply_mobile_optimizations()
    
    def _apply_mobile_optimizations(self):
        """Apply mobile-specific optimizations"""
        # Use smaller models for mobile
        if self.model_size in ["medium", "large"]:
            self.model_size = "base.en"
            logger.info("Mobile optimization: using base.en model")
        
        # Force CPU for mobile (better battery life)
        self.device = "cpu"
        
        # Optimize memory usage and continuous mode for mobile
        self.engine.diarizer.segment_length = 1.5  # Shorter segments
        self.engine.diarizer.min_segment_length = 0.3  # Shorter min segments
        
        # More sensitive interruption detection for mobile (faster response)
        if self.interruption_gap > 0.8:
            self.interruption_gap = 0.8
            self.engine.interruption_gap = 0.8
            logger.info("Mobile optimization: faster interruption detection (0.8s)")
        
        logger.info(f"Mobile optimization: continuous mode {'enabled' if self.continuous_mode else 'disabled'}")
    
    def initialize(self) -> bool:
        """Initialize the engine"""
        try:
            logger.info("Initializing Simple Nook Engine...")
            success = self.engine.initialize()
            
            if success:
                self.is_initialized = True
                logger.info("✅ Simple Nook Engine initialized successfully")
                return True
            else:
                logger.error("❌ Failed to initialize engine")
                return False
                
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            if self.on_error:
                self.on_error(f"Initialization failed: {e}")
            return False
    
    def start_listening(
        self,
        output_file: str = "live_transcription.json",
        enable_diarization: bool = True,
        partial_updates: bool = True,
        update_interval: float = 0.25
    ) -> bool:
        """
        Start listening to microphone in real-time
        
        Args:
            output_file: File to save results
            enable_diarization: Enable speaker separation
            partial_updates: Enable partial transcription updates
            update_interval: How often to send updates (seconds)
            
        Returns:
            True if successfully started
        """
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        try:
            logger.info("🎤 Starting real-time listening...")
            
            # Start low-latency processing
            success = self.engine.audio_processor.start_low_latency_processing(
                voice_engine=self.engine,
                output_json=output_file,
                output_jsonl=f"{output_file}.stream",
                partial_interval=update_interval,
                vad_aggressiveness=2,
                min_speech_ms=280,
                post_silence_ms=320,
                max_segment_ms=4000,
                enable_diarization=False,
            )
            
            if success:
                self.is_listening = True
                self.current_session = {
                    "start_time": time.time(),
                    "output_file": output_file,
                    "enable_diarization": enable_diarization
                }
                
                # Start monitoring thread
                self._start_monitoring_thread()
                
                logger.info("✅ Real-time listening started")
                return True
            else:
                logger.error("❌ Failed to start listening")
                return False
                
        except Exception as e:
            logger.error(f"Error starting listening: {e}")
            if self.on_error:
                self.on_error(f"Failed to start listening: {e}")
            return False
    
    def _start_monitoring_thread(self):
        """Start thread to monitor transcription updates"""
        def monitor_updates():
            stream_file = f"{self.current_session['output_file']}.stream"
            
            while self.is_listening:
                try:
                    if os.path.exists(stream_file):
                        # Read latest updates
                        with open(stream_file, 'r') as f:
                            lines = f.readlines()
                            
                        if lines:
                            # Process latest line
                            latest_line = lines[-1].strip()
                            if latest_line:
                                try:
                                    update = json.loads(latest_line)
                                    self._process_update(update)
                                except json.JSONDecodeError:
                                    continue
                    
                    time.sleep(0.5)  # Check every 500ms
                    
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    break
        
        thread = threading.Thread(target=monitor_updates, daemon=True)
        thread.start()
    
    def _process_update(self, update: Dict):
        """Process transcription update and trigger callbacks"""
        try:
            # Trigger transcription update callback
            if self.on_transcription_update:
                self.on_transcription_update(update)
            
            # Check for speaker change
            if 'speaker' in update:
                if self.on_speaker_change:
                    self.on_speaker_change(update['speaker'])
            
        except Exception as e:
            logger.error(f"Error processing update: {e}")
    
    def stop_listening(self) -> bool:
        """Stop listening to microphone"""
        try:
            if self.is_listening:
                logger.info("🛑 Stopping real-time listening...")
                
                # Stop audio processing
                self.engine.audio_processor.stop_recording()
                
                # Update state
                self.is_listening = False
                session_duration = time.time() - self.current_session['start_time']
                
                logger.info(f"✅ Listening stopped. Session duration: {session_duration:.1f}s")
                
                # Return final results
                return self._get_final_results()
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping listening: {e}")
            if self.on_error:
                self.on_error(f"Failed to stop listening: {e}")
            return False
    
    def _get_final_results(self) -> Dict:
        """Get final transcription results"""
        try:
            if self.current_session and os.path.exists(self.current_session['output_file']):
                with open(self.current_session['output_file'], 'r') as f:
                    return json.load(f)
            return {"segments": [], "speakers": [], "total_duration": 0.0}
        except Exception as e:
            logger.error(f"Error getting final results: {e}")
            return {"segments": [], "speakers": [], "total_duration": 0.0}
    
    def transcribe_file(
        self,
        audio_file: str,
        enable_diarization: bool = True,
        output_format: str = "json"
    ) -> Optional[Dict]:
        """
        Transcribe an audio file
        
        Args:
            audio_file: Path to audio file
            enable_diarization: Enable speaker separation
            output_format: Output format (json, txt, srt)
            
        Returns:
            Transcription result or None if failed
        """
        if not self.is_initialized:
            if not self.initialize():
                return None
        
        try:
            logger.info(f"🎵 Transcribing: {audio_file}")
            
            if enable_diarization:
                # Full transcription + diarization
                result = self.engine.diarize_audio(audio_file)
                logger.info("✅ Diarization completed")
            else:
                # Just transcription
                result = self.engine.transcribe_audio(audio_file)
                logger.info("✅ Transcription completed")
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            if self.on_error:
                self.on_error(f"Transcription failed: {e}")
            return None
    
    def get_latest_text(self) -> str:
        """Get the latest transcribed text"""
        try:
            if self.current_session:
                stream_file = f"{self.current_session['output_file']}.stream"
                if os.path.exists(stream_file):
                    with open(stream_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            latest = json.loads(lines[-1].strip())
                            return latest.get('text', '')
            return ""
        except Exception:
            return ""
    
    def get_speakers(self) -> List[str]:
        """Get list of detected speakers"""
        try:
            if self.current_session:
                output_file = self.current_session['output_file']
                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        data = json.load(f)
                        return data.get('speakers', [])
            return []
        except Exception:
            return []
    
    def set_callbacks(
        self,
        on_transcription_update: Optional[Callable] = None,
        on_speaker_change: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """Set callback functions for real-time updates"""
        self.on_transcription_update = on_transcription_update
        self.on_speaker_change = on_speaker_change
        self.on_error = on_error
    
    def get_status(self) -> Dict:
        """Get current engine status"""
        return {
            "is_initialized": self.is_initialized,
            "is_listening": self.is_listening,
            "model_size": self.model_size,
            "device": self.device,
            "language": self.language,
            "optimize_for_mobile": self.optimize_for_mobile,
            "session_active": self.current_session is not None
        }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.is_listening:
                self.stop_listening()
            
            if self.is_initialized:
                self.engine.cleanup()
                self.is_initialized = False
            
            logger.info("🧹 Simple Nook Engine cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Convenience functions for quick usage
def create_mobile_engine() -> SimpleNookEngine:
    """Create a mobile-optimized engine instance"""
    return SimpleNookEngine(
        model_size="tiny.en",
        optimize_for_mobile=True
    )

def create_high_quality_engine() -> SimpleNookEngine:
    """Create a high-quality engine instance"""
    return SimpleNookEngine(
        model_size="base.en",
        optimize_for_mobile=False
    )

def create_fast_engine() -> SimpleNookEngine:
    """Create a fast engine instance"""
    return SimpleNookEngine(
        model_size="tiny.en",
        optimize_for_mobile=False
    )
