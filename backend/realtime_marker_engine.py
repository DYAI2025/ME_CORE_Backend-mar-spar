#!/usr/bin/env python3
"""
Real-time Marker Processing Engine for TransRapport Desktop MVP

Integrates audio streaming with marker detection for real-time analysis.
Implements ATO heuristics, SEM gating, CLU windowing, and INTUITION telemetry.
"""

import asyncio
import json
import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Import existing marker components
try:
    from ..detect.detect.DETECT_config_loader import MarkerLoader
    from ..detect.detect.DETECT_marker_models import MarkerDefinition, MarkerCategory
    MARKER_SYSTEM_AVAILABLE = True
except ImportError:
    # Fallback to absolute imports when package-relative imports are not valid
    try:
        from backend.detect.detect.DETECT_config_loader import MarkerLoader
        from backend.detect.detect.DETECT_marker_models import MarkerDefinition, MarkerCategory
        MARKER_SYSTEM_AVAILABLE = True
    except ImportError:
        MARKER_SYSTEM_AVAILABLE = False

# Import configuration
try:
    from ..app_config import app_config
    CONFIG_AVAILABLE = True
except ImportError:
    # Fallback to absolute import when package-relative import is not valid
    try:
        from backend.app_config import app_config
        CONFIG_AVAILABLE = True
    except ImportError:
        CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)

class MarkerEventType(Enum):
    """Types of marker events"""
    MARKER_DETECTED = "marker_detected"
    AUDIO_CHUNK_PROCESSED = "audio_chunk_processed"
    PROSODY_FEATURES = "prosody_features"
    TRANSCRIPTION_RESULT = "transcription_result"
    LLM_INTERPRETATION = "llm_interpretation"
    ATO_HEURISTIC = "ato_heuristic"
    SEM_GATING = "sem_gating"
    CLU_WINDOWING = "clu_windowing"
    INTUITION_SIGNAL = "intuition_signal"

@dataclass
class ProsodyFeatures:
    """Prosody features for ATO markers"""
    f0: float = 0.0          # Fundamental frequency
    rms: float = 0.0         # Root mean square energy
    zcr: float = 0.0         # Zero crossing rate
    flatness: float = 0.0    # Spectral flatness
    voicing: float = 0.0     # Voicing probability
    timestamp: float = 0.0

@dataclass
class MarkerEvent:
    """Real-time marker event"""
    event_type: MarkerEventType
    marker_id: str
    category: str
    confidence: float
    timestamp: float
    audio_chunk_id: Optional[str] = None
    prosody_features: Optional[ProsodyFeatures] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "type": self.event_type.value,
            "marker_id": self.marker_id,
            "category": self.category,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }
        
        if self.audio_chunk_id:
            result["audio_chunk_id"] = self.audio_chunk_id
            
        if self.prosody_features:
            result["prosody_features"] = {
                "f0": self.prosody_features.f0,
                "rms": self.prosody_features.rms,
                "zcr": self.prosody_features.zcr,
                "flatness": self.prosody_features.flatness,
                "voicing": self.prosody_features.voicing
            }
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result

class ATOHeuristics:
    """ATO (Attachment Theory) heuristics for marker detection"""
    
    def __init__(self):
        self.enabled = True
        self.confidence_threshold = 0.6
        
    def analyze_prosody(self, features: ProsodyFeatures) -> List[MarkerEvent]:
        """Analyze prosody features for ATO markers"""
        events = []
        
        if not self.enabled:
            return events
            
        # Anxious attachment - high F0 variance, increased RMS
        if features.f0 > 200 and features.rms > 0.03:
            events.append(MarkerEvent(
                event_type=MarkerEventType.ATO_HEURISTIC,
                marker_id="ato_anxious_speech",
                category="ATO",
                confidence=0.75,
                timestamp=features.timestamp,
                prosody_features=features,
                metadata={"attachment_style": "anxious", "indicators": ["high_f0", "high_rms"]}
            ))
        
        # Avoidant attachment - low emotional variance, flat prosody
        if features.flatness > 0.8 and features.rms < 0.01:
            events.append(MarkerEvent(
                event_type=MarkerEventType.ATO_HEURISTIC,
                marker_id="ato_avoidant_speech",
                category="ATO",
                confidence=0.68,
                timestamp=features.timestamp,
                prosody_features=features,
                metadata={"attachment_style": "avoidant", "indicators": ["high_flatness", "low_rms"]}
            ))
        
        # Secure attachment - stable prosody patterns
        if 100 < features.f0 < 200 and 0.01 < features.rms < 0.03 and features.voicing > 0.7:
            events.append(MarkerEvent(
                event_type=MarkerEventType.ATO_HEURISTIC,
                marker_id="ato_secure_speech",
                category="ATO",
                confidence=0.82,
                timestamp=features.timestamp,
                prosody_features=features,
                metadata={"attachment_style": "secure", "indicators": ["stable_f0", "balanced_rms", "good_voicing"]}
            ))
        
        return events

class SEMGating:
    """SEM (Semantic) gating for marker filtering"""
    
    def __init__(self):
        self.enabled = True
        self.gate_threshold = 0.7
        
    def gate_event(self, event: MarkerEvent, semantic_content: Optional[str] = None) -> bool:
        """Apply SEM gating to filter events"""
        if not self.enabled:
            return True
            
        # Basic semantic filtering logic
        if event.confidence < self.gate_threshold:
            return False
            
        # Category-specific gating
        if event.category == "SEM":
            # Require higher confidence for semantic markers
            return event.confidence > 0.8
            
        return True

class CLUWindowing:
    """CLU (Clustering) windowing logic for temporal analysis"""
    
    def __init__(self):
        self.enabled = True
        self.window_size = 5000  # 5 seconds in ms
        self.overlap = 0.5
        self.event_buffer: List[MarkerEvent] = []
        
    def add_event(self, event: MarkerEvent) -> List[MarkerEvent]:
        """Add event to window and return clustered events"""
        if not self.enabled:
            return [event]
            
        self.event_buffer.append(event)
        current_time = time.time() * 1000  # Convert to ms
        
        # Remove old events outside window
        self.event_buffer = [
            e for e in self.event_buffer 
            if (current_time - e.timestamp * 1000) < self.window_size
        ]
        
        # Perform clustering analysis
        clustered_events = self._analyze_clusters()
        
        return clustered_events
    
    def _analyze_clusters(self) -> List[MarkerEvent]:
        """Analyze clusters within the current window"""
        events = []
        
        if len(self.event_buffer) < 2:
            return []
            
        # Group events by category
        categories = {}
        for event in self.event_buffer:
            if event.category not in categories:
                categories[event.category] = []
            categories[event.category].append(event)
        
        # Detect clustering patterns
        for category, cat_events in categories.items():
            if len(cat_events) >= 3:  # Cluster threshold
                # Calculate average confidence
                avg_confidence = sum(e.confidence for e in cat_events) / len(cat_events)
                
                # Create cluster event
                cluster_event = MarkerEvent(
                    event_type=MarkerEventType.CLU_WINDOWING,
                    marker_id=f"clu_cluster_{category.lower()}",
                    category="CLU",
                    confidence=avg_confidence,
                    timestamp=time.time(),
                    metadata={
                        "cluster_category": category,
                        "event_count": len(cat_events),
                        "window_size_ms": self.window_size,
                        "pattern": "temporal_clustering"
                    }
                )
                events.append(cluster_event)
        
        return events

class IntuitionTelemetry:
    """INTUITION telemetry for therapeutic insights"""
    
    def __init__(self):
        self.enabled = True
        self.sensitivity = 0.5
        self.pattern_history: List[MarkerEvent] = []
        
    def analyze_patterns(self, recent_events: List[MarkerEvent]) -> List[MarkerEvent]:
        """Analyze patterns for intuitive insights"""
        if not self.enabled:
            return []
            
        self.pattern_history.extend(recent_events)
        
        # Keep last 100 events for pattern analysis
        if len(self.pattern_history) > 100:
            self.pattern_history = self.pattern_history[-100:]
        
        intuition_events = []
        
        # Detect subtle conflict patterns
        conflict_indicators = [
            e for e in self.pattern_history[-20:] 
            if e.category == "ATO" and e.confidence > 0.7
        ]
        
        if len(conflict_indicators) >= 3:
            intuition_events.append(MarkerEvent(
                event_type=MarkerEventType.INTUITION_SIGNAL,
                marker_id="intuition_subtle_conflict",
                category="INTUITION",
                confidence=0.65,
                timestamp=time.time(),
                metadata={
                    "pattern_type": "subtle_conflict",
                    "indicator_count": len(conflict_indicators),
                    "therapeutic_note": "Potential underlying tension detected"
                }
            ))
        
        # Detect emotional state changes
        emotional_variance = self._calculate_emotional_variance()
        if emotional_variance > 0.3:
            intuition_events.append(MarkerEvent(
                event_type=MarkerEventType.INTUITION_SIGNAL,
                marker_id="intuition_emotional_state",
                category="INTUITION",
                confidence=0.58,
                timestamp=time.time(),
                metadata={
                    "pattern_type": "emotional_variance",
                    "variance_score": emotional_variance,
                    "therapeutic_note": "Emotional state fluctuation observed"
                }
            ))
        
        return intuition_events
    
    def _calculate_emotional_variance(self) -> float:
        """Calculate emotional variance from recent events"""
        if len(self.pattern_history) < 5:
            return 0.0
            
        # Simplified emotional variance calculation
        recent_confidences = [e.confidence for e in self.pattern_history[-10:]]
        if not recent_confidences:
            return 0.0
            
        mean_conf = sum(recent_confidences) / len(recent_confidences)
        variance = sum((c - mean_conf) ** 2 for c in recent_confidences) / len(recent_confidences)
        
        return variance

class RealTimeMarkerEngine:
    """Main real-time marker processing engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.event_callbacks: List[Callable[[MarkerEvent], None]] = []
        
        # Initialize processing components
        self.ato_heuristics = ATOHeuristics()
        self.sem_gating = SEMGating()
        self.clu_windowing = CLUWindowing()
        self.intuition_telemetry = IntuitionTelemetry()
        
        # Load configuration
        self._load_configuration()
        
        # Initialize marker loader if available
        self.marker_loader = None
        if MARKER_SYSTEM_AVAILABLE:
            try:
                self.marker_loader = MarkerLoader()
                self.marker_loader.load_all_markers()
                self.logger.info(f"Loaded {len(self.marker_loader._markers)} markers")
            except Exception as e:
                self.logger.warning(f"Could not load markers: {e}")
    
    def _load_configuration(self):
        """Load configuration from app config"""
        if not CONFIG_AVAILABLE:
            return
            
        # Load marker configuration
        marker_config = app_config.get_marker_config()
        realtime_config = marker_config.get('realtime', {})
        
        if realtime_config.get('enabled', True):
            confidence_threshold = realtime_config.get('confidence_threshold', 0.7)
            self.ato_heuristics.confidence_threshold = confidence_threshold
            self.sem_gating.gate_threshold = confidence_threshold
            
        # Load prosody configuration
        prosody_config = app_config.get('prosody', {})
        if not prosody_config.get('enabled', True):
            self.ato_heuristics.enabled = False
    
    def add_event_callback(self, callback: Callable[[MarkerEvent], None]):
        """Add callback for marker events"""
        self.event_callbacks.append(callback)
    
    def _emit_event(self, event: MarkerEvent):
        """Emit event to all callbacks"""
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Event callback error: {e}")
    
    async def process_audio_chunk(self, audio_data: bytes, timestamp: float, 
                                 sample_rate: int = 16000) -> List[MarkerEvent]:
        """Process audio chunk and return detected markers"""
        events = []
        
        try:
            # Extract prosody features (simplified)
            prosody_features = self._extract_prosody_features(audio_data, timestamp, sample_rate)
            
            # ATO heuristics analysis
            ato_events = self.ato_heuristics.analyze_prosody(prosody_features)
            
            # Apply SEM gating
            gated_events = [e for e in ato_events if self.sem_gating.gate_event(e)]
            
            # CLU windowing analysis
            for event in gated_events:
                clustered_events = self.clu_windowing.add_event(event)
                events.extend(clustered_events)
            
            # Add original gated events
            events.extend(gated_events)
            
            # INTUITION telemetry
            intuition_events = self.intuition_telemetry.analyze_patterns(events)
            events.extend(intuition_events)
            
            # Emit all events
            for event in events:
                self._emit_event(event)
            
            # Create audio processing event
            processing_event = MarkerEvent(
                event_type=MarkerEventType.AUDIO_CHUNK_PROCESSED,
                marker_id="audio_processing",
                category="SYSTEM",
                confidence=1.0,
                timestamp=timestamp,
                audio_chunk_id=str(hash(audio_data[:100])),
                metadata={
                    "chunk_size": len(audio_data),
                    "sample_rate": sample_rate,
                    "markers_detected": len(events)
                }
            )
            events.append(processing_event)
            self._emit_event(processing_event)
            
        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {e}")
            
        return events
    
    def _extract_prosody_features(self, audio_data: bytes, timestamp: float, 
                                 sample_rate: int) -> ProsodyFeatures:
        """Extract prosody features from audio data (simplified implementation)"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            if len(audio_array) == 0:
                return ProsodyFeatures(timestamp=timestamp)
            
            # Simplified prosody feature extraction
            # In a real implementation, this would use proper signal processing
            
            # F0 estimation (simplified)
            f0 = self._estimate_f0(audio_array, sample_rate)
            
            # RMS energy
            rms = np.sqrt(np.mean(audio_array ** 2))
            
            # Zero crossing rate
            zcr = np.mean(np.abs(np.diff(np.sign(audio_array)))) / 2
            
            # Spectral flatness (simplified)
            flatness = self._estimate_spectral_flatness(audio_array)
            
            # Voicing (simplified)
            voicing = min(1.0, max(0.0, (rms * 10) * (1 - zcr)))
            
            return ProsodyFeatures(
                f0=f0,
                rms=rms,
                zcr=zcr,
                flatness=flatness,
                voicing=voicing,
                timestamp=timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting prosody features: {e}")
            return ProsodyFeatures(timestamp=timestamp)
    
    def _estimate_f0(self, audio: np.ndarray, sample_rate: int) -> float:
        """Simplified F0 estimation"""
        if len(audio) < 100:
            return 0.0
            
        # Simple autocorrelation-based F0 estimation
        autocorr = np.correlate(audio, audio, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Find peak (simplified)
        min_period = int(sample_rate / 500)  # 500 Hz max
        max_period = int(sample_rate / 50)   # 50 Hz min
        
        if max_period < len(autocorr):
            peak_idx = np.argmax(autocorr[min_period:max_period]) + min_period
            if peak_idx > 0:
                f0 = sample_rate / peak_idx
                return min(500, max(50, f0))  # Clamp to reasonable range
        
        return 150.0  # Default F0
    
    def _estimate_spectral_flatness(self, audio: np.ndarray) -> float:
        """Simplified spectral flatness estimation"""
        if len(audio) < 100:
            return 0.5
            
        # Simple energy-based flatness measure
        energy = np.sum(audio ** 2)
        peak_energy = np.max(audio ** 2) * len(audio)
        
        if peak_energy > 0:
            flatness = energy / peak_energy
            return min(1.0, max(0.0, flatness))
        
        return 0.5

# Global engine instance
marker_engine = RealTimeMarkerEngine()