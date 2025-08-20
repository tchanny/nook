"""
Transcriber module - responsible for converting speech to text
Supports various backends: whisper.cpp, whisper-ctranslate2, faster-whisper
"""

import os
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Whisper-based transcriber with support for various backends
    """
    
    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "auto",
        compute_type: str = "auto",
        language: str = "en",
        backend: str = "auto"
    ):
        """
        Initialize transcriber
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device (cpu, gpu, auto)
            compute_type: Computation type (int8, float16, float32)
            language: Recognition language
            backend: Transcription backend
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.backend = backend
        
        # Auto-detect backend
        if backend == "auto":
            self.backend = self._detect_best_backend()
        
        # State
        self.is_initialized = False
        self.model_path = None
        self.backend_instance = None
        
        # Model paths
        self.models_dir = self._get_models_directory()
        
        logger.info(f"Initializing WhisperTranscriber: {self.backend}, model: {model_size}")
    
    def _detect_best_backend(self) -> str:
        """Auto-detect best available backend"""
        # Check whisper.cpp
        if self._check_whisper_cpp():
            return "whisper_cpp"
        
        # Check faster-whisper
        if self._check_faster_whisper():
            return "faster_whisper"
        
        # Check whisper-ctranslate2
        if self._check_whisper_ctranslate2():
            return "whisper_ctranslate2"
        
        # Fallback to whisper.cpp
        logger.warning("No backend found, using whisper.cpp")
        return "whisper_cpp"
    
    def _check_whisper_cpp(self) -> bool:
        """Check whisper.cpp availability"""
        try:
            # Check for whisper.cpp
            whisper_cli = self._get_whisper_cpp_path()
            if whisper_cli and os.path.exists(whisper_cli):
                # Check functionality
                result = subprocess.run([whisper_cli, "--help"], 
                                     capture_output=True, text=True)
                return result.returncode == 0
        except Exception:
            pass
        return False
    
    def _check_faster_whisper(self) -> bool:
        """Check faster-whisper availability"""
        try:
            import faster_whisper
            return True
        except ImportError:
            return False
    
    def _check_whisper_ctranslate2(self) -> bool:
        """Check whisper-ctranslate2 availability"""
        try:
            import whisper_ctranslate2
            return True
        except ImportError:
            return False
    
    def _get_models_directory(self) -> str:
        """Get path to models directory"""
        # Priority: local directory, then system
        local_models = "./whisper.cpp/models"
        if os.path.exists(local_models):
            return local_models
        
        # System paths
        system_paths = [
            "~/.cache/whisper",
            "/usr/local/share/whisper",
            "/opt/whisper/models"
        ]
        
        for path in system_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                return expanded_path
        
        return local_models
    
    def _get_whisper_cpp_path(self) -> Optional[str]:
        """Get path to whisper.cpp CLI"""
        # Check various possible paths
        possible_paths = [
            "./whisper.cpp/build/bin/whisper-cli",
            "./whisper.cpp/build/bin/whisper",
            "./whisper.cpp/main",
            "whisper-cli",
            "whisper"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def initialize(self) -> bool:
        """Initialize transcriber and load model"""
        try:
            logger.info(f"Initializing backend: {self.backend}")
            
            if self.backend == "whisper_cpp":
                return self._init_whisper_cpp()
            elif self.backend == "faster_whisper":
                return self._init_faster_whisper()
            elif self.backend == "whisper_ctranslate2":
                return self._init_whisper_ctranslate2()
            else:
                logger.error(f"Unknown backend: {self.backend}")
                return False
                
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
    
    def _init_whisper_cpp(self) -> bool:
        """Initialize whisper.cpp"""
        try:
            # Check for whisper.cpp
            whisper_cli = self._get_whisper_cpp_path()
            if not whisper_cli:
                logger.error("whisper.cpp not found")
                return False
            
            # Check for model
            model_path = os.path.join(self.models_dir, f"ggml-{self.model_size}.bin")
            if not os.path.exists(model_path):
                logger.warning(f"Model not found: {model_path}")
                # Try to find alternative model
                model_path = self._find_alternative_model()
                if not model_path:
                    logger.error("No suitable model found")
                    return False
            
            self.model_path = model_path
            self.is_initialized = True
            logger.info(f"whisper.cpp initialized, model: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"whisper.cpp initialization error: {e}")
            return False
    
    def _init_faster_whisper(self) -> bool:
        """Initialize faster-whisper"""
        try:
            import faster_whisper
            
            # Determine device
            device = "cuda" if self.device == "gpu" else "cpu"
            # Force int8 for lowest latency on CPU
            compute_type = "int8"
            
            # Load model
            self.backend_instance = faster_whisper.WhisperModel(
                model_size_or_path=self.model_size,
                device=device,
                compute_type=compute_type
            )
            
            self.is_initialized = True
            logger.info(f"faster-whisper initialized, model: {self.model_size}")
            return True
            
        except Exception as e:
            logger.error(f"faster-whisper initialization error: {e}")
            return False
    
    def _init_whisper_ctranslate2(self) -> bool:
        """Initialize whisper-ctranslate2"""
        try:
            import whisper_ctranslate2
            
            # Determine device
            device = "cuda" if self.device == "gpu" else "cpu"
            compute_type = self.compute_type if self.compute_type != "auto" else "float32"
            
            # Load model
            self.backend_instance = whisper_ctranslate2.WhisperModel(
                model_size_or_path=self.model_size,
                device=device,
                compute_type=compute_type
            )
            
            self.is_initialized = True
            logger.info(f"whisper-ctranslate2 initialized, model: {self.model_size}")
            return True
            
        except Exception as e:
            logger.error(f"whisper-ctranslate2 initialization error: {e}")
            return False
    
    def _find_alternative_model(self) -> Optional[str]:
        """Find alternative model if main one is not found"""
        # Look for any available model
        if os.path.exists(self.models_dir):
            for file in os.listdir(self.models_dir):
                if file.endswith('.bin') and 'ggml' in file:
                    return os.path.join(self.models_dir, file)
        
        return None
    
    def transcribe(
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
            if self.backend == "whisper_cpp":
                return self._transcribe_whisper_cpp(audio_file, output_format)
            elif self.backend == "faster_whisper":
                return self._transcribe_faster_whisper(audio_file, output_format)
            elif self.backend == "whisper_ctranslate2":
                return self._transcribe_ctranslate2(audio_file, output_format)
            else:
                logger.error(f"Unknown backend: {self.backend}")
                return None
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def _transcribe_whisper_cpp(
        self,
        audio_file: Union[str, Path],
        output_format: str
    ) -> Optional[Dict]:
        """Transcription via whisper.cpp"""
        try:
            whisper_cli = self._get_whisper_cpp_path()
            
            # Build command
            cmd = [
                whisper_cli,
                "-m", self.model_path,
                "-f", str(audio_file),
                "--language", self.language
            ]
            
            # Add flags for JSON output
            if output_format == "json":
                cmd.extend(["--output-json"])
            elif output_format == "txt":
                cmd.extend(["--output-txt"])
            elif output_format == "srt":
                cmd.extend(["--output-srt"])
            
            # Start process
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Process result
            if output_format == "json":
                # Look for JSON file
                base_name = Path(audio_file).stem
                json_file = f"{base_name}.json"
                
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    logger.error(f"JSON file not found: {json_file}")
                    return None
            else:
                # For text formats return stdout content
                return {
                    "text": result.stdout.strip(),
                    "format": output_format,
                    "audio_file": str(audio_file)
                }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"whisper.cpp error: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"whisper.cpp transcription error: {e}")
            return None
    
    def _transcribe_faster_whisper(
        self,
        audio_file: Union[str, Path],
        output_format: str
    ) -> Optional[Dict]:
        """Transcription via faster-whisper"""
        try:
            # Transcribe
            kwargs = {
                "beam_size": 1,
                "temperature": 0.0,
                "best_of": 1,
                "vad_filter": True,
            }
            lang = self.language or "en"
            segments, info = self.backend_instance.transcribe(
                str(audio_file),
                language=lang,
                condition_on_previous_text=False,
                **kwargs,
            )
            
            # Build result
            result = {
                "language": info.language,
                "language_probability": info.language_probability,
                "segments": []
            }
            
            for segment in segments:
                result["segments"].append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "avg_logprob": segment.avg_logprob,
                    "compression_ratio": segment.compression_ratio,
                    "no_speech_prob": segment.no_speech_prob
                })
            
            return result
            
        except Exception as e:
            logger.error(f"faster-whisper transcription error: {e}")
            return None
    
    def _transcribe_ctranslate2(
        self,
        audio_file: Union[str, Path],
        output_format: str
    ) -> Optional[Dict]:
        """Transcription via whisper-ctranslate2"""
        try:
            # Transcribe
            segments, info = self.backend_instance.transcribe(
                str(audio_file),
                language=self.language
            )
            
            # Build result
            result = {
                "language": info.language,
                "segments": []
            }
            
            for segment in segments:
                result["segments"].append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"whisper-ctranslate2 transcription error: {e}")
            return None
    
    def get_model_info(self) -> Dict:
        """Return model information"""
        return {
            "backend": self.backend,
            "model_size": self.model_size,
            "model_path": self.model_path,
            "device": self.device,
            "compute_type": self.compute_type,
            "language": self.language,
            "is_initialized": self.is_initialized
        }
    
    def cleanup(self):
        """Clean up resources"""
        if self.backend_instance:
            del self.backend_instance
            self.backend_instance = None
        
        self.is_initialized = False
        logger.info("Transcriber resources cleaned up")
