"""Datenmodelle für das Scoring-System."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..matcher.marker_models import MarkerCategory, MarkerSeverity


class ScoreType(str, Enum):
    """Verschiedene Score-Typen für unterschiedliche Analysen."""
    
    MANIPULATION_INDEX = "manipulation_index"
    RELATIONSHIP_HEALTH = "relationship_health"
    FRAUD_PROBABILITY = "fraud_probability"
    EMOTIONAL_SUPPORT = "emotional_support"
    CONFLICT_LEVEL = "conflict_level"
    COMMUNICATION_QUALITY = "communication_quality"
    TRUST_LEVEL = "trust_level"
    RESOURCE_BALANCE = "resource_balance"


class ScoringModel(BaseModel):
    """Definition eines Scoring-Modells."""
    
    id: str = Field(..., description="Eindeutige Model-ID")
    name: str = Field(..., description="Name des Scoring-Modells")
    type: ScoreType = Field(..., description="Typ des Scores")
    description: str = Field(..., description="Beschreibung des Modells")
    
    # Gewichtungen für verschiedene Marker-Kategorien
    category_weights: Dict[MarkerCategory, float] = Field(
        default_factory=dict,
        description="Gewichtung pro Marker-Kategorie"
    )
    
    # Gewichtungen für Severity-Level
    severity_multipliers: Dict[MarkerSeverity, float] = Field(
        default_factory=lambda: {
            MarkerSeverity.LOW: 0.5,
            MarkerSeverity.MEDIUM: 1.0,
            MarkerSeverity.HIGH: 2.0,
            MarkerSeverity.CRITICAL: 3.0
        },
        description="Multiplikatoren für Schweregrade"
    )
    
    # Score-Berechnung
    scale_min: float = Field(default=1.0, description="Minimaler Score")
    scale_max: float = Field(default=10.0, description="Maximaler Score")
    inverse_scale: bool = Field(
        default=False,
        description="Ob höhere Marker-Counts zu niedrigeren Scores führen"
    )
    
    # Normalisierung
    normalization_factor: float = Field(
        default=100.0,
        description="Faktor zur Normalisierung der Rohwerte"
    )
    
    # Schwellenwerte für Interpretation
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "critical": 8.0,
            "warning": 6.0,
            "normal": 4.0,
            "good": 2.0
        },
        description="Schwellenwerte für verschiedene Zustände"
    )
    
    active: bool = Field(default=True, description="Ob das Modell aktiv ist")


class ChunkScore(BaseModel):
    """Score für einen einzelnen Text-Chunk."""
    
    chunk_id: str = Field(..., description="ID des bewerteten Chunks")
    model_id: str = Field(..., description="ID des verwendeten Scoring-Modells")
    score_type: ScoreType = Field(..., description="Typ des Scores")
    
    raw_score: float = Field(..., description="Roher Score vor Normalisierung")
    normalized_score: float = Field(..., ge=1.0, le=10.0, description="Normalisierter Score (1-10)")
    
    contributing_markers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Marker die zum Score beigetragen haben"
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Konfidenz des Scores"
    )
    
    timestamp: Optional[datetime] = Field(None, description="Zeitstempel des Chunks")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('normalized_score')
    def validate_normalized_score(cls, v, values):
        """Stelle sicher, dass Score im gültigen Bereich ist."""
        if 'score_type' in values:
            return max(1.0, min(10.0, v))
        return v


class AggregatedScore(BaseModel):
    """Aggregierter Score über mehrere Chunks/Zeiträume."""
    
    model_id: str = Field(..., description="ID des Scoring-Modells")
    score_type: ScoreType = Field(..., description="Typ des Scores")
    
    average_score: float = Field(..., ge=1.0, le=10.0)
    min_score: float = Field(..., ge=1.0, le=10.0)
    max_score: float = Field(..., ge=1.0, le=10.0)
    
    trend: str = Field(
        default="stable",
        description="Trend: improving, declining, stable"
    )
    trend_strength: float = Field(
        default=0.0,
        description="Stärke des Trends (-1 bis 1)"
    )
    
    chunk_count: int = Field(..., description="Anzahl bewerteter Chunks")
    time_range: Optional[Dict[str, datetime]] = Field(
        None,
        description="Zeitbereich der Aggregation"
    )
    
    distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Verteilung der Scores (z.B. 1-2: 5, 3-4: 10, ...)"
    )
    
    top_markers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Häufigste beitragende Marker"
    )
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScoreComparison(BaseModel):
    """Vergleich von Scores zwischen Sprechern/Zeiträumen."""
    
    comparison_type: str = Field(..., description="speaker_comparison oder time_comparison")
    model_id: str = Field(..., description="Verwendetes Scoring-Modell")
    
    entities: List[str] = Field(
        ...,
        description="Verglichene Entitäten (Speaker-IDs oder Zeiträume)"
    )
    
    scores: Dict[str, AggregatedScore] = Field(
        ...,
        description="Scores pro Entität"
    )
    
    differences: Dict[str, float] = Field(
        default_factory=dict,
        description="Unterschiede zwischen Entitäten"
    )
    
    winner: Optional[str] = Field(
        None,
        description="Entität mit bestem Score (je nach Modell)"
    )
    
    insights: List[str] = Field(
        default_factory=list,
        description="Automatisch generierte Einsichten"
    )
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScoringResult(BaseModel):
    """Gesamtergebnis einer Scoring-Analyse."""
    
    chunk_scores: List[ChunkScore] = Field(
        default_factory=list,
        description="Einzelne Chunk-Scores"
    )
    
    aggregated_scores: Dict[str, AggregatedScore] = Field(
        default_factory=dict,
        description="Aggregierte Scores pro Modell"
    )
    
    speaker_scores: Dict[str, Dict[str, AggregatedScore]] = Field(
        default_factory=dict,
        description="Scores pro Sprecher und Modell"
    )
    
    timeline: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Zeitliche Entwicklung der Scores"
    )
    
    alerts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Generierte Warnungen basierend auf Schwellenwerten"
    )
    
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Zusammenfassung der wichtigsten Erkenntnisse"
    )
    
    processing_time: float = Field(0.0)
    
    def get_score_by_type(self, score_type: ScoreType) -> Optional[AggregatedScore]:
        """Holt aggregierten Score für einen bestimmten Typ."""
        return self.aggregated_scores.get(score_type.value)
    
    def get_speaker_comparison(self, score_type: ScoreType) -> ScoreComparison:
        """Erstellt Vergleich zwischen Sprechern für einen Score-Typ."""
        comparison = ScoreComparison(
            comparison_type="speaker_comparison",
            model_id=score_type.value,
            entities=list(self.speaker_scores.keys()),
            scores={}
        )
        
        for speaker, scores in self.speaker_scores.items():
            if score_type.value in scores:
                comparison.scores[speaker] = scores[score_type.value]
        
        # Berechne Unterschiede
        if len(comparison.scores) == 2:
            speakers = list(comparison.scores.keys())
            diff = comparison.scores[speakers[0]].average_score - comparison.scores[speakers[1]].average_score
            comparison.differences[f"{speakers[0]}_vs_{speakers[1]}"] = diff
        
        return comparison