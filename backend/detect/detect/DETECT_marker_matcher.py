"""Marker Matcher - Hauptmodul für Marker-Erkennung."""

import logging
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path

from .marker_models import (
    MarkerDefinition, MarkerMatch, MarkerStatistics, 
    MarkerCategory, MarkerSeverity
)
from .fuzzy_engine import FuzzyMatcher, RegexMatcher
from ..chunker.chunk_models import TextChunk
from ..config.config_loader import MarkerLoader, MarkerConfig

logger = logging.getLogger(__name__)


class MarkerMatcher:
    """Hauptklasse für Marker-Matching in Text-Chunks."""
    
    def __init__(
        self,
        config: Optional[MarkerConfig] = None,
        fuzzy_threshold: float = 0.85
    ):
        self.config = config or MarkerConfig()
        self.loader = MarkerLoader(config)
        self.fuzzy_matcher = FuzzyMatcher(fuzzy_threshold)
        self.regex_matcher = RegexMatcher()
        
        self._markers: Dict[str, MarkerDefinition] = {}
        self._semantic_groups: Dict[str, Dict[str, List[str]]] = {}
        
    def load_markers(self, path: Optional[Path] = None) -> int:
        """Lädt Marker-Definitionen.
        
        Args:
            path: Spezifischer Pfad zu Marker-Datei (optional)
            
        Returns:
            Anzahl geladener Marker
        """
        if path:
            # Lade spezifische Datei
            if path.suffix == '.yaml':
                markers = self.loader.load_yaml_markers(path)
            elif path.suffix == '.json':
                markers = self.loader.load_json_markers(path)
            elif path.suffix == '.txt':
                markers = self.loader.load_txt_markers(path)
            else:
                raise ValueError(f"Unbekanntes Dateiformat: {path.suffix}")
            
            for marker in markers:
                self._markers[marker.id] = marker
        else:
            # Lade alle Marker aus konfigurierten Verzeichnissen
            self._markers = self.loader.load_all_markers()
        
        # Baue semantische Gruppen
        self._build_semantic_groups()
        
        logger.info(f"Geladen: {len(self._markers)} Marker")
        return len(self._markers)
    
    def find_matches(
        self,
        chunks: List[TextChunk],
        categories: Optional[List[MarkerCategory]] = None,
        min_confidence: float = 0.7
    ) -> List[MarkerMatch]:
        """Findet alle Marker-Matches in den gegebenen Chunks.
        
        Args:
            chunks: Liste von Text-Chunks
            categories: Nur bestimmte Kategorien suchen (optional)
            min_confidence: Minimale Konfidenz für Matches
            
        Returns:
            Liste aller gefundenen Marker-Matches
        """
        all_matches = []
        
        # Lade Marker neu wenn Auto-Reload aktiv
        if self.config.auto_reload:
            self.loader.reload_if_changed()
        
        # Filtere Marker nach Kategorien
        active_markers = self._get_active_markers(categories)
        
        logger.info(f"Suche mit {len(active_markers)} aktiven Markern in {len(chunks)} Chunks")
        
        for chunk in chunks:
            chunk_matches = self._find_matches_in_chunk(
                chunk,
                active_markers,
                min_confidence
            )
            all_matches.extend(chunk_matches)
        
        logger.info(f"Gefunden: {len(all_matches)} Matches")
        return all_matches
    
    def find_matches_in_text(
        self,
        text: str,
        categories: Optional[List[MarkerCategory]] = None,
        min_confidence: float = 0.7
    ) -> List[MarkerMatch]:
        """Convenience-Methode für direktes Text-Matching.
        
        Args:
            text: Der zu analysierende Text
            categories: Nur bestimmte Kategorien suchen
            min_confidence: Minimale Konfidenz
            
        Returns:
            Liste der Matches
        """
        # Erstelle temporären Chunk
        temp_chunk = TextChunk(
            id="temp_chunk",
            type="message",
            text=text,
            start_pos=0,
            end_pos=len(text)
        )
        
        return self.find_matches([temp_chunk], categories, min_confidence)
    
    def get_statistics(
        self,
        matches: List[MarkerMatch]
    ) -> MarkerStatistics:
        """Berechnet Statistiken über gefundene Matches.
        
        Args:
            matches: Liste von Marker-Matches
            
        Returns:
            Statistik-Objekt
        """
        stats = MarkerStatistics()
        
        if not matches:
            return stats
        
        stats.total_matches = len(matches)
        
        # Zähle nach Kategorie
        for match in matches:
            cat = match.category.value
            stats.matches_by_category[cat] = stats.matches_by_category.get(cat, 0) + 1
            
            sev = match.severity.value
            stats.matches_by_severity[sev] = stats.matches_by_severity.get(sev, 0) + 1
            
            if match.speaker:
                speaker = match.speaker
                stats.matches_by_speaker[speaker] = stats.matches_by_speaker.get(speaker, 0) + 1
        
        # Durchschnittliche Konfidenz
        stats.average_confidence = sum(m.confidence for m in matches) / len(matches)
        
        # Häufigste Marker
        marker_counts: Dict[str, int] = {}
        for match in matches:
            marker_counts[match.marker_id] = marker_counts.get(match.marker_id, 0) + 1
        
        stats.most_frequent_markers = [
            {"marker_id": mid, "count": count}
            for mid, count in sorted(
                marker_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]
        
        return stats
    
    def _find_matches_in_chunk(
        self,
        chunk: TextChunk,
        markers: List[MarkerDefinition],
        min_confidence: float
    ) -> List[MarkerMatch]:
        """Findet Matches in einem einzelnen Chunk."""
        matches = []
        chunk_text = chunk.text
        
        for marker in markers:
            # Sammle alle Patterns
            patterns = marker.get_all_patterns()
            if not patterns:
                continue
            
            # Regex-Patterns
            regex_patterns = [
                p.pattern for p in marker.patterns 
                if p.is_regex
            ]
            
            if regex_patterns:
                regex_matches = self.regex_matcher.find_regex_matches(
                    chunk_text,
                    regex_patterns,
                    case_sensitive=any(p.case_sensitive for p in marker.patterns if p.is_regex)
                )
                
                for match_text, start, end in regex_matches:
                    context = self.regex_matcher.extract_context(
                        chunk_text,
                        start,
                        context_words=marker.patterns[0].context_words or 10
                    )
                    
                    match = MarkerMatch(
                        marker_id=marker.id,
                        marker_name=marker.name,
                        category=marker.category,
                        severity=marker.severity,
                        text=match_text,
                        context=context,
                        chunk_id=chunk.id,
                        position=chunk.start_pos + start,
                        confidence=1.0,  # Regex matches sind immer 100%
                        speaker=chunk.speaker.name if chunk.speaker else None,
                        timestamp=chunk.timestamp,
                        metadata={
                            "match_type": "regex",
                            "weight": marker.weight
                        }
                    )
                    matches.append(match)
            
            # Fuzzy-Matching für Keywords und nicht-Regex Patterns
            fuzzy_patterns = []
            fuzzy_patterns.extend(marker.keywords)
            fuzzy_patterns.extend([
                p.pattern for p in marker.patterns 
                if not p.is_regex
            ])
            
            if fuzzy_patterns:
                # Bestimme Threshold
                threshold = min(
                    p.fuzzy_threshold or self.fuzzy_matcher.threshold
                    for p in marker.patterns
                    if p.fuzzy_threshold is not None
                ) if marker.patterns else self.fuzzy_matcher.threshold
                
                fuzzy_matches = self.fuzzy_matcher.find_fuzzy_matches(
                    chunk_text,
                    fuzzy_patterns,
                    threshold=max(threshold, min_confidence)
                )
                
                for match_text, start, end, confidence in fuzzy_matches:
                    if confidence < min_confidence:
                        continue
                    
                    context = self.regex_matcher.extract_context(
                        chunk_text,
                        start,
                        context_words=marker.patterns[0].context_words if marker.patterns else 10
                    )
                    
                    match = MarkerMatch(
                        marker_id=marker.id,
                        marker_name=marker.name,
                        category=marker.category,
                        severity=marker.severity,
                        text=match_text,
                        context=context,
                        chunk_id=chunk.id,
                        position=chunk.start_pos + start,
                        confidence=confidence,
                        speaker=chunk.speaker.name if chunk.speaker else None,
                        timestamp=chunk.timestamp,
                        metadata={
                            "match_type": "fuzzy",
                            "weight": marker.weight
                        }
                    )
                    matches.append(match)
        
        return matches
    
    def _get_active_markers(
        self,
        categories: Optional[List[MarkerCategory]] = None
    ) -> List[MarkerDefinition]:
        """Gibt aktive Marker zurück, optional gefiltert nach Kategorien."""
        markers = [m for m in self._markers.values() if m.active]
        
        if categories:
            markers = [m for m in markers if m.category in categories]
        
        return markers
    
    def _build_semantic_groups(self):
        """Baut semantische Gruppen aus Marker-Definitionen."""
        self._semantic_groups.clear()
        
        for marker in self._markers.values():
            if not marker.active:
                continue
            
            # Gruppiere nach Kategorie
            cat_key = marker.category.value
            if cat_key not in self._semantic_groups:
                self._semantic_groups[cat_key] = {}
            
            # Füge Marker mit seinen Varianten hinzu
            all_patterns = marker.get_all_patterns()
            if all_patterns:
                self._semantic_groups[cat_key][marker.id] = all_patterns