"""Datenmodelle für Marker-Definitionen und -Treffer."""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class MarkerCategory(str, Enum):
    """Kategorien für verschiedene Marker-Typen."""
    
    FRAUD = "fraud"
    MANIPULATION = "manipulation"
    GASLIGHTING = "gaslighting"
    LOVE_BOMBING = "love_bombing"
    EMOTIONAL_ABUSE = "emotional_abuse"
    FINANCIAL_ABUSE = "financial_abuse"
    POSITIVE = "positive"
    EMPATHY = "empathy"
    SUPPORT = "support"
    CONFLICT_RESOLUTION = "conflict_resolution"
    BOUNDARY_SETTING = "boundary_setting"
    SELF_CARE = "self_care"


class MarkerSeverity(str, Enum):
    """Schweregrad eines Markers."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MarkerPattern(BaseModel):
    """Ein einzelnes Pattern zur Marker-Erkennung."""
    
    pattern: str = Field(..., description="Regex oder Text-Pattern")
    is_regex: bool = Field(default=False, description="Ob Pattern als Regex interpretiert werden soll")
    case_sensitive: bool = Field(default=False, description="Groß-/Kleinschreibung beachten")
    fuzzy_threshold: Optional[float] = Field(
        default=0.85, 
        ge=0.0, 
        le=1.0,
        description="Schwellenwert für Fuzzy-Matching (0-1)"
    )
    context_words: Optional[int] = Field(
        default=10,
        description="Anzahl Wörter für Kontext-Extraktion"
    )


class MarkerDefinition(BaseModel):
    """Definition eines Markers mit allen relevanten Eigenschaften."""
    
    id: str = Field(..., description="Eindeutige Marker-ID")
    name: str = Field(..., description="Menschenlesbarer Name")
    category: MarkerCategory = Field(..., description="Marker-Kategorie")
    severity: MarkerSeverity = Field(default=MarkerSeverity.MEDIUM)
    description: str = Field(..., description="Ausführliche Beschreibung")
    
    patterns: List[MarkerPattern] = Field(
        default_factory=list,
        description="Liste von Patterns zur Erkennung"
    )
    
    keywords: List[str] = Field(
        default_factory=list,
        description="Schlüsselwörter für einfaches Matching"
    )
    
    examples: List[str] = Field(
        default_factory=list,
        description="Beispiele für diesen Marker"
    )
    
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Gewichtung für Scoring (0-10)"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Zusätzliche Metadaten"
    )
    
    active: bool = Field(default=True, description="Ob Marker aktiv ist")
    
    @validator('patterns')
    def validate_patterns(cls, v):
        """Stelle sicher, dass mindestens ein Pattern oder Keyword existiert."""
        if not v:
            return v
        return v
    
    def get_all_patterns(self) -> List[str]:
        """Gibt alle Patterns und Keywords zurück."""
        all_patterns = []
        for p in self.patterns:
            all_patterns.append(p.pattern)
        all_patterns.extend(self.keywords)
        return all_patterns


class MarkerMatch(BaseModel):
    """Ein gefundener Marker-Treffer in einem Text."""
    
    marker_id: str = Field(..., description="ID des gefundenen Markers")
    marker_name: str = Field(..., description="Name des Markers")
    category: MarkerCategory = Field(..., description="Kategorie des Markers")
    severity: MarkerSeverity = Field(..., description="Schweregrad")
    
    text: str = Field(..., description="Gefundener Text")
    context: str = Field(..., description="Kontext um den Fund")
    
    chunk_id: str = Field(..., description="ID des Text-Chunks")
    position: int = Field(..., description="Position im Text")
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Konfidenz des Matches (0-1)"
    )
    
    speaker: Optional[str] = Field(None, description="Sprecher/Autor")
    timestamp: Optional[datetime] = Field(None, description="Zeitstempel")
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Zusätzliche Match-Metadaten"
    )


class MarkerStatistics(BaseModel):
    """Statistiken über Marker-Treffer."""
    
    total_matches: int = Field(default=0)
    matches_by_category: Dict[str, int] = Field(default_factory=dict)
    matches_by_severity: Dict[str, int] = Field(default_factory=dict)
    matches_by_speaker: Dict[str, int] = Field(default_factory=dict)
    
    average_confidence: float = Field(default=0.0)
    time_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Verteilung über Zeit (z.B. pro Stunde/Tag)"
    )
    
    most_frequent_markers: List[Dict[str, Union[str, int]]] = Field(
        default_factory=list,
        description="Top Marker nach Häufigkeit"
    )


class MarkerProfile(BaseModel):
    """Profil einer Person basierend auf Marker-Analyse."""
    
    speaker_id: str = Field(..., description="ID des Sprechers")
    total_messages: int = Field(default=0)
    
    positive_markers: int = Field(default=0)
    negative_markers: int = Field(default=0)
    
    dominant_categories: List[str] = Field(default_factory=list)
    risk_score: float = Field(default=0.0, ge=0.0, le=10.0)
    
    marker_timeline: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Zeitliche Entwicklung der Marker"
    )
    
    behavioral_patterns: Dict[str, Any] = Field(
        default_factory=dict,
        description="Erkannte Verhaltensmuster"
    )