"""Scoring Engine für die Bewertung von Text-Chunks basierend auf Marker-Treffern."""

import logging
import time
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import numpy as np

from .score_models import (
    ScoringModel, ChunkScore, AggregatedScore, ScoringResult,
    ScoreType, ScoreComparison
)
from ..matcher.marker_models import MarkerMatch, MarkerCategory, MarkerSeverity
from ..chunker.chunk_models import TextChunk

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Engine zur Berechnung von Scores basierend auf Marker-Matches."""
    
    def __init__(self):
        self.models: Dict[str, ScoringModel] = {}
        self._initialize_default_models()
    
    def _initialize_default_models(self):
        """Initialisiert Standard-Scoring-Modelle."""
        
        # Manipulations-Index
        self.models["manipulation_index"] = ScoringModel(
            id="manipulation_index",
            name="Manipulations-Index",
            type=ScoreType.MANIPULATION_INDEX,
            description="Misst den Grad manipulativer Kommunikation",
            category_weights={
                MarkerCategory.MANIPULATION: 2.0,
                MarkerCategory.GASLIGHTING: 3.0,
                MarkerCategory.EMOTIONAL_ABUSE: 2.5,
                MarkerCategory.LOVE_BOMBING: 1.5,
                MarkerCategory.FRAUD: 3.0,
                MarkerCategory.POSITIVE: -1.0,  # Positive Marker reduzieren Score
                MarkerCategory.EMPATHY: -0.5,
                MarkerCategory.SUPPORT: -0.5
            },
            inverse_scale=False  # Höher = mehr Manipulation
        )
        
        # Beziehungsgesundheit
        self.models["relationship_health"] = ScoringModel(
            id="relationship_health",
            name="Beziehungsgesundheit",
            type=ScoreType.RELATIONSHIP_HEALTH,
            description="Bewertet die Gesundheit der Beziehungskommunikation",
            category_weights={
                MarkerCategory.POSITIVE: 2.0,
                MarkerCategory.EMPATHY: 2.5,
                MarkerCategory.SUPPORT: 2.0,
                MarkerCategory.CONFLICT_RESOLUTION: 1.5,
                MarkerCategory.MANIPULATION: -2.0,
                MarkerCategory.GASLIGHTING: -3.0,
                MarkerCategory.EMOTIONAL_ABUSE: -2.5,
                MarkerCategory.FRAUD: -3.0
            },
            inverse_scale=True  # Positive Marker erhöhen Score
        )
        
        # Fraud-Wahrscheinlichkeit
        self.models["fraud_probability"] = ScoringModel(
            id="fraud_probability",
            name="Fraud-Wahrscheinlichkeit",
            type=ScoreType.FRAUD_PROBABILITY,
            description="Wahrscheinlichkeit für Betrug/Scam",
            category_weights={
                MarkerCategory.FRAUD: 3.0,
                MarkerCategory.FINANCIAL_ABUSE: 2.5,
                MarkerCategory.LOVE_BOMBING: 1.5,
                MarkerCategory.MANIPULATION: 1.0,
                MarkerCategory.POSITIVE: -0.5,
                MarkerCategory.EMPATHY: -0.3
            },
            thresholds={
                "critical": 7.0,
                "warning": 5.0,
                "normal": 3.0,
                "low": 1.5
            }
        )
        
        # Kommunikationsqualität
        self.models["communication_quality"] = ScoringModel(
            id="communication_quality",
            name="Kommunikationsqualität",
            type=ScoreType.COMMUNICATION_QUALITY,
            description="Qualität der Kommunikation",
            category_weights={
                MarkerCategory.POSITIVE: 1.5,
                MarkerCategory.EMPATHY: 2.0,
                MarkerCategory.SUPPORT: 1.5,
                MarkerCategory.CONFLICT_RESOLUTION: 2.0,
                MarkerCategory.BOUNDARY_SETTING: 1.0,
                MarkerCategory.SELF_CARE: 0.5,
                MarkerCategory.MANIPULATION: -1.5,
                MarkerCategory.GASLIGHTING: -2.0,
                MarkerCategory.EMOTIONAL_ABUSE: -2.0
            },
            inverse_scale=True
        )
    
    def calculate_scores(
        self,
        chunks: List[TextChunk],
        matches: List[MarkerMatch],
        models: Optional[List[str]] = None
    ) -> ScoringResult:
        """Berechnet Scores für gegebene Chunks und Matches.
        
        Args:
            chunks: Liste von Text-Chunks
            matches: Liste von Marker-Matches
            models: Spezifische Modelle zur Verwendung (None = alle)
            
        Returns:
            ScoringResult mit allen berechneten Scores
        """
        start_time = time.time()
        result = ScoringResult()
        
        # Wähle Modelle
        active_models = self._get_active_models(models)
        
        # Gruppiere Matches nach Chunk
        matches_by_chunk = self._group_matches_by_chunk(matches)
        
        # Berechne Scores pro Chunk
        for chunk in chunks:
            chunk_matches = matches_by_chunk.get(chunk.id, [])
            
            for model in active_models:
                chunk_score = self._calculate_chunk_score(
                    chunk,
                    chunk_matches,
                    model
                )
                result.chunk_scores.append(chunk_score)
        
        # Aggregiere Scores
        result.aggregated_scores = self._aggregate_scores(
            result.chunk_scores,
            active_models
        )
        
        # Berechne Speaker-Scores
        result.speaker_scores = self._calculate_speaker_scores(
            chunks,
            result.chunk_scores
        )
        
        # Erstelle Timeline
        result.timeline = self._create_timeline(result.chunk_scores)
        
        # Generiere Alerts
        result.alerts = self._generate_alerts(result.aggregated_scores)
        
        # Erstelle Summary
        result.summary = self._create_summary(result)
        
        result.processing_time = time.time() - start_time
        logger.info(f"Scoring abgeschlossen in {result.processing_time:.2f}s")
        
        return result
    
    def _calculate_chunk_score(
        self,
        chunk: TextChunk,
        matches: List[MarkerMatch],
        model: ScoringModel
    ) -> ChunkScore:
        """Berechnet Score für einen einzelnen Chunk."""
        raw_score = 0.0
        contributing_markers = []
        
        # Berechne gewichteten Score basierend auf Matches
        for match in matches:
            if match.category in model.category_weights:
                weight = model.category_weights[match.category]
                severity_mult = model.severity_multipliers.get(
                    match.severity,
                    1.0
                )
                
                # Marker-spezifisches Gewicht aus Metadaten
                marker_weight = match.metadata.get('weight', 1.0)
                
                contribution = weight * severity_mult * marker_weight * match.confidence
                raw_score += contribution
                
                contributing_markers.append({
                    'marker_id': match.marker_id,
                    'marker_name': match.marker_name,
                    'category': match.category.value,
                    'severity': match.severity.value,
                    'contribution': contribution,
                    'confidence': match.confidence
                })
        
        # Normalisiere Score
        normalized_score = self._normalize_score(raw_score, model, chunk.word_count)
        
        # Erstelle ChunkScore
        return ChunkScore(
            chunk_id=chunk.id,
            model_id=model.id,
            score_type=model.type,
            raw_score=raw_score,
            normalized_score=normalized_score,
            contributing_markers=contributing_markers,
            confidence=self._calculate_confidence(matches, model),
            timestamp=chunk.timestamp,
            metadata={
                'word_count': chunk.word_count,
                'marker_count': len(matches)
            }
        )
    
    def _normalize_score(
        self,
        raw_score: float,
        model: ScoringModel,
        word_count: int
    ) -> float:
        """Normalisiert einen Raw-Score auf die 1-10 Skala."""
        # Normalisiere basierend auf Wortanzahl
        if word_count > 0:
            normalized = (raw_score / word_count) * model.normalization_factor
        else:
            normalized = 0.0
        
        # Inverse Skalierung wenn nötig
        if model.inverse_scale:
            # Bei inverser Skala: Negative Werte = hoher Score
            if normalized < 0:
                score = model.scale_max + (normalized / 10)  # Skaliere negative Werte
            else:
                score = model.scale_max - (normalized * 2)  # Positive reduzieren Score
        else:
            # Normale Skala: Positive Werte = hoher Score
            score = model.scale_min + (normalized * 2)
        
        # Begrenze auf Min/Max
        return max(model.scale_min, min(model.scale_max, score))
    
    def _calculate_confidence(
        self,
        matches: List[MarkerMatch],
        model: ScoringModel
    ) -> float:
        """Berechnet Konfidenz des Scores basierend auf Matches."""
        if not matches:
            return 0.5  # Niedrige Konfidenz ohne Matches
        
        # Durchschnittliche Match-Konfidenz
        avg_confidence = sum(m.confidence for m in matches) / len(matches)
        
        # Anzahl relevanter Matches
        relevant_matches = [
            m for m in matches 
            if m.category in model.category_weights
        ]
        
        # Konfidenz steigt mit Anzahl relevanter Matches
        count_factor = min(1.0, len(relevant_matches) / 10)
        
        return avg_confidence * 0.7 + count_factor * 0.3
    
    def _aggregate_scores(
        self,
        chunk_scores: List[ChunkScore],
        models: List[ScoringModel]
    ) -> Dict[str, AggregatedScore]:
        """Aggregiert Chunk-Scores zu Gesamt-Scores."""
        aggregated = {}
        
        for model in models:
            model_scores = [
                cs for cs in chunk_scores 
                if cs.model_id == model.id
            ]
            
            if not model_scores:
                continue
            
            scores = [cs.normalized_score for cs in model_scores]
            
            # Berechne Trend
            trend, trend_strength = self._calculate_trend(scores)
            
            # Score-Verteilung
            distribution = self._calculate_distribution(scores)
            
            # Top Marker
            all_markers = []
            for cs in model_scores:
                all_markers.extend(cs.contributing_markers)
            
            marker_counts = defaultdict(int)
            for marker in all_markers:
                marker_counts[marker['marker_name']] += 1
            
            top_markers = [
                {'name': name, 'count': count}
                for name, count in sorted(
                    marker_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            ]
            
            aggregated[model.type.value] = AggregatedScore(
                model_id=model.id,
                score_type=model.type,
                average_score=np.mean(scores),
                min_score=min(scores),
                max_score=max(scores),
                trend=trend,
                trend_strength=trend_strength,
                chunk_count=len(model_scores),
                distribution=distribution,
                top_markers=top_markers
            )
        
        return aggregated
    
    def _calculate_trend(
        self,
        scores: List[float]
    ) -> Tuple[str, float]:
        """Berechnet Trend aus einer Score-Serie."""
        if len(scores) < 3:
            return "stable", 0.0
        
        # Einfache lineare Regression
        x = np.arange(len(scores))
        y = np.array(scores)
        
        # Berechne Steigung
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalisiere Steigung
        normalized_slope = slope / np.mean(scores) if np.mean(scores) > 0 else 0
        
        if normalized_slope > 0.1:
            return "improving", min(1.0, normalized_slope)
        elif normalized_slope < -0.1:
            return "declining", max(-1.0, normalized_slope)
        else:
            return "stable", normalized_slope
    
    def _calculate_distribution(
        self,
        scores: List[float]
    ) -> Dict[str, int]:
        """Berechnet Score-Verteilung."""
        distribution = {
            "1-2": 0,
            "3-4": 0,
            "5-6": 0,
            "7-8": 0,
            "9-10": 0
        }
        
        for score in scores:
            if score <= 2:
                distribution["1-2"] += 1
            elif score <= 4:
                distribution["3-4"] += 1
            elif score <= 6:
                distribution["5-6"] += 1
            elif score <= 8:
                distribution["7-8"] += 1
            else:
                distribution["9-10"] += 1
        
        return distribution
    
    def _calculate_speaker_scores(
        self,
        chunks: List[TextChunk],
        chunk_scores: List[ChunkScore]
    ) -> Dict[str, Dict[str, AggregatedScore]]:
        """Berechnet Scores pro Sprecher."""
        speaker_scores = defaultdict(lambda: defaultdict(list))
        
        # Sammle Scores pro Sprecher
        for chunk, scores in zip(chunks, chunk_scores):
            if chunk.speaker:
                speaker_name = chunk.speaker.name
                for score in [s for s in chunk_scores if s.chunk_id == chunk.id]:
                    speaker_scores[speaker_name][score.model_id].append(score)
        
        # Aggregiere pro Sprecher
        result = {}
        for speaker, model_scores in speaker_scores.items():
            result[speaker] = {}
            for model_id, scores in model_scores.items():
                model = self.models[model_id]
                result[speaker][model.type.value] = self._aggregate_scores(
                    scores,
                    [model]
                )[model.type.value]
        
        return result
    
    def _create_timeline(
        self,
        chunk_scores: List[ChunkScore]
    ) -> List[Dict[str, Any]]:
        """Erstellt Timeline der Score-Entwicklung."""
        timeline = []
        
        # Gruppiere nach Zeitstempel
        scores_by_time = defaultdict(lambda: defaultdict(list))
        
        for score in chunk_scores:
            if score.timestamp:
                # Runde auf Stunde
                hour = score.timestamp.replace(minute=0, second=0, microsecond=0)
                scores_by_time[hour][score.model_id].append(score.normalized_score)
        
        # Erstelle Timeline-Einträge
        for timestamp in sorted(scores_by_time.keys()):
            entry = {
                'timestamp': timestamp.isoformat(),
                'scores': {}
            }
            
            for model_id, scores in scores_by_time[timestamp].items():
                model = self.models[model_id]
                entry['scores'][model.type.value] = {
                    'average': np.mean(scores),
                    'min': min(scores),
                    'max': max(scores),
                    'count': len(scores)
                }
            
            timeline.append(entry)
        
        return timeline
    
    def _generate_alerts(
        self,
        aggregated_scores: Dict[str, AggregatedScore]
    ) -> List[Dict[str, Any]]:
        """Generiert Alerts basierend auf Score-Schwellenwerten."""
        alerts = []
        
        for score_type, agg_score in aggregated_scores.items():
            model = self.models[agg_score.model_id]
            
            # Prüfe Schwellenwerte
            for level, threshold in model.thresholds.items():
                if model.inverse_scale:
                    # Bei inverser Skala: Niedrige Scores sind schlecht
                    if agg_score.average_score <= threshold and level in ['warning', 'critical']:
                        alerts.append({
                            'level': level,
                            'type': score_type,
                            'message': f"{model.name} ist {level}: {agg_score.average_score:.1f}",
                            'score': agg_score.average_score,
                            'threshold': threshold
                        })
                else:
                    # Normale Skala: Hohe Scores sind schlecht
                    if agg_score.average_score >= threshold and level in ['warning', 'critical']:
                        alerts.append({
                            'level': level,
                            'type': score_type,
                            'message': f"{model.name} ist {level}: {agg_score.average_score:.1f}",
                            'score': agg_score.average_score,
                            'threshold': threshold
                        })
        
        return sorted(alerts, key=lambda x: x['level'] == 'critical', reverse=True)
    
    def _create_summary(self, result: ScoringResult) -> Dict[str, Any]:
        """Erstellt Zusammenfassung der wichtigsten Erkenntnisse."""
        summary = {
            'total_chunks_analyzed': len(result.chunk_scores),
            'models_used': list(result.aggregated_scores.keys()),
            'critical_alerts': len([a for a in result.alerts if a['level'] == 'critical']),
            'warning_alerts': len([a for a in result.alerts if a['level'] == 'warning']),
            'speaker_count': len(result.speaker_scores),
            'key_insights': []
        }
        
        # Wichtigste Erkenntnisse
        for score_type, agg_score in result.aggregated_scores.items():
            insight = {
                'type': score_type,
                'score': agg_score.average_score,
                'trend': agg_score.trend,
                'interpretation': self._interpret_score(score_type, agg_score.average_score)
            }
            summary['key_insights'].append(insight)
        
        return summary
    
    def _interpret_score(self, score_type: str, score: float) -> str:
        """Interpretiert einen Score verbal."""
        model = next((m for m in self.models.values() if m.type.value == score_type), None)
        if not model:
            return "Unbekannt"
        
        if model.inverse_scale:
            if score >= 8:
                return "Ausgezeichnet"
            elif score >= 6:
                return "Gut"
            elif score >= 4:
                return "Durchschnittlich"
            elif score >= 2:
                return "Problematisch"
            else:
                return "Kritisch"
        else:
            if score <= 2:
                return "Sehr niedrig"
            elif score <= 4:
                return "Niedrig"
            elif score <= 6:
                return "Mittel"
            elif score <= 8:
                return "Hoch"
            else:
                return "Sehr hoch"
    
    def _get_active_models(self, model_ids: Optional[List[str]] = None) -> List[ScoringModel]:
        """Gibt aktive Scoring-Modelle zurück."""
        if model_ids:
            return [self.models[mid] for mid in model_ids if mid in self.models and self.models[mid].active]
        else:
            return [m for m in self.models.values() if m.active]
    
    def _group_matches_by_chunk(self, matches: List[MarkerMatch]) -> Dict[str, List[MarkerMatch]]:
        """Gruppiert Matches nach Chunk-ID."""
        grouped = defaultdict(list)
        for match in matches:
            grouped[match.chunk_id].append(match)
        return grouped
    
    def add_custom_model(self, model: ScoringModel):
        """Fügt ein benutzerdefiniertes Scoring-Modell hinzu."""
        self.models[model.id] = model
        logger.info(f"Custom Scoring-Modell '{model.name}' hinzugefügt")
    
    def get_model(self, model_id: str) -> Optional[ScoringModel]:
        """Gibt ein spezifisches Scoring-Modell zurück."""
        return self.models.get(model_id)