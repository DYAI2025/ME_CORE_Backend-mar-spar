"""Datenmodelle für Text-Chunks."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ChunkType(str, Enum):
    """Typ eines Text-Chunks."""
    
    MESSAGE = "message"
    PARAGRAPH = "paragraph"
    CONVERSATION = "conversation"
    TIME_WINDOW = "time_window"
    SPEAKER_TURN = "speaker_turn"


class Speaker(BaseModel):
    """Information über einen Sprecher/Autor."""
    
    id: str = Field(..., description="Eindeutige ID des Sprechers")
    name: str = Field(..., description="Name oder Alias")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TextChunk(BaseModel):
    """Ein segmentierter Text-Abschnitt zur Analyse."""
    
    id: str = Field(..., description="Eindeutige Chunk-ID")
    type: ChunkType = Field(..., description="Art des Chunks")
    
    text: str = Field(..., description="Der eigentliche Text-Inhalt")
    original_text: Optional[str] = Field(None, description="Original-Text vor Bereinigung")
    
    speaker: Optional[Speaker] = Field(None, description="Sprecher/Autor")
    timestamp: Optional[datetime] = Field(None, description="Zeitstempel")
    
    start_pos: int = Field(..., description="Startposition im Gesamttext")
    end_pos: int = Field(..., description="Endposition im Gesamttext")
    
    word_count: int = Field(0, description="Anzahl Wörter")
    char_count: int = Field(0, description="Anzahl Zeichen")
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Zusätzliche Metadaten (z.B. Plattform, Thread-ID)"
    )
    
    previous_chunk_id: Optional[str] = Field(None, description="ID des vorherigen Chunks")
    next_chunk_id: Optional[str] = Field(None, description="ID des nächsten Chunks")
    
    @validator('word_count', always=True)
    def calculate_word_count(cls, v, values):
        """Berechnet Wortanzahl wenn nicht gesetzt."""
        if v == 0 and 'text' in values:
            return len(values['text'].split())
        return v
    
    @validator('char_count', always=True)
    def calculate_char_count(cls, v, values):
        """Berechnet Zeichenanzahl wenn nicht gesetzt."""
        if v == 0 and 'text' in values:
            return len(values['text'])
        return v
    
    def get_context(self, words_before: int = 5, words_after: int = 5) -> str:
        """Gibt Kontext um eine Position im Chunk zurück."""
        words = self.text.split()
        return ' '.join(words[:words_before + words_after + 1])


class ChunkingConfig(BaseModel):
    """Konfiguration für das Text-Chunking."""
    
    # Größen-Limits
    max_chunk_size: int = Field(
        default=1000,
        description="Maximale Chunk-Größe in Zeichen"
    )
    min_chunk_size: int = Field(
        default=50,
        description="Minimale Chunk-Größe in Zeichen"
    )
    
    # Chunking-Strategien
    chunk_by_speaker: bool = Field(
        default=True,
        description="Bei Sprecherwechsel neuen Chunk beginnen"
    )
    chunk_by_time: bool = Field(
        default=True,
        description="Bei Zeitsprüngen neuen Chunk beginnen"
    )
    time_gap_minutes: int = Field(
        default=30,
        description="Zeitlücke in Minuten für neuen Chunk"
    )
    
    # Text-Verarbeitung
    preserve_formatting: bool = Field(
        default=False,
        description="Original-Formatierung beibehalten"
    )
    normalize_whitespace: bool = Field(
        default=True,
        description="Mehrfache Leerzeichen normalisieren"
    )
    
    # Overlap für Kontext
    overlap_size: int = Field(
        default=50,
        description="Überlappung zwischen Chunks in Zeichen"
    )
    
    # Metadaten
    extract_timestamps: bool = Field(
        default=True,
        description="Zeitstempel aus Text extrahieren"
    )
    extract_speakers: bool = Field(
        default=True,
        description="Sprecher aus Text extrahieren"
    )


class ChunkingResult(BaseModel):
    """Ergebnis des Chunking-Prozesses."""
    
    chunks: List[TextChunk] = Field(default_factory=list)
    total_chunks: int = Field(0)
    
    speakers: List[Speaker] = Field(
        default_factory=list,
        description="Alle identifizierten Sprecher"
    )
    
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistiken über das Chunking"
    )
    
    errors: List[str] = Field(
        default_factory=list,
        description="Aufgetretene Fehler/Warnungen"
    )
    
    processing_time: float = Field(
        0.0,
        description="Verarbeitungszeit in Sekunden"
    )
    
    @validator('total_chunks', always=True)
    def calculate_total(cls, v, values):
        """Berechnet Gesamtzahl wenn nicht gesetzt."""
        if v == 0 and 'chunks' in values:
            return len(values['chunks'])
        return v
    
    def get_chunks_by_speaker(self, speaker_id: str) -> List[TextChunk]:
        """Gibt alle Chunks eines Sprechers zurück."""
        return [c for c in self.chunks if c.speaker and c.speaker.id == speaker_id]
    
    def get_chunks_in_timerange(
        self, 
        start: datetime, 
        end: datetime
    ) -> List[TextChunk]:
        """Gibt Chunks in einem Zeitbereich zurück."""
        return [
            c for c in self.chunks 
            if c.timestamp and start <= c.timestamp <= end
        ]