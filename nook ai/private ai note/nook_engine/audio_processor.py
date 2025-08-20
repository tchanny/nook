"""
Audio processor module - responsible for microphone operation and real-time processing
Supports various audio backends: sounddevice, pyaudio, av

Added low-latency mode with VAD and streaming output (JSONL):
- Writes intermediate (is_final=false) and final (is_final=true) dialogue updates
- Updates aggregated JSON by merging stable segments
"""

import os
import time
import threading
import wave
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable
import logging
import json
import queue
from collections import deque

try:
    import webrtcvad  # For VAD in low-latency mode
    _HAS_WEBRTCVAD = True
except Exception:
    _HAS_WEBRTCVAD = False

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Audio processor for microphone operation and real-time processing
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration: float = 10.0,
        backend: str = "auto"
    ):
        """
        Initialize audio processor
        
        Args:
            sample_rate: Sampling rate
            channels: Number of channels
            chunk_duration: Chunk duration in seconds
            backend: Audio backend (auto, sounddevice, pyaudio, av)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.backend = backend
        
        # Auto-detect backend
        if backend == "auto":
            self.backend = self._detect_best_backend()
        
        # State
        self.is_initialized = False
        self.is_recording = False
        self.audio_backend = None
        
        # Recording parameters
        self.chunk_samples = int(sample_rate * chunk_duration)
        self.audio_buffer = []
        self.current_chunk = []
        
        # Callbacks
        self.on_chunk_ready: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        # Real-time (low-latency) state
        self._stream: Optional[object] = None
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._frames_deque: deque[bytes] = deque(maxlen=int(sample_rate * 10 // 320))  # ~10s @ 20ms frames
        self._segment_queue: "queue.Queue[dict]" = queue.Queue()
        self._sequence_id = 0
        
        logger.info(f"Initializing AudioProcessor: {self.backend}, SR: {sample_rate}")
    
    def _detect_best_backend(self) -> str:
        """Auto-detect best available audio backend"""
        # Check sounddevice (recommended for macOS)
        if self._check_sounddevice():
            return "sounddevice"
        
        # Check pyaudio
        if self._check_pyaudio():
            return "pyaudio"
        
        # Check av
        if self._check_av():
            return "av"
        
        # Fallback to sounddevice
        logger.warning("No audio backend found, using sounddevice")
        return "sounddevice"
    
    def _check_sounddevice(self) -> bool:
        """Check sounddevice availability"""
        try:
            import sounddevice as sd
            # Check available devices
            devices = sd.query_devices()
            return len(devices) > 0
        except ImportError:
            return False
    
    def _check_pyaudio(self) -> bool:
        """Check pyaudio availability"""
        try:
            import pyaudio
            return True
        except ImportError:
            return False
    
    def _check_av(self) -> bool:
        """Check av availability"""
        try:
            import av
            return True
        except ImportError:
            return False
    
    def initialize(self) -> bool:
        """Initialize audio processor"""
        try:
            logger.info(f"Initializing backend: {self.backend}")
            
            if self.backend == "sounddevice":
                return self._init_sounddevice()
            elif self.backend == "pyaudio":
                return self._init_pyaudio()
            elif self.backend == "av":
                return self._init_av()
            else:
                logger.error(f"Unknown backend: {self.backend}")
                return False
                
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
    
    def _init_sounddevice(self) -> bool:
        """Initialize sounddevice with system audio support"""
        try:
            import sounddevice as sd
            
            # Check available devices
            devices = sd.query_devices()
            input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
            
            if not input_devices:
                logger.warning("No input devices found, but continuing initialization")
                # Continue without input devices (for fallback mode)
                self.audio_backend = sd
                self.is_initialized = True
                logger.info("sounddevice initialized (without input devices)")
                return True
            
            # Look for system audio capture devices (BlackHole, Loopback, etc.)
            system_audio_devices = []
            microphone_devices = []
            
            for idx, info in enumerate(devices):
                if info.get('max_input_channels', 0) > 0:
                    name = (info.get('name') or '').lower()
                    if any(keyword in name for keyword in ['blackhole', 'loopback', 'system', 'audio', 'mix']):
                        system_audio_devices.append((idx, info))
                    elif any(keyword in name for keyword in ['microphone', 'микрофон', 'built-in', 'macbook', 'internal']):
                        microphone_devices.append((idx, info))
            
            # Prefer microphone devices to capture user's voice by default
            if microphone_devices:
                selected_device = microphone_devices[0][0]
                logger.info(f"Using microphone device: {microphone_devices[0][1].get('name')}")
            elif system_audio_devices:
                selected_device = system_audio_devices[0][0]
                logger.info(f"Using system audio device: {system_audio_devices[0][1].get('name')}")
            else:
                selected_device = sd.default.device[0]
                logger.info(f"Using default device: {selected_device}")
            
            # Apply selected device
            try:
                out_dev = sd.default.device[1] if isinstance(sd.default.device, (list, tuple)) and len(sd.default.device) > 1 else None
                sd.default.device = (selected_device, out_dev)
            except Exception:
                pass
            
            self.audio_backend = sd
            self.is_initialized = True
            logger.info(f"sounddevice initialized with device {selected_device}")
            return True
            
        except Exception as e:
            logger.error(f"sounddevice initialization error: {e}")
            return False
    
    def _init_pyaudio(self) -> bool:
        """Initialize pyaudio"""
        try:
            import pyaudio
            
            # Initialize PyAudio
            self.audio_backend = pyaudio.PyAudio()
            
            # Check available devices
            device_count = self.audio_backend.get_device_count()
            if device_count == 0:
                logger.error("No audio devices found")
                return False
            
            logger.info(f"Found {device_count} audio devices")
            self.is_initialized = True
            logger.info("pyaudio initialized")
            return True
            
        except Exception as e:
            logger.error(f"pyaudio initialization error: {e}")
            return False
    
    def _init_av(self) -> bool:
        """Initialize av"""
        try:
            import av
            
            # av is mainly used for decoding, not for recording
            logger.warning("av is not suitable for recording, switching to sounddevice")
            self.backend = "sounddevice"
            return self._init_sounddevice()
            
        except Exception as e:
            logger.error(f"av initialization error: {e}")
            return False
    
    def start_realtime_processing(
        self,
        voice_engine,
        output_file: str = "realtime_dialogue.json",
        chunk_duration: int = 10,
        save_audio: bool = True
    ) -> bool:
        """
        Start real-time processing
        
        Args:
            voice_engine: NookEngine instance
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
            logger.info("Starting real-time processing...")
            
            # Check microphone availability
            if not self._check_microphone_access():
                logger.warning("Microphone not available, using fallback mode")
                return self._start_fallback_mode(voice_engine, output_file, chunk_duration, save_audio)
            
            # Create directories
            os.makedirs("transcripts", exist_ok=True)
            os.makedirs("audio_chunks", exist_ok=True)
            
            # Configure parameters
            self.chunk_duration = chunk_duration
            self.chunk_samples = int(self.sample_rate * chunk_duration)
            
            # Start recording
            self.is_recording = True
            
            # Start recording thread
            recording_thread = threading.Thread(
                target=self._recording_loop,
                args=(voice_engine, output_file, save_audio)
            )
            recording_thread.daemon = True
            recording_thread.start()
            
            logger.info("Real-time processing started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting real-time processing: {e}")
            return False

    # === LOW LATENCY (STREAMING) ===
    def start_low_latency_processing(
        self,
        voice_engine,
        output_json: str = "transcripts/realtime_diarized.json",
        output_jsonl: str = "transcripts/realtime_stream.jsonl",
        partial_interval: float = 1.0,
        vad_aggressiveness: int = 2,
        min_speech_ms: int = 300,
        post_silence_ms: int = 400,
        max_segment_ms: int = 8000,
        enable_diarization: bool = True,
    ) -> bool:
        """
        Start low-latency mode with VAD and streaming JSONL output.

        - Every partial_interval seconds intermediate segments are published (is_final=false)
        - At the end of phrase final segment is published (is_final=true)
        """
        if not self.is_initialized:
            if not self.initialize():
                return False

        if not _HAS_WEBRTCVAD:
            logger.warning("webrtcvad not installed, using fallback to short chunks (2s)")
            return self.start_realtime_processing(
                voice_engine,
                output_file=output_json,
                chunk_duration=2,
                save_audio=False,
            )

        try:
            import sounddevice as sd

            os.makedirs(os.path.dirname(output_json) or ".", exist_ok=True)

            self._stop_event.clear()
            self._frames_deque.clear()
            self._sequence_id = 0

            # Segmenter state
            state = {
                "in_speech": False,
                "speech_frames": [],  # list[bytes]
                "speech_start_sample": 0,
                "last_emit_time": 0.0,
                "samples_seen": 0,
                "frame_samples": int(self.sample_rate * 0.02),  # 20 ms
                "frame_bytes": int(self.sample_rate * 0.02) * 2,  # int16 mono
                "partial_interval": partial_interval,
                "min_speech_frames": max(1, int(min_speech_ms / 20)),
                "post_silence_frames": max(1, int(post_silence_ms / 20)),
                "max_segment_frames": max(1, int(max_segment_ms / 20)),
                "silence_counter": 0,
            }

            vad = webrtcvad.Vad(vad_aggressiveness)

            def _write_jsonl(path: str, obj: dict):
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(obj, ensure_ascii=False) + "\n")

            def _emit_segment(is_final: bool, pcm_frames: list[bytes], start_sample: int):
                if not pcm_frames:
                    return
                # Convert to numpy
                pcm = b"".join(pcm_frames)
                audio_np = np.frombuffer(pcm, dtype=np.int16)

                # Timestamps
                start_sec = start_sample / self.sample_rate
                end_sec = (start_sample + len(audio_np)) / self.sample_rate

                # Save to temporary WAV
                tmp_name = f"audio_chunks/live_{self._sequence_id:06d}.wav"
                os.makedirs("audio_chunks", exist_ok=True)
                with wave.open(tmp_name, "wb") as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(pcm)

                seq_id = self._sequence_id
                self._sequence_id += 1

                # Put task for processing
                self._segment_queue.put({
                    "id": seq_id,
                    "file": tmp_name,
                    "start": start_sec,
                    "end": end_sec,
                    "is_final": is_final,
                    "output_json": output_json,
                    "output_jsonl": output_jsonl,
                    "voice_engine": voice_engine,
                    "enable_diarization": enable_diarization,
                })

            def callback(indata, frames, time_info, status):  # sd.InputStream callback
                if self._stop_event.is_set():
                    raise sd.CallbackStop
                if status:
                    logger.debug(f"audio status: {status}")

                # indata: float32 [-1..1] shape (frames, channels)
                mono = indata[:, 0]
                # Clamp and scale to int16 to avoid NaNs/overflows causing garbage text
                mono = np.clip(mono, -1.0, 1.0)
                pcm16 = (mono * 32767.0).astype(np.int16).tobytes()

                # Cut into 20ms frames
                frame_size = state["frame_bytes"]
                buffer = getattr(callback, "_buffer", b"") + pcm16
                chunks = []
                while len(buffer) >= frame_size:
                    chunks.append(buffer[:frame_size])
                    buffer = buffer[frame_size:]
                callback._buffer = buffer

                for frame in chunks:
                    is_speech = vad.is_speech(frame, self.sample_rate)
                    if is_speech:
                        if not state["in_speech"]:
                            # speech start
                            state["in_speech"] = True
                            state["speech_frames"] = []
                            state["speech_start_sample"] = state["samples_seen"]
                            state["silence_counter"] = 0
                            state["last_emit_time"] = time.time()
                        state["speech_frames"].append(frame)
                        state["silence_counter"] = 0

                        # Partial emit (use ~0.6s context for lower latency and better stability)
                        if time.time() - state["last_emit_time"] >= state["partial_interval"]:
                            max_frames = int(0.6 / 0.02)
                            start_index = max(0, len(state["speech_frames"]) - max_frames)
                            partial_frames = state["speech_frames"][start_index:]
                            _emit_segment(False, partial_frames, state["speech_start_sample"] + start_index * state["frame_samples"]) 
                            state["last_emit_time"] = time.time()

                        # Limit maximum segment length
                        if len(state["speech_frames"]) >= state["max_segment_frames"]:
                            _emit_segment(True, state["speech_frames"], state["speech_start_sample"])
                            state["in_speech"] = False
                            state["speech_frames"] = []
                            state["silence_counter"] = 0
                    else:
                        # silence
                        if state["in_speech"]:
                            state["silence_counter"] += 1
                            if state["silence_counter"] >= state["post_silence_frames"] and len(state["speech_frames"]) >= state["min_speech_frames"]:
                                _emit_segment(True, state["speech_frames"], state["speech_start_sample"])
                                state["in_speech"] = False
                                state["speech_frames"] = []
                                state["silence_counter"] = 0

                    state["samples_seen"] += state["frame_samples"]

            # Segment processing thread
            def worker():
                while not self._stop_event.is_set():
                    try:
                        task = self._segment_queue.get(timeout=0.2)
                    except queue.Empty:
                        continue
                    try:
                        seg_id = task["id"]
                        file_path = task["file"]
                        start = task["start"]
                        end = task["end"]
                        is_final = task["is_final"]
                        engine = task["voice_engine"]
                        out_json = task["output_json"]
                        out_jsonl = task["output_jsonl"]

                        # Transcription
                        transcription = engine.transcriber.transcribe(file_path, "json")
                        if not transcription:
                            continue

                        enable_diar = bool(task.get("enable_diarization", True)) and is_final
                        if enable_diar:
                            diar = engine.diarizer.diarize(file_path, transcription, reference_speaker=None)
                            segments = diar.get("segments", []) if diar else []
                        else:
                            # Use raw transcription segments for faster updates (filter trivial fillers)
                            segs = transcription.get("segments", [])
                            segments = []
                            for s in segs:
                                text = (s.get("text", "") or "").strip()
                                if not text:
                                    continue
                                low = text.lower().strip(" .!")
                                if low in {"ok", "okay", "yeah", "uh", "um"}:
                                    continue
                                if s.get("no_speech_prob", 0.0) > 0.6:
                                    continue
                                # Drop if this segment is fully contained in the last one to reduce loops
                                if segments:
                                    prev = segments[-1]["text"].lower()
                                    if text.lower().startswith(prev) or prev.endswith(text.lower()):
                                        continue
                                segments.append({
                                    "start": s.get("start", start),
                                    "end": s.get("end", end),
                                    "text": text,
                                    "speaker": "USER",
                                })

                        # Fallback: if diarization produced no segments, synthesize from transcription
                        if not segments:
                            tsegs = transcription.get("segments", [])
                            if tsegs:
                                segments = [{
                                    "start": s.get("start", start),
                                    "end": s.get("end", end),
                                    "text": s.get("text", "").strip(),
                                    "speaker": "SPEAKER_00",
                                } for s in tsegs if s.get("text")]

                        # If still empty - skip
                        if not segments:
                            continue

                        # Join segment text (for short segments usually one segment)
                        joined = {
                            "id": seg_id,
                            "start": segments[0].get("start", start),
                            "end": segments[-1].get("end", end),
                            "text": " ".join(s.get("text", "").strip() for s in segments).strip(),
                            "speaker": segments[0].get("speaker", "UNKNOWN"),
                            "is_final": is_final,
                        }

                        # Write JSONL (update stream)
                        _write_jsonl(out_jsonl, joined)

                        # Update aggregated JSON (only final)
                        if is_final:
                            try:
                                if os.path.exists(out_json):
                                    with open(out_json, "r", encoding="utf-8") as f:
                                        agg = json.load(f)
                                else:
                                    agg = {"segments": [], "speakers": [], "total_duration": 0.0, "audio_file": "realtime_recording", "metadata": {"backend": self.backend}}
                                agg["segments"].append({k: joined[k] for k in ["start", "end", "text", "speaker"]})
                                agg["speakers"] = sorted(list({*agg.get("speakers", []), joined["speaker"]}))
                                agg["total_duration"] = float(sum(seg["end"] - seg["start"] for seg in agg["segments"]))
                                with open(out_json, "w", encoding="utf-8") as f:
                                    json.dump(agg, f, indent=2, ensure_ascii=False)
                            except Exception as ee:
                                logger.warning(f"Error updating aggregated JSON: {ee}")
                    except Exception as e:
                        logger.error(f"Error processing segment: {e}")
                    finally:
                        self._segment_queue.task_done()

            worker_thread = threading.Thread(target=worker, daemon=True)
            worker_thread.start()

            # Start input stream
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                blocksize=int(self.sample_rate * 0.01),  # 10ms frames for lower latency
                callback=callback,
            )
            self._stream.start()

            logger.info("Low-latency mode started. Publishing to JSONL and JSON...")
            logger.info("Stop with stop_recording()")
            return True
        except Exception as e:
            logger.error(f"Error starting low-latency mode: {e}")
            return False
    
    def _recording_loop(
        self,
        voice_engine,
        output_file: str,
        save_audio: bool
    ):
        """Main recording and processing loop"""
        chunk_idx = 0
        all_results = []
        
        try:
            while self.is_recording:
                # Write chunk
                chunk_file = f"audio_chunks/chunk_{chunk_idx:04d}.wav"
                logger.info(f"Writing chunk {chunk_idx}: {chunk_file}")
                
                if self._record_chunk(chunk_file):
                    # Process chunk
                    result = self._process_chunk(voice_engine, chunk_file)
                    
                    if result:
                        all_results.extend(result)
                        
                        # Save intermediate result
                        self._save_intermediate_result(all_results, output_file)
                        
                        # Output last lines
                        for item in result:
                            logger.info(f"[{item['speaker']}] {item['text']}")
                    
                    chunk_idx += 1
                else:
                    logger.warning("Error recording chunk")
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Stop signal received")
        except Exception as e:
            logger.error(f"Error in recording loop: {e}")
        finally:
            self.is_recording = False
            logger.info("Real-time processing stopped")
            
            # Save final result
            if all_results:
                self._save_intermediate_result(all_results, output_file)
                logger.info(f"Final result saved to: {output_file}")
    
    def _record_chunk(self, filename: str) -> bool:
        """Record one audio chunk"""
        try:
            if self.backend == "sounddevice":
                return self._record_chunk_sounddevice(filename)
            elif self.backend == "pyaudio":
                return self._record_chunk_pyaudio(filename)
            else:
                logger.error(f"Unsupported backend: {self.backend}")
                return False
                
        except Exception as e:
            logger.error(f"Error recording chunk: {e}")
            return False
    
    def _record_chunk_sounddevice(self, filename: str) -> bool:
        """Record chunk via sounddevice"""
        try:
            import sounddevice as sd
            
            # Record audio
            audio_data = sd.rec(
                int(self.chunk_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16
            )
            
            # Wait for recording to complete
            sd.wait()
            
            # Save to WAV file
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            return True
            
        except Exception as e:
            logger.error(f"sounddevice recording error: {e}")
            return False
    
    def _record_chunk_pyaudio(self, filename: str) -> bool:
        """Record chunk via pyaudio"""
        try:
            # Open stream
            stream = self.audio_backend.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_samples
            )
            
            # Write data
            frames = []
            for _ in range(0, int(self.sample_rate / self.chunk_samples * self.chunk_duration)):
                data = stream.read(self.chunk_samples)
                frames.append(data)
            
            # Close stream
            stream.stop_stream()
            stream.close()
            
            # Save to WAV file
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(b''.join(frames))
            
            return True
            
        except Exception as e:
            logger.error(f"pyaudio recording error: {e}")
            return False
    
    def _process_chunk(
        self,
        voice_engine,
        chunk_file: str
    ) -> Optional[List[Dict]]:
        """Process recorded chunk"""
        try:
            # Transcribe
            transcription = voice_engine.transcriber.transcribe(chunk_file, "json")
            if not transcription:
                logger.warning(f"Failed to transcribe: {chunk_file}")
                return None
            
            # Diarize
            diarization_result = voice_engine.diarizer.diarize(
                chunk_file,
                transcription
            )
            
            if diarization_result:
                return diarization_result.get('segments', [])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            return None
    
    def _save_intermediate_result(self, results: List[Dict], output_file: str):
        """Save intermediate result"""
        try:
            # Create result structure
            final_result = {
                'segments': results,
                'speakers': list(set(seg['speaker'] for seg in results)),
                'total_duration': sum(seg['end'] - seg['start'] for seg in results),
                'audio_file': 'realtime_recording',
                'metadata': {
                    'timestamp': time.time(),
                    'chunks_processed': len(results),
                    'backend': self.backend
                }
            }
            
            # Save to JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving intermediate result: {e}")
    
    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        self._stop_event.set()
        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        except Exception:
            pass
        logger.info("Recording stopped")
    
    def get_audio_devices(self) -> List[Dict]:
        """Return list of available audio devices"""
        try:
            if self.backend == "sounddevice":
                import sounddevice as sd
                devices = sd.query_devices()
                return [
                    {
                        'id': i,
                        'name': d.get('name', f'Device {i}'),
                        'max_inputs': d.get('max_input_channels', 0),
                        'max_outputs': d.get('max_output_channels', 0),
                        'default_samplerate': d.get('default_samplerate', 44100)
                    }
                    for i, d in enumerate(devices)
                ]
            elif self.backend == "pyaudio":
                devices = []
                for i in range(self.audio_backend.get_device_count()):
                    try:
                        info = self.audio_backend.get_device_info_by_index(i)
                        devices.append({
                            'id': i,
                            'name': info['name'],
                            'max_inputs': info['maxInputChannels'],
                            'max_outputs': info['maxOutputChannels'],
                            'default_samplerate': info['defaultSampleRate']
                        })
                    except Exception:
                        continue
                return devices
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting device list: {e}")
            return []
    
    def set_audio_device(self, device_id: int) -> bool:
        """Set audio device"""
        try:
            if self.backend == "sounddevice":
                import sounddevice as sd
                sd.default.device = device_id
                logger.info(f"Device set: {device_id}")
                return True
            else:
                logger.warning("Device changing is only supported for sounddevice")
                return False
                
        except Exception as e:
            logger.error(f"Error setting device: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """Return model information"""
        return {
            "backend": self.backend,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_duration": self.chunk_duration,
            "is_initialized": self.is_initialized,
            "is_recording": self.is_recording
        }
    
    def _check_microphone_access(self) -> bool:
        """Check microphone availability"""
        try:
            if self.backend == "sounddevice":
                import sounddevice as sd
                devices = sd.query_devices()
                input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
                return len(input_devices) > 0
            return False
        except Exception:
            return False
    
    def _start_fallback_mode(
        self,
        voice_engine,
        output_file: str,
        chunk_duration: int,
        save_audio: bool
    ) -> bool:
        """Start fallback mode without microphone"""
        try:
            logger.info("Starting fallback mode (without microphone)")
            
            # Create directories
            os.makedirs("transcripts", exist_ok=True)
            os.makedirs("audio_chunks", exist_ok=True)
            
            # Create empty result
            empty_result = {
                "segments": [],
                "speakers": [],
                "total_duration": 0.0,
                "audio_file": "fallback_mode",
                "metadata": {
                    "mode": "fallback",
                    "message": "Microphone not available, use files for processing"
                }
            }
            
            # Save empty result
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(empty_result, f, indent=2, ensure_ascii=False)
            
            logger.info("Fallback mode started (without microphone)")
            return True
            
        except Exception as e:
            logger.error(f"Error starting fallback mode: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_recording()
        
        if self.audio_backend and hasattr(self.audio_backend, 'terminate'):
            self.audio_backend.terminate()
        
        self.is_initialized = False
        logger.info("Audio processor resources cleaned up")
