"""
Diarizer module - responsible for separating speech into speakers
Supports various algorithms: Resemblyzer, pyannote.audio, speaker-diarization
"""

import os
import json
import numpy as np
import librosa
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeakerDiarizer:
    """
    High-quality speaker diarizer
    """
    
    def __init__(
        self,
        threshold: float = 0.7,
        method: str = "auto",
        segment_length: float = 2.0,
        min_segment_length: float = 1.0,
        clustering_method: str = "hierarchical",
        interruption_gap: float = 1.0,
        continuous_mode: bool = True
    ):
        """
        Initialize diarizer
        
        Args:
            threshold: Threshold for speaker separation
            method: Diarization method (auto, resemblyzer, pyannote, speaker_diarization)
            segment_length: Segment length in seconds
            min_segment_length: Minimum segment length
            clustering_method: Clustering method
            interruption_gap: Maximum gap in seconds to consider as interruption
            continuous_mode: Enable continuous transcription mode
        """
        self.threshold = threshold
        self.method = method
        self.segment_length = segment_length
        self.min_segment_length = min_segment_length
        self.clustering_method = clustering_method
        self.interruption_gap = interruption_gap
        self.continuous_mode = continuous_mode
        
        # Auto-detect method
        if method == "auto":
            self.method = self._detect_best_method()
        
        # State
        self.is_initialized = False
        self.encoder = None
        self.diarization_model = None
        
        # Clustering parameters
        self.clustering_params = {
            "hierarchical": {
                "n_clusters": None,  # Auto-detect
                "metric": "precomputed",
                "linkage": "average"
            },
            "spectral": {
                "n_clusters": None,
                "affinity": "precomputed",
                "random_state": 42
            },
            "dbscan": {
                "eps": 0.3,
                "min_samples": 2,
                "metric": "precomputed"
            }
        }
        
        logger.info(f"Initializing SpeakerDiarizer: {self.method}")
    
    def _detect_best_method(self) -> str:
        """Auto-detect best available diarization method"""
        # Check Resemblyzer (reliable local method)
        if self._check_resemblyzer():
            return "resemblyzer"
        
        # Check pyannote.audio (highest quality, but requires token)
        if self._check_pyannote():
            return "pyannote"
        
        # Check speaker-diarization
        if self._check_speaker_diarization():
            return "speaker_diarization"
        
        # Fallback to a simple heuristic diarizer
        logger.warning("No method found, using simple_heuristic")
        return "simple_heuristic"
    
    def _check_pyannote(self) -> bool:
        """Check pyannote.audio availability"""
        try:
            import pyannote.audio
            return True
        except ImportError:
            return False
    
    def _check_speaker_diarization(self) -> bool:
        """Check speaker-diarization availability"""
        try:
            import speaker_diarization
            return True
        except ImportError:
            return False
    
    def _check_resemblyzer(self) -> bool:
        """Check Resemblyzer availability"""
        try:
            from resemblyzer import VoiceEncoder
            return True
        except ImportError:
            return False
    
    def initialize(self) -> bool:
        """Initialize diarizer and load models"""
        try:
            logger.info(f"Initializing method: {self.method}")
            
            if self.method == "pyannote":
                return self._init_pyannote()
            elif self.method == "speaker_diarization":
                return self._init_speaker_diarization()
            elif self.method == "resemblyzer":
                return self._init_resemblyzer()
            elif self.method == "simple_heuristic":
                # No heavy models required
                self.is_initialized = True
                logger.info("Simple heuristic diarizer initialized")
                return True
            else:
                logger.error(f"Unknown method: {self.method}")
                return False
                
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
    
    def _init_pyannote(self) -> bool:
        """Initialize pyannote.audio"""
        try:
            import pyannote.audio
            from pyannote.audio.pipelines.speaker_diarization import SpeakerDiarization
            
            # Load model (requires HuggingFace token)
            # For production need to get token at https://huggingface.co/pyannote/speaker-diarization
            model_name = "pyannote/speaker-diarization"
            
            try:
                self.diarization_model = SpeakerDiarization.from_pretrained(model_name)
                self.is_initialized = True
                logger.info("pyannote.audio initialized")
                return True
            except Exception as e:
                logger.warning(f"Failed to load pyannote model: {e}")
                logger.info("Switching to Resemblyzer")
                self.method = "resemblyzer"
                self.is_initialized = False
                return self._init_resemblyzer()
                
        except ImportError:
            logger.warning("pyannote.audio not installed, switching to Resemblyzer")
            self.method = "resemblyzer"
            return self._init_resemblyzer()
    
    def _init_speaker_diarization(self) -> bool:
        """Initialize speaker-diarization"""
        try:
            import speaker_diarization
            
            # Initialize model
            self.diarization_model = speaker_diarization.SpeakerDiarization()
            self.is_initialized = True
            logger.info("speaker-diarization initialized")
            return True
            
        except ImportError:
            logger.warning("speaker-diarization not installed, switching to Resemblyzer")
            self.method = "resemblyzer"
            return self._init_resemblyzer()
    
    def _init_resemblyzer(self) -> bool:
        """Initialize Resemblyzer"""
        try:
            from resemblyzer import VoiceEncoder
            
            # Initialize encoder
            self.encoder = VoiceEncoder()
            self.is_initialized = True
            logger.info("Resemblyzer initialized")
            return True
            
        except ImportError:
            logger.error("Resemblyzer not installed")
            return False
    
    def diarize(
        self,
        audio_file: Union[str, Path],
        transcription: Dict,
        reference_speaker: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Perform audio diarization
        
        Args:
            audio_file: Path to audio file
            transcription: Transcription result
            reference_speaker: Path to reference voice of main speaker
            
        Returns:
            Diarization result
        """
        if not self.is_initialized:
            if not self.initialize():
                return None
        
        try:
            if self.method == "pyannote":
                return self._diarize_pyannote(audio_file, transcription, reference_speaker)
            elif self.method == "speaker_diarization":
                return self._diarize_speaker_diarization(audio_file, transcription, reference_speaker)
            elif self.method == "resemblyzer":
                return self._diarize_resemblyzer(audio_file, transcription, reference_speaker)
            elif self.method == "simple_heuristic":
                return self._diarize_simple(audio_file, transcription)
            else:
                logger.error(f"Unknown method: {self.method}")
                return None
                
        except Exception as e:
            logger.error(f"Diarization error: {e}")
            return None
    
    def _diarize_pyannote(
        self,
        audio_file: Union[str, Path],
        transcription: Dict,
        reference_speaker: Optional[str]
    ) -> Optional[Dict]:
        """Diarization via pyannote.audio"""
        try:
            # Perform diarization
            diarization = self.diarization_model(str(audio_file))
            
            # Get segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': speaker
                })
            
            # Align with transcription
            return self._align_with_transcription(segments, transcription, reference_speaker)
            
        except Exception as e:
            logger.error(f"pyannote diarization error: {e}")
            return None
    
    def _diarize_speaker_diarization(
        self,
        audio_file: Union[str, Path],
        transcription: Dict,
        reference_speaker: Optional[str]
    ) -> Optional[Dict]:
        """Diarization via speaker-diarization"""
        try:
            # Perform diarization
            result = self.diarization_model.diarize(str(audio_file))
            
            # Process result
            segments = []
            for segment in result:
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'speaker': segment['speaker']
                })
            
            # Align with transcription
            return self._align_with_transcription(segments, transcription, reference_speaker)
            
        except Exception as e:
            logger.error(f"speaker-diarization diarization error: {e}")
            return None
    
    def _diarize_resemblyzer(
        self,
        audio_file: Union[str, Path],
        transcription: Dict,
        reference_speaker: Optional[str]
    ) -> Optional[Dict]:
        """Diarization via Resemblyzer"""
        try:
            # Load audio
            wav, sr = librosa.load(str(audio_file), sr=16000)
            
            # Preprocessing
            from resemblyzer import preprocess_wav
            wav = preprocess_wav(wav)
            
            # Create segments
            samples_per_segment = int(self.segment_length * sr)
            min_samples = int(self.min_segment_length * sr)
            
            segments = []
            embeddings = []
            
            logger.info("Extracting embeddings...")
            logger.info(f"Audio length: {len(wav)} samples ({len(wav)/sr:.2f}s)")
            logger.info(f"Segment length: {samples_per_segment} samples ({self.segment_length}s)")
            logger.info(f"Min segment length: {min_samples} samples ({self.min_segment_length}s)")
            
            for i in range(0, len(wav), samples_per_segment):
                segment = wav[i:i + samples_per_segment]
                if len(segment) >= min_samples:
                    start_time = i / sr
                    end_time = min((i + len(segment)) / sr, len(wav) / sr)
                    
                    # Extract embedding
                    embedding = self.encoder.embed_utterance(segment)
                    embeddings.append(embedding)
                    
                    segments.append({
                        'start': start_time,
                        'end': end_time,
                        'embedding': embedding
                    })
            
            logger.info(f"Created {len(segments)} segments")
            
            # Handle case with no segments
            if len(segments) == 0:
                logger.warning("No segments created, creating single segment for entire audio")
                # Create a single segment for the entire audio
                embedding = self.encoder.embed_utterance(wav)
                segments.append({
                    'start': 0.0,
                    'end': len(wav) / sr,
                    'embedding': embedding,
                    'speaker': 'SPEAKER_00'
                })
                return self._align_with_transcription(segments, transcription, reference_speaker)
            
            # Clustering
            if len(embeddings) > 1:
                speaker_labels = self._cluster_embeddings(embeddings)
                
                # Assign speaker labels
                for i, segment in enumerate(segments):
                    segment['speaker'] = f'SPEAKER_{speaker_labels[i]:02d}'
            elif len(embeddings) == 1:
                segments[0]['speaker'] = 'SPEAKER_00'
            else:
                # No embeddings case (should not happen after our fix above)
                logger.warning("No embeddings available")
                return None
            
            # Align with transcription
            return self._align_with_transcription(segments, transcription, reference_speaker)
            
        except Exception as e:
            logger.error(f"Resemblyzer diarization error: {e}")
            return None

    def _diarize_simple(
        self,
        audio_file: Union[str, Path],
        transcription: Dict
    ) -> Optional[Dict]:
        """Heuristic diarizer: alternate speakers on pauses.
        Assigns speakers based on gaps > interruption_gap between segments.
        This is a lightweight fallback for environments without heavy deps.
        """
        try:
            whisper_segments = transcription.get('segments', [])
            if not whisper_segments:
                return None
            segments = []
            current_speaker = 'SPEAKER_00'
            last_end = None
            for seg in whisper_segments:
                start = seg.get('start', 0.0)
                end = seg.get('end', start)
                text = (seg.get('text') or '').strip()
                if not text:
                    continue
                if last_end is not None and start - last_end > self.interruption_gap:
                    # Switch speaker on larger pause
                    current_speaker = 'SPEAKER_01' if current_speaker == 'SPEAKER_00' else 'SPEAKER_00'
                segments.append({
                    'start': start,
                    'end': end,
                    'text': text,
                    'speaker': current_speaker,
                })
                last_end = end
            speakers = sorted(list({seg['speaker'] for seg in segments}))
            total_duration = sum(seg['end'] - seg['start'] for seg in segments)
            return {
                'segments': segments,
                'speakers': speakers,
                'total_duration': float(total_duration),
                'audio_file': str(transcription.get('audio_file', '')),
                'metadata': {
                    'method': 'simple_heuristic',
                    'threshold': self.threshold,
                    'segment_length': self.segment_length,
                    'continuous_mode': self.continuous_mode
                }
            }
        except Exception as e:
            logger.error(f"Simple heuristic diarization error: {e}")
            return None
    
    def _cluster_embeddings(self, embeddings: List[np.ndarray]) -> List[int]:
        """Cluster embeddings to determine speakers"""
        try:
            from sklearn.cluster import AgglomerativeClustering
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings)
            
            # Auto-detect number of clusters
            n_speakers = self._estimate_speaker_count(embeddings_array)
            
            # Apply hierarchical clustering
            clustering = AgglomerativeClustering(
                n_clusters=n_speakers,
                metric='precomputed',
                linkage='average'
            )
            
            # Calculate distance matrix
            distances = 1 - cosine_similarity(embeddings_array)
            
            # Cluster
            labels = clustering.fit_predict(distances)
            
            return labels.tolist()
            
        except ImportError:
            logger.warning("scikit-learn not installed, using simple clustering")
            return self._simple_clustering(embeddings)
    
    def _estimate_speaker_count(self, embeddings: np.ndarray) -> int:
        """Estimate number of speakers"""
        try:
            from sklearn.cluster import AgglomerativeClustering
            from sklearn.metrics.pairwise import cosine_similarity
            from sklearn.metrics import silhouette_score
            
            # Try different number of clusters
            max_speakers = min(5, len(embeddings) - 1)
            best_score = -1
            best_n = 2
            
            for n in range(2, max_speakers + 1):
                try:
                    clustering = AgglomerativeClustering(
                        n_clusters=n,
                        metric='precomputed',
                        linkage='average'
                    )
                    
                    distances = 1 - cosine_similarity(embeddings)
                    labels = clustering.fit_predict(distances)
                    
                    # Calculate silhouette score
                    score = silhouette_score(distances, labels, metric='precomputed')
                    
                    if score > best_score:
                        best_score = score
                        best_n = n
                        
                except Exception:
                    continue
            
            logger.info(f"Estimated number of speakers: {best_n}")
            return best_n
            
        except Exception:
            logger.warning("Failed to estimate number of speakers, using 2")
            return 2
    
    def _simple_clustering(self, embeddings: List[np.ndarray]) -> List[int]:
        """Simple clustering without scikit-learn"""
        labels = [0]  # First speaker
        
        for i in range(1, len(embeddings)):
            # Compare with previous segment
            similarity = np.dot(embeddings[i], embeddings[i-1])
            
            # If similarity is low - new speaker
            if similarity < self.threshold:
                labels.append(max(labels) + 1)
            else:
                labels.append(labels[-1])
        
        return labels
    
    def _align_with_transcription(
        self,
        diarization_segments: List[Dict],
        transcription: Dict,
        reference_speaker: Optional[str]
    ) -> Optional[Dict]:
        """Align diarization results with transcription"""
        try:
            # Get transcription segments
            whisper_segments = transcription.get('segments', [])
            if not whisper_segments:
                logger.warning("No segments in transcription")
                return None
            
            # Load reference voice if available
            reference_embedding = None
            if reference_speaker and os.path.exists(reference_speaker):
                reference_embedding = self._load_reference_embedding(reference_speaker)
            
            # Align segments
            aligned_segments = []
            
            for seg in whisper_segments:
                seg_start = seg['start']
                seg_end = seg['end']
                seg_text = seg['text'].strip()
                
                if not seg_text:
                    continue
                
                # Find corresponding speaker
                speaker = self._find_speaker_for_segment(
                    seg_start, seg_end, diarization_segments, reference_embedding
                )
                
                aligned_segments.append({
                    'speaker': speaker,
                    'start': seg_start,
                    'end': seg_end,
                    'text': seg_text,
                    'confidence': seg.get('avg_logprob', 0.0)
                })
            
            # Use continuous mode if enabled
            if self.continuous_mode:
                final_segments = self._create_continuous_transcription(aligned_segments)
            else:
                final_segments = aligned_segments
            
            # Build result
            speakers = list(set(seg['speaker'] for seg in final_segments))
            total_duration = sum(seg['end'] - seg['start'] for seg in final_segments)
            
            return {
                'segments': final_segments,
                'speakers': speakers,
                'total_duration': total_duration,
                'audio_file': str(transcription.get('audio_file', '')),
                'metadata': {
                    'method': self.method,
                    'threshold': self.threshold,
                    'segment_length': self.segment_length,
                    'continuous_mode': self.continuous_mode
                }
            }
            
        except Exception as e:
            logger.error(f"Alignment error: {e}")
            return None

    def _create_continuous_transcription(self, aligned_segments: List[Dict]) -> List[Dict]:
        """
        Create continuous transcription where speakers change only when interrupting each other
        """
        if not aligned_segments:
            return []
        
        continuous_segments = []
        current_speaker = aligned_segments[0]['speaker']
        current_text = []
        current_start = aligned_segments[0]['start']
        current_end = aligned_segments[0]['end']
        
        for i, segment in enumerate(aligned_segments):
            # Check if this is a speaker interruption (different speaker with small gap)
            is_interruption = False
            if i > 0:
                prev_segment = aligned_segments[i-1]
                time_gap = segment['start'] - prev_segment['end']
                
                # If different speaker and small gap, consider it interruption
                if (segment['speaker'] != prev_segment['speaker'] and 
                    time_gap < self.interruption_gap and 
                    segment['speaker'] != current_speaker):
                    is_interruption = True
            
            # If same speaker or continuation, merge text
            if segment['speaker'] == current_speaker and not is_interruption:
                current_text.append(segment['text'])
                current_end = segment['end']
            else:
                # Save current segment if we have text
                if current_text:
                    continuous_segments.append({
                        'speaker': current_speaker,
                        'start': current_start,
                        'end': current_end,
                        'text': ' '.join(current_text).strip(),
                        'confidence': 0.0  # Average confidence would be better
                    })
                
                # Start new segment
                current_speaker = segment['speaker']
                current_text = [segment['text']]
                current_start = segment['start']
                current_end = segment['end']
        
        # Add final segment
        if current_text:
            continuous_segments.append({
                'speaker': current_speaker,
                'start': current_start,
                'end': current_end,
                'text': ' '.join(current_text).strip(),
                'confidence': 0.0
            })
        
        return continuous_segments
    
    def _find_speaker_for_segment(
        self,
        seg_start: float,
        seg_end: float,
        diarization_segments: List[Dict],
        reference_embedding: Optional[np.ndarray]
    ) -> str:
        """Find speaker for transcription segment"""
        speaker = 'UNKNOWN'
        max_overlap = 0
        
        for diar_seg in diarization_segments:
            # Calculate time overlap
            overlap_start = max(seg_start, diar_seg['start'])
            overlap_end = min(seg_end, diar_seg['end'])
            
            if overlap_end > overlap_start:
                overlap = overlap_end - overlap_start
                if overlap > max_overlap:
                    max_overlap = overlap
                    speaker = diar_seg['speaker']
                    
                    # If reference voice exists, check similarity
                    if reference_embedding is not None and 'embedding' in diar_seg:
                        similarity = np.dot(diar_seg['embedding'], reference_embedding)
                        if similarity > self.threshold:
                            speaker = 'USER'
                        else:
                            speaker = 'OTHER'
        
        return speaker
    
    def _load_reference_embedding(self, reference_file: str) -> Optional[np.ndarray]:
        """Load reference voice embedding"""
        try:
            if self.encoder is None:
                return None
            
            # Load audio
            wav, sr = librosa.load(reference_file, sr=16000)
            
            # Preprocessing
            from resemblyzer import preprocess_wav
            wav = preprocess_wav(wav)
            
            # Extract embedding
            embedding = self.encoder.embed_utterance(wav)
            
            logger.info(f"Reference voice loaded: {reference_file}")
            return embedding
            
        except Exception as e:
            logger.warning(f"Failed to load reference voice: {e}")
            return None
    
    def get_model_info(self) -> Dict:
        """Return model information"""
        return {
            "method": self.method,
            "threshold": self.threshold,
            "segment_length": self.segment_length,
            "clustering_method": self.clustering_method,
            "is_initialized": self.is_initialized
        }
    
    def cleanup(self):
        """Clean up resources"""
        if self.encoder:
            del self.encoder
            self.encoder = None
        
        if self.diarization_model:
            del self.diarization_model
            self.diarization_model = None
        
        self.is_initialized = False
        logger.info("Diarizer resources cleaned up")
