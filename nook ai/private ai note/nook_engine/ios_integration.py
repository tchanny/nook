"""
iOS/macOS Integration Module for Nook Engine
Provides easy integration with Swift/SwiftUI applications
"""

import os
import json
import time
import threading
from typing import Dict, List, Optional, Callable, Union
from pathlib import Path
import logging

from .simple_api import SimpleNookEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IOSIntegrationEngine:
    """
    iOS/macOS Integration Engine
    
    Features:
    - Swift-friendly API
    - Memory optimization for mobile
    - Background processing
    - File-based communication
    - Status monitoring
    """
    
    def __init__(
        self,
        model_size: str = "tiny.en",
        optimize_for_mobile: bool = True,
        temp_dir: str = "/tmp/nook_engine",
        continuous_mode: bool = True,
        interruption_gap: float = 1.0
    ):
        """
        Initialize iOS Integration Engine
        
        Args:
            model_size: Whisper model size
            optimize_for_mobile: Enable mobile optimizations
            temp_dir: Temporary directory for communication
            continuous_mode: Enable continuous transcription mode
            interruption_gap: Gap threshold for interruption detection (seconds)
        """
        self.model_size = model_size
        self.optimize_for_mobile = optimize_for_mobile
        self.continuous_mode = continuous_mode
        self.interruption_gap = interruption_gap
        self.temp_dir = temp_dir
        self.work_dir = os.getcwd()
        self.chunks_dir = os.path.join(self.work_dir, "audio_chunks")
        self.transcripts_dir = os.path.join(self.work_dir, "transcripts")
        
        # Create temp directory
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize core engine with continuous mode
        self.engine = SimpleNookEngine(
            model_size=model_size,
            optimize_for_mobile=optimize_for_mobile,
            continuous_mode=continuous_mode,
            interruption_gap=interruption_gap
        )
        
        # State
        self.is_initialized = False
        self.is_listening = False
        self.current_session = None
        
        # Communication files
        self.status_file = os.path.join(temp_dir, "status.json")
        self.command_file = os.path.join(temp_dir, "command.json")
        self.result_file = os.path.join(temp_dir, "result.json")
        self.stream_file = os.path.join(temp_dir, "stream.jsonl")
        
        # Background thread
        self.command_monitor_thread = None
        self.should_monitor = False
        
        # Ensure folders exist and are clean on startup
        os.makedirs(self.chunks_dir, exist_ok=True)
        os.makedirs(self.transcripts_dir, exist_ok=True)
        self._purge_old_artifacts(remove_all=True)
    
    def initialize(self) -> bool:
        """Initialize the engine"""
        try:
            logger.info("🚀 Initializing iOS Integration Engine...")
            
            success = self.engine.initialize()
            if success:
                self.is_initialized = True
                self._update_status()
                self._start_command_monitor()
                # Clean any stale files from previous runs
                self._purge_old_artifacts(remove_all=True)
                logger.info("✅ iOS Integration Engine initialized")
                return True
            else:
                logger.error("❌ Failed to initialize")
                return False
                
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
    
    def _update_status(self):
        """Update status file for iOS app to read"""
        try:
            status = {
                "is_initialized": self.is_initialized,
                "is_listening": self.is_listening,
                "model_size": self.model_size,
                "optimize_for_mobile": self.optimize_for_mobile,
                "continuous_mode": self.continuous_mode,
                "interruption_gap": self.interruption_gap,
                "timestamp": time.time(),
                "session_active": self.current_session is not None
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            logger.error(f"Status update error: {e}")
    
    def _start_command_monitor(self):
        """Start monitoring for commands from iOS app"""
        self.should_monitor = True
        self.command_monitor_thread = threading.Thread(target=self._monitor_commands, daemon=True)
        self.command_monitor_thread.start()
    
    def _monitor_commands(self):
        """Monitor command file for iOS app commands"""
        while self.should_monitor:
            try:
                if os.path.exists(self.command_file):
                    # Read command
                    with open(self.command_file, 'r') as f:
                        command = json.load(f)
                    
                    # Process command
                    self._process_command(command)
                    
                    # Remove command file
                    os.remove(self.command_file)
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                logger.error(f"Command monitoring error: {e}")
                time.sleep(1)
    
    def _process_command(self, command: Dict):
        """Process command from iOS app"""
        try:
            cmd_type = command.get("type")
            
            if cmd_type == "start_listening":
                self._handle_start_listening(command)
            elif cmd_type == "stop_listening":
                self._handle_stop_listening(command)
            elif cmd_type == "transcribe_file":
                self._handle_transcribe_file(command)
            elif cmd_type == "get_status":
                self._handle_get_status(command)
            elif cmd_type == "cleanup":
                self._handle_cleanup(command)
            else:
                logger.warning(f"Unknown command type: {cmd_type}")
                
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            self._send_error(f"Command failed: {e}")
    
    def _handle_start_listening(self, command: Dict):
        """Handle start listening command"""
        try:
            if self.is_listening:
                self._send_error("Already listening")
                return
            
            # Start listening
            requested_output = command.get("output_file", "live_transcription.json")
            # Ensure output goes into temp_dir so the app can read it
            output_file = requested_output
            if not os.path.isabs(output_file):
                output_file = os.path.join(self.temp_dir, requested_output)
            success = self.engine.start_listening(
                output_file=output_file,
                enable_diarization=command.get("enable_diarization", True),
                partial_updates=command.get("partial_updates", True),
                update_interval=command.get("update_interval", 1.0)
            )
            
            if success:
                self.is_listening = True
                self.current_session = {
                    "start_time": time.time(),
                    "output_file": output_file
                }
                
                # Start stream monitoring
                self._start_stream_monitor()
                
                self._update_status()
                self._send_result({"message": "Listening started", "success": True})
                logger.info("✅ Listening started")
            else:
                self._send_error("Failed to start listening")
                
        except Exception as e:
            logger.error(f"Start listening error: {e}")
            self._send_error(f"Start listening failed: {e}")
    
    def _handle_stop_listening(self, command: Dict):
        """Handle stop listening command"""
        try:
            if not self.is_listening:
                self._send_error("Not currently listening")
                return
            
            # Stop listening
            results = self.engine.stop_listening()
            self.is_listening = False
            self.current_session = None
            
            self._update_status()
            self._send_result({
                "message": "Listening stopped",
                "success": True,
                "results": results
            })
            
            logger.info("✅ Listening stopped")
            
        except Exception as e:
            logger.error(f"Stop listening error: {e}")
            self._send_error(f"Stop listening failed: {e}")
    
    def _handle_transcribe_file(self, command: Dict):
        """Handle file transcription command"""
        try:
            audio_file = command.get("audio_file")
            if not audio_file:
                self._send_error("audio_file is required")
                return
            
            # Transcribe file
            result = self.engine.transcribe_file(
                audio_file=audio_file,
                enable_diarization=command.get("enable_diarization", True),
                output_format=command.get("output_format", "json")
            )
            
            if result:
                self._send_result({
                    "message": "Transcription completed",
                    "success": True,
                    "result": result
                })
            else:
                self._send_error("Transcription failed")
                
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            self._send_error(f"Transcription failed: {e}")
    
    def _handle_get_status(self, command: Dict):
        """Handle status request command"""
        try:
            status = self.engine.get_status()
            status.update({
                "ios_integration": {
                    "temp_dir": self.temp_dir,
                    "status_file": self.status_file,
                    "command_file": self.command_file,
                    "result_file": self.result_file,
                    "stream_file": self.stream_file
                }
            })
            
            self._send_result({
                "message": "Status retrieved",
                "success": True,
                "status": status
            })
            
        except Exception as e:
            logger.error(f"Status error: {e}")
            self._send_error(f"Status failed: {e}")
    
    def _handle_cleanup(self, command: Dict):
        """Handle cleanup command"""
        try:
            if self.is_listening:
                self.engine.stop_listening()
            
            self.engine.cleanup()
            self.is_initialized = False
            self.is_listening = False
            self.current_session = None
            
            self._update_status()
            self._send_result({
                "message": "Cleanup completed",
                "success": True
            })
            
            logger.info("🧹 Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            self._send_error(f"Cleanup failed: {e}")
    
    def _start_stream_monitor(self):
        """Start monitoring transcription stream.
        
        If low-latency mode is active, mirror ``<output>.stream`` to ``self.stream_file``.
        If low-latency stream is unavailable (fallback mode), synthesize lightweight
        JSONL updates from aggregated ``<output>.json`` so that the app UI can still
        display progressive text.
        """
        def monitor_stream():
            stream_file = f"{self.current_session['output_file']}.stream"
            agg_file = self.current_session['output_file']
            last_emitted_len = 0
            
            while self.is_listening:
                try:
                    if os.path.exists(stream_file):
                        # Read latest updates from low-latency stream
                        with open(stream_file, 'r') as f:
                            lines = f.readlines()
                        if lines:
                            with open(self.stream_file, 'w') as f:
                                f.writelines(lines)
                    else:
                        # Fallback: synthesize JSONL from aggregated JSON
                        if os.path.exists(agg_file):
                            try:
                                with open(agg_file, 'r') as f:
                                    data = json.load(f)
                                segments = data.get('segments', [])
                                if len(segments) > 0:
                                    # Emit only when new segment appears
                                    if len(segments) != last_emitted_len:
                                        last = segments[-1]
                                        payload = {
                                            "id": len(segments) - 1,
                                            "start": last.get("start", 0.0),
                                            "end": last.get("end", 0.0),
                                            "text": last.get("text", ""),
                                            "speaker": last.get("speaker", "UNKNOWN"),
                                            "is_final": True
                                        }
                                        with open(self.stream_file, 'a') as f:
                                            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
                                        last_emitted_len = len(segments)
                            except Exception as ie:
                                logger.debug(f"Fallback stream synth error: {ie}")
                    
                    time.sleep(0.1)  # Faster mirror
                except Exception as e:
                    logger.error(f"Stream monitoring error: {e}")
                    break
        
        thread = threading.Thread(target=monitor_stream, daemon=True)
        thread.start()

    def _purge_old_artifacts(self, max_age_seconds: int = 3600, remove_all: bool = False):
        """Remove old audio chunks, transcripts and temporary files.
        If remove_all=True, remove everything regardless of age.
        """
        now = time.time()
        for folder in [self.chunks_dir, self.transcripts_dir]:
            try:
                if not os.path.exists(folder):
                    continue
                for name in os.listdir(folder):
                    path = os.path.join(folder, name)
                    try:
                        if remove_all or (now - os.path.getmtime(path) > max_age_seconds):
                            if os.path.isfile(path):
                                os.remove(path)
                            else:
                                # remove empty subfolders if any
                                for root, dirs, files in os.walk(path, topdown=False):
                                    for f in files:
                                        try:
                                            os.remove(os.path.join(root, f))
                                        except Exception:
                                            pass
                                    for d in dirs:
                                        try:
                                            os.rmdir(os.path.join(root, d))
                                        except Exception:
                                            pass
                                try:
                                    os.rmdir(path)
                                except Exception:
                                    pass
                    except Exception as ie:
                        logger.debug(f"Purge skip {path}: {ie}")
            except Exception as e:
                logger.debug(f"Purge folder error {folder}: {e}")
        
        # Also remove live_transcription artifacts in work_dir
        for name in ["live_transcription.json", "live_transcription.json.stream"]:
            p = os.path.join(self.work_dir, name)
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
    
    def _send_result(self, result: Dict):
        """Send result to iOS app"""
        try:
            result["timestamp"] = time.time()
            with open(self.result_file, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.error(f"Send result error: {e}")
    
    def _send_error(self, error: str):
        """Send error to iOS app"""
        self._send_result({
            "message": error,
            "success": False,
            "error": error
        })
    
    def get_latest_transcription(self) -> str:
        """Get latest transcription text for iOS app"""
        try:
            if os.path.exists(self.stream_file):
                with open(self.stream_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        latest = json.loads(lines[-1].strip())
                        return latest.get('text', '')
            return ""
        except Exception:
            return ""
    
    def get_speakers(self) -> List[str]:
        """Get list of detected speakers for iOS app"""
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
    
    def get_status(self) -> Dict:
        """Get current engine status"""
        try:
            status = self.engine.get_status()
            status.update({
                "ios_integration": {
                    "temp_dir": self.temp_dir,
                    "status_file": self.status_file,
                    "command_file": self.command_file,
                    "result_file": self.result_file,
                    "stream_file": self.stream_file
                }
            })
            
            return status
            
        except Exception as e:
            logger.error(f"Status error: {e}")
            return {
                "error": f"Status failed: {e}",
                "ios_integration": {
                    "temp_dir": self.temp_dir,
                    "status_file": self.status_file,
                    "command_file": self.command_file,
                    "result_file": self.result_file,
                    "stream_file": self.stream_file
                }
            }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.should_monitor = False
            
            if self.is_listening:
                self.engine.stop_listening()
            
            if self.engine:
                self.engine.cleanup()
            
            # Clean up temp files
            for file_path in [self.status_file, self.command_file, self.result_file, self.stream_file]:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Purge working artifacts as well
            self._purge_old_artifacts(remove_all=True)
            
            logger.info("🧹 iOS Integration Engine cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Convenience functions for iOS integration
def create_ios_engine(
    model_size: str = "tiny.en",
    optimize_for_mobile: bool = True,
    temp_dir: str = "/tmp/nook_engine",
    continuous_mode: bool = True,
    interruption_gap: float = 0.8
) -> IOSIntegrationEngine:
    """Create an iOS-optimized engine instance with continuous transcription"""
    return IOSIntegrationEngine(
        model_size=model_size,
        optimize_for_mobile=optimize_for_mobile,
        temp_dir=temp_dir,
        continuous_mode=continuous_mode,
        interruption_gap=interruption_gap  # Faster interruption detection for mobile
    )


def create_macos_engine(
    model_size: str = "base.en",
    optimize_for_mobile: bool = False,
    temp_dir: str = "/tmp/nook_engine",
    continuous_mode: bool = True,
    interruption_gap: float = 1.0
) -> IOSIntegrationEngine:
    """Create a macOS-optimized engine instance with continuous transcription"""
    return IOSIntegrationEngine(
        model_size=model_size,
        optimize_for_mobile=optimize_for_mobile,
        temp_dir=temp_dir,
        continuous_mode=continuous_mode,
        interruption_gap=interruption_gap
    )


# Example usage for iOS app
def example_ios_usage():
    """Example of how to use from iOS app"""
    
    # 1. Create engine
    engine = create_ios_engine()
    
    # 2. Initialize
    if engine.initialize():
        print("✅ Engine ready for iOS app")
        
        # 3. iOS app can now send commands via command.json file
        # 4. Read results from result.json file
        # 5. Read real-time updates from stream.jsonl file
        # 6. Read status from status.json file
        
        # 7. Cleanup when done
        engine.cleanup()
    else:
        print("❌ Failed to initialize engine")


if __name__ == "__main__":
    example_ios_usage()
