"""Konfigurationslader für Marker-Definitionen aus verschiedenen Formaten."""

import json
import yaml
import re
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
import logging
from dataclasses import dataclass

from ..matcher.marker_models import MarkerDefinition, MarkerPattern, MarkerCategory, MarkerSeverity


logger = logging.getLogger(__name__)


@dataclass
class MarkerConfig:
    """Globale Konfiguration für das Marker-System."""
    
    marker_directories: List[Path] = None
    auto_reload: bool = True
    cache_enabled: bool = True
    fuzzy_matching_default: bool = True
    default_context_words: int = 10
    
    def __post_init__(self):
        if self.marker_directories is None:
            self.marker_directories = [Path("markers")]


class MarkerLoader:
    """Lädt und verwaltet Marker-Definitionen aus verschiedenen Quellen."""
    
    def __init__(self, config: Optional[MarkerConfig] = None):
        self.config = config or MarkerConfig()
        self._markers: Dict[str, MarkerDefinition] = {}
        self._file_cache: Dict[str, float] = {}  # Datei -> Zeitstempel
        
    def load_all_markers(self) -> Dict[str, MarkerDefinition]:
        """Lädt alle Marker aus den konfigurierten Verzeichnissen."""
        self._markers.clear()
        
        for directory in self.config.marker_directories:
            if not directory.exists():
                logger.warning(f"Marker-Verzeichnis existiert nicht: {directory}")
                continue
                
            # YAML-Dateien
            for yaml_file in directory.glob("*.yaml"):
                try:
                    markers = self.load_yaml_markers(yaml_file)
                    self._merge_markers(markers)
                except Exception as e:
                    logger.error(f"Fehler beim Laden von {yaml_file}: {e}")
            
            # JSON-Dateien
            for json_file in directory.glob("*.json"):
                try:
                    markers = self.load_json_markers(json_file)
                    self._merge_markers(markers)
                except Exception as e:
                    logger.error(f"Fehler beim Laden von {json_file}: {e}")
            
            # TXT-Dateien (einfaches Format)
            for txt_file in directory.glob("*.txt"):
                try:
                    markers = self.load_txt_markers(txt_file)
                    self._merge_markers(markers)
                except Exception as e:
                    logger.error(f"Fehler beim Laden von {txt_file}: {e}")
        
        logger.info(f"Gesamt {len(self._markers)} Marker geladen")
        return self._markers
    
    def load_yaml_markers(self, filepath: Path) -> List[MarkerDefinition]:
        """Lädt Marker aus einer YAML-Datei."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        markers = []
        if isinstance(data, dict) and 'markers' in data:
            marker_list = data['markers']
        elif isinstance(data, list):
            marker_list = data
        else:
            raise ValueError(f"Unerwartetes YAML-Format in {filepath}")
        
        for marker_data in marker_list:
            marker = self._parse_marker_data(marker_data)
            if marker:
                markers.append(marker)
        
        logger.info(f"Geladen: {len(markers)} Marker aus {filepath}")
        return markers
    
    def load_json_markers(self, filepath: Path) -> List[MarkerDefinition]:
        """Lädt Marker aus einer JSON-Datei."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        markers = []
        if isinstance(data, dict) and 'markers' in data:
            marker_list = data['markers']
        elif isinstance(data, list):
            marker_list = data
        else:
            raise ValueError(f"Unerwartetes JSON-Format in {filepath}")
        
        for marker_data in marker_list:
            marker = self._parse_marker_data(marker_data)
            if marker:
                markers.append(marker)
        
        logger.info(f"Geladen: {len(markers)} Marker aus {filepath}")
        return markers
    
    def load_txt_markers(self, filepath: Path) -> List[MarkerDefinition]:
        """Lädt Marker aus einer einfachen TXT-Datei.
        
        Format:
        # Kommentar
        MARKER_ID | Kategorie | Name | Pattern1, Pattern2, ...
        """
        markers = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Überspringe leere Zeilen und Kommentare
                if not line or line.startswith('#'):
                    continue
                
                parts = [p.strip() for p in line.split('|')]
                if len(parts) < 4:
                    logger.warning(f"Zeile {line_num} in {filepath} hat ungültiges Format")
                    continue
                
                marker_id, category, name, patterns = parts[0], parts[1], parts[2], parts[3]
                
                # Parse patterns
                pattern_list = [p.strip() for p in patterns.split(',')]
                
                try:
                    marker = MarkerDefinition(
                        id=marker_id,
                        name=name,
                        category=self._parse_category(category),
                        description=f"Marker aus {filepath.name}",
                        keywords=pattern_list,
                        weight=1.0
                    )
                    markers.append(marker)
                except Exception as e:
                    logger.error(f"Fehler beim Parsen von Zeile {line_num}: {e}")
        
        logger.info(f"Geladen: {len(markers)} Marker aus {filepath}")
        return markers
    
    def _parse_marker_data(self, data: Dict[str, Any]) -> Optional[MarkerDefinition]:
        """Parst Marker-Daten aus einem Dictionary."""
        try:
            # Basis-Felder
            marker_id = data.get('id', data.get('marker_id'))
            if not marker_id:
                logger.warning("Marker ohne ID gefunden, überspringe")
                return None
            
            # Patterns verarbeiten
            patterns = []
            if 'patterns' in data:
                for p in data['patterns']:
                    if isinstance(p, str):
                        patterns.append(MarkerPattern(pattern=p))
                    elif isinstance(p, dict):
                        patterns.append(MarkerPattern(**p))
            
            # Keywords
            keywords = data.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [keywords]
            
            # Kategorie parsen
            category = self._parse_category(data.get('category', 'manipulation'))
            
            # Severity parsen
            severity = self._parse_severity(data.get('severity', 'medium'))
            
            marker = MarkerDefinition(
                id=marker_id,
                name=data.get('name', marker_id),
                category=category,
                severity=severity,
                description=data.get('description', ''),
                patterns=patterns,
                keywords=keywords,
                examples=data.get('examples', []),
                weight=float(data.get('weight', 1.0)),
                metadata=data.get('metadata', {}),
                active=data.get('active', True)
            )
            
            return marker
            
        except Exception as e:
            logger.error(f"Fehler beim Parsen von Marker-Daten: {e}")
            return None
    
    def _parse_category(self, category_str: str) -> MarkerCategory:
        """Parst eine Kategorie-String zu MarkerCategory Enum."""
        category_str = category_str.lower().strip()
        
        # Mapping für alternative Namen
        category_map = {
            'scam': MarkerCategory.FRAUD,
            'romance_scam': MarkerCategory.FRAUD,
            'betrug': MarkerCategory.FRAUD,
            'manipulativ': MarkerCategory.MANIPULATION,
            'abuse': MarkerCategory.EMOTIONAL_ABUSE,
            'positiv': MarkerCategory.POSITIVE,
            'wertschätzung': MarkerCategory.POSITIVE,
            'unterstützung': MarkerCategory.SUPPORT,
        }
        
        # Erst im Mapping suchen
        if category_str in category_map:
            return category_map[category_str]
        
        # Dann versuchen direkt zu parsen
        try:
            return MarkerCategory(category_str)
        except ValueError:
            logger.warning(f"Unbekannte Kategorie '{category_str}', nutze MANIPULATION")
            return MarkerCategory.MANIPULATION
    
    def _parse_severity(self, severity_str: str) -> MarkerSeverity:
        """Parst eine Severity-String zu MarkerSeverity Enum."""
        severity_str = severity_str.lower().strip()
        
        severity_map = {
            'niedrig': MarkerSeverity.LOW,
            'gering': MarkerSeverity.LOW,
            'mittel': MarkerSeverity.MEDIUM,
            'hoch': MarkerSeverity.HIGH,
            'kritisch': MarkerSeverity.CRITICAL,
            'schwer': MarkerSeverity.HIGH,
        }
        
        if severity_str in severity_map:
            return severity_map[severity_str]
        
        try:
            return MarkerSeverity(severity_str)
        except ValueError:
            logger.warning(f"Unbekannte Severity '{severity_str}', nutze MEDIUM")
            return MarkerSeverity.MEDIUM
    
    def _merge_markers(self, new_markers: List[MarkerDefinition]):
        """Fügt neue Marker zum bestehenden Set hinzu."""
        for marker in new_markers:
            if marker.id in self._markers:
                logger.warning(f"Marker {marker.id} existiert bereits, wird überschrieben")
            self._markers[marker.id] = marker
    
    def get_marker(self, marker_id: str) -> Optional[MarkerDefinition]:
        """Gibt einen spezifischen Marker zurück."""
        return self._markers.get(marker_id)
    
    def get_markers_by_category(self, category: MarkerCategory) -> List[MarkerDefinition]:
        """Gibt alle Marker einer Kategorie zurück."""
        return [m for m in self._markers.values() if m.category == category]
    
    def get_active_markers(self) -> List[MarkerDefinition]:
        """Gibt nur aktive Marker zurück."""
        return [m for m in self._markers.values() if m.active]
    
    def reload_if_changed(self) -> bool:
        """Lädt Marker neu, wenn sich Dateien geändert haben."""
        if not self.config.auto_reload:
            return False
        
        changed = False
        for directory in self.config.marker_directories:
            if not directory.exists():
                continue
            
            for file in directory.glob("*.{yaml,json,txt}"):
                mtime = file.stat().st_mtime
                if file.as_posix() not in self._file_cache or \
                   self._file_cache[file.as_posix()] < mtime:
                    changed = True
                    break
        
        if changed:
            logger.info("Änderungen erkannt, lade Marker neu")
            self.load_all_markers()
            
        return changed