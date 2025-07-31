"""Fuzzy-Matching Engine für flexible Marker-Erkennung."""

import re
from typing import List, Tuple, Optional, Dict
from difflib import SequenceMatcher
import logging

try:
    from fuzzywuzzy import fuzz, process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy nicht installiert, verwende Fallback")

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """Engine für Fuzzy-String-Matching."""
    
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.use_fuzzywuzzy = FUZZYWUZZY_AVAILABLE
        
    def find_fuzzy_matches(
        self,
        text: str,
        patterns: List[str],
        threshold: Optional[float] = None
    ) -> List[Tuple[str, int, int, float]]:
        """Findet Fuzzy-Matches in einem Text.
        
        Args:
            text: Der zu durchsuchende Text
            patterns: Liste von Patterns zum Suchen
            threshold: Mindest-Ähnlichkeit (0-1)
            
        Returns:
            Liste von (matched_text, start_pos, end_pos, confidence)
        """
        if threshold is None:
            threshold = self.threshold
            
        matches = []
        text_lower = text.lower()
        words = text.split()
        
        for pattern in patterns:
            pattern_lower = pattern.lower()
            pattern_words = pattern.split()
            pattern_len = len(pattern_words)
            
            # Exakte Substring-Suche zuerst
            start = 0
            while True:
                pos = text_lower.find(pattern_lower, start)
                if pos == -1:
                    break
                matches.append((
                    text[pos:pos + len(pattern)],
                    pos,
                    pos + len(pattern),
                    1.0  # Exakter Match = 100% Konfidenz
                ))
                start = pos + 1
            
            # Fuzzy-Matching auf Wort-Ebene
            if pattern_len <= len(words):
                for i in range(len(words) - pattern_len + 1):
                    window = words[i:i + pattern_len]
                    window_text = ' '.join(window)
                    
                    similarity = self._calculate_similarity(
                        window_text.lower(),
                        pattern_lower
                    )
                    
                    if similarity >= threshold:
                        # Finde Position im Original-Text
                        start_pos = text.find(window[0], 0 if i == 0 else len(' '.join(words[:i])))
                        end_pos = text.find(window[-1], start_pos) + len(window[-1])
                        
                        matches.append((
                            text[start_pos:end_pos],
                            start_pos,
                            end_pos,
                            similarity
                        ))
        
        # Deduplizierung - behalte nur beste Matches für überlappende Bereiche
        matches = self._deduplicate_matches(matches)
        
        return matches
    
    def find_semantic_matches(
        self,
        text: str,
        semantic_groups: Dict[str, List[str]],
        threshold: Optional[float] = None
    ) -> List[Tuple[str, str, int, int, float]]:
        """Findet semantisch ähnliche Matches.
        
        Args:
            text: Der zu durchsuchende Text
            semantic_groups: Dict von Gruppe -> Synonyme/Varianten
            threshold: Mindest-Ähnlichkeit
            
        Returns:
            Liste von (group_name, matched_text, start_pos, end_pos, confidence)
        """
        if threshold is None:
            threshold = self.threshold
            
        semantic_matches = []
        
        for group_name, variants in semantic_groups.items():
            matches = self.find_fuzzy_matches(text, variants, threshold)
            
            for match_text, start, end, conf in matches:
                semantic_matches.append((
                    group_name,
                    match_text,
                    start,
                    end,
                    conf
                ))
        
        return semantic_matches
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Berechnet Ähnlichkeit zwischen zwei Strings."""
        if self.use_fuzzywuzzy:
            # Verwende verschiedene Fuzzy-Metriken und nimm Maximum
            ratio = fuzz.ratio(str1, str2) / 100.0
            partial = fuzz.partial_ratio(str1, str2) / 100.0
            token_sort = fuzz.token_sort_ratio(str1, str2) / 100.0
            
            return max(ratio, partial, token_sort)
        else:
            # Fallback: SequenceMatcher
            return SequenceMatcher(None, str1, str2).ratio()
    
    def _deduplicate_matches(
        self,
        matches: List[Tuple[str, int, int, float]]
    ) -> List[Tuple[str, int, int, float]]:
        """Entfernt überlappende Matches, behält die mit höchster Konfidenz."""
        if not matches:
            return []
        
        # Sortiere nach Konfidenz (absteigend) und dann Position
        sorted_matches = sorted(matches, key=lambda x: (-x[3], x[1]))
        
        deduplicated = []
        used_ranges = []
        
        for match in sorted_matches:
            _, start, end, _ = match
            
            # Prüfe Überlappung mit bereits verwendeten Bereichen
            overlaps = False
            for used_start, used_end in used_ranges:
                if not (end <= used_start or start >= used_end):
                    overlaps = True
                    break
            
            if not overlaps:
                deduplicated.append(match)
                used_ranges.append((start, end))
        
        # Sortiere nach Position für Output
        return sorted(deduplicated, key=lambda x: x[1])


class RegexMatcher:
    """Engine für Regex-basiertes Matching."""
    
    def __init__(self):
        self._compiled_patterns: Dict[str, re.Pattern] = {}
    
    def find_regex_matches(
        self,
        text: str,
        patterns: List[str],
        case_sensitive: bool = False
    ) -> List[Tuple[str, int, int]]:
        """Findet Regex-Matches in einem Text.
        
        Args:
            text: Der zu durchsuchende Text
            patterns: Liste von Regex-Patterns
            case_sensitive: Groß-/Kleinschreibung beachten
            
        Returns:
            Liste von (matched_text, start_pos, end_pos)
        """
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for pattern in patterns:
            try:
                # Compile und cache Pattern
                cache_key = f"{pattern}_{flags}"
                if cache_key not in self._compiled_patterns:
                    self._compiled_patterns[cache_key] = re.compile(pattern, flags)
                
                regex = self._compiled_patterns[cache_key]
                
                for match in regex.finditer(text):
                    matches.append((
                        match.group(),
                        match.start(),
                        match.end()
                    ))
                    
            except re.error as e:
                logger.error(f"Ungültiges Regex-Pattern '{pattern}': {e}")
                continue
        
        return matches
    
    def extract_context(
        self,
        text: str,
        position: int,
        context_words: int = 10
    ) -> str:
        """Extrahiert Kontext um eine Position im Text.
        
        Args:
            text: Der Gesamttext
            position: Position im Text
            context_words: Anzahl Wörter vor/nach der Position
            
        Returns:
            Kontext-String
        """
        words = text.split()
        word_positions = []
        current_pos = 0
        
        # Finde Wort-Positionen
        for word in words:
            word_start = text.find(word, current_pos)
            word_end = word_start + len(word)
            word_positions.append((word_start, word_end))
            current_pos = word_end
        
        # Finde Wort, das die Position enthält
        target_word_idx = 0
        for i, (start, end) in enumerate(word_positions):
            if start <= position <= end:
                target_word_idx = i
                break
        
        # Extrahiere Kontext
        start_idx = max(0, target_word_idx - context_words)
        end_idx = min(len(words), target_word_idx + context_words + 1)
        
        context_words_list = words[start_idx:end_idx]
        
        # Markiere Target
        if start_idx < target_word_idx < end_idx:
            relative_idx = target_word_idx - start_idx
            context_words_list[relative_idx] = f"**{context_words_list[relative_idx]}**"
        
        return ' '.join(context_words_list)