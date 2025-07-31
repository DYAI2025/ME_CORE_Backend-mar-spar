"""Text Chunker für intelligente Text-Segmentierung."""

import re
import time
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
import logging
from uuid import uuid4

from .chunk_models import (
    TextChunk, ChunkType, Speaker, ChunkingConfig, ChunkingResult
)

logger = logging.getLogger(__name__)


class TextChunker:
    """Segmentiert Texte intelligent in analysierbare Chunks."""
    
    # Regex-Patterns für verschiedene Chat-Formate
    WHATSAPP_PATTERN = re.compile(
        r'(\d{1,2}[./]\d{1,2}[./]\d{2,4},?\s*\d{1,2}:\d{2}(?:\s*[AP]M)?)\s*-\s*([^:]+):\s*(.*)',
        re.MULTILINE
    )
    
    TELEGRAM_PATTERN = re.compile(
        r'\[(\d{1,2}\.\d{1,2}\.\d{2,4}\s+\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.*)',
        re.MULTILINE
    )
    
    GENERIC_PATTERN = re.compile(
        r'^([^:]+):\s*(.*)',
        re.MULTILINE
    )
    
    TIMESTAMP_PATTERNS = [
        # ISO format
        re.compile(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}'),
        # Deutsch
        re.compile(r'\d{1,2}\.\d{1,2}\.\d{2,4}\s+\d{1,2}:\d{2}'),
        # US
        re.compile(r'\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}'),
    ]
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
        self._speaker_map: Dict[str, Speaker] = {}
        
    def chunk_text(
        self, 
        text: str, 
        format_hint: Optional[str] = None
    ) -> ChunkingResult:
        """Hauptmethode zum Chunking von Text.
        
        Args:
            text: Der zu segmentierende Text
            format_hint: Hinweis auf Format (whatsapp, telegram, etc.)
            
        Returns:
            ChunkingResult mit allen Chunks und Metadaten
        """
        start_time = time.time()
        result = ChunkingResult()
        
        try:
            # Format erkennen
            chat_format = format_hint or self._detect_format(text)
            logger.info(f"Erkanntes Format: {chat_format}")
            
            # Parse Messages
            messages = self._parse_messages(text, chat_format)
            
            if not messages:
                # Fallback: Als einzelnen Chunk behandeln
                chunk = self._create_chunk(
                    text=text,
                    chunk_type=ChunkType.PARAGRAPH,
                    start_pos=0,
                    end_pos=len(text)
                )
                result.chunks = [chunk]
            else:
                # Chunks aus Messages erstellen
                result.chunks = self._create_chunks_from_messages(messages)
            
            # Speakers sammeln
            result.speakers = list(self._speaker_map.values())
            
            # Statistiken
            result.statistics = self._calculate_statistics(result.chunks)
            
        except Exception as e:
            logger.error(f"Fehler beim Chunking: {e}")
            result.errors.append(str(e))
        
        result.processing_time = time.time() - start_time
        return result
    
    def _detect_format(self, text: str) -> str:
        """Erkennt das Chat-Format automatisch."""
        # Teste verschiedene Patterns
        if self.WHATSAPP_PATTERN.search(text):
            return "whatsapp"
        elif self.TELEGRAM_PATTERN.search(text):
            return "telegram"
        elif self.GENERIC_PATTERN.search(text):
            return "generic"
        else:
            return "plain"
    
    def _parse_messages(
        self, 
        text: str, 
        format_type: str
    ) -> List[Dict[str, Any]]:
        """Parst Messages aus dem Text basierend auf Format."""
        messages = []
        
        if format_type == "whatsapp":
            pattern = self.WHATSAPP_PATTERN
        elif format_type == "telegram":
            pattern = self.TELEGRAM_PATTERN
        elif format_type == "generic":
            pattern = self.GENERIC_PATTERN
        else:
            # Plain text - keine Messages
            return []
        
        last_end = 0
        
        for match in pattern.finditer(text):
            if format_type in ["whatsapp", "telegram"]:
                timestamp_str, speaker, message = match.groups()
                timestamp = self._parse_timestamp(timestamp_str)
            else:
                speaker, message = match.groups()
                timestamp = None
            
            # Multi-line Messages zusammenführen
            start = match.start()
            end = match.end()
            
            # Finde nächste Message oder Ende
            next_match = pattern.search(text, end)
            if next_match:
                message_end = next_match.start()
            else:
                message_end = len(text)
            
            # Erweitere Message bis zur nächsten
            full_message = text[match.end():message_end].strip()
            if full_message:
                message = message + "\n" + full_message
            
            messages.append({
                'speaker': speaker.strip(),
                'text': message.strip(),
                'timestamp': timestamp,
                'start_pos': start,
                'end_pos': message_end
            })
            
            last_end = message_end
        
        return messages
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Versucht einen Zeitstempel zu parsen."""
        # Verschiedene Formate probieren
        formats = [
            "%d.%m.%Y %H:%M",
            "%d.%m.%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%m/%d/%Y %H:%M",
            "%d.%m.%y, %H:%M",
            "%d/%m/%y, %H:%M",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Konnte Zeitstempel nicht parsen: {timestamp_str}")
        return None
    
    def _create_chunks_from_messages(
        self, 
        messages: List[Dict[str, Any]]
    ) -> List[TextChunk]:
        """Erstellt Chunks aus geparsten Messages."""
        chunks = []
        current_chunk_messages = []
        current_speaker = None
        last_timestamp = None
        
        for i, msg in enumerate(messages):
            speaker_name = msg['speaker']
            timestamp = msg['timestamp']
            
            # Entscheide ob neuer Chunk nötig
            need_new_chunk = False
            
            # Bei Sprecherwechsel
            if self.config.chunk_by_speaker and speaker_name != current_speaker:
                need_new_chunk = True
            
            # Bei Zeitsprung
            if (self.config.chunk_by_time and 
                last_timestamp and timestamp and
                (timestamp - last_timestamp).total_seconds() > self.config.time_gap_minutes * 60):
                need_new_chunk = True
            
            # Bei Größenlimit
            current_size = sum(len(m['text']) for m in current_chunk_messages)
            if current_size + len(msg['text']) > self.config.max_chunk_size:
                need_new_chunk = True
            
            # Erstelle neuen Chunk wenn nötig
            if need_new_chunk and current_chunk_messages:
                chunk = self._create_chunk_from_messages(current_chunk_messages)
                chunks.append(chunk)
                current_chunk_messages = []
            
            current_chunk_messages.append(msg)
            current_speaker = speaker_name
            last_timestamp = timestamp
        
        # Letzten Chunk erstellen
        if current_chunk_messages:
            chunk = self._create_chunk_from_messages(current_chunk_messages)
            chunks.append(chunk)
        
        # Chunk-IDs verlinken
        for i in range(len(chunks)):
            if i > 0:
                chunks[i].previous_chunk_id = chunks[i-1].id
            if i < len(chunks) - 1:
                chunks[i].next_chunk_id = chunks[i+1].id
        
        return chunks
    
    def _create_chunk_from_messages(
        self, 
        messages: List[Dict[str, Any]]
    ) -> TextChunk:
        """Erstellt einen Chunk aus einer Liste von Messages."""
        # Text zusammenführen
        texts = []
        for msg in messages:
            if msg['timestamp']:
                texts.append(f"[{msg['timestamp']}] {msg['speaker']}: {msg['text']}")
            else:
                texts.append(f"{msg['speaker']}: {msg['text']}")
        
        combined_text = "\n".join(texts)
        
        # Speaker bestimmen
        speakers = list(set(msg['speaker'] for msg in messages))
        if len(speakers) == 1:
            speaker = self._get_or_create_speaker(speakers[0])
        else:
            speaker = None  # Multiple speakers in chunk
        
        # Timestamps
        timestamps = [msg['timestamp'] for msg in messages if msg['timestamp']]
        timestamp = timestamps[0] if timestamps else None
        
        return self._create_chunk(
            text=combined_text,
            chunk_type=ChunkType.CONVERSATION if len(speakers) > 1 else ChunkType.MESSAGE,
            speaker=speaker,
            timestamp=timestamp,
            start_pos=messages[0]['start_pos'],
            end_pos=messages[-1]['end_pos'],
            metadata={
                'message_count': len(messages),
                'speakers': speakers
            }
        )
    
    def _create_chunk(
        self,
        text: str,
        chunk_type: ChunkType,
        start_pos: int,
        end_pos: int,
        speaker: Optional[Speaker] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TextChunk:
        """Erstellt einen einzelnen Chunk."""
        chunk_id = f"chunk_{uuid4().hex[:8]}"
        
        # Text normalisieren wenn gewünscht
        if self.config.normalize_whitespace:
            text = ' '.join(text.split())
        
        return TextChunk(
            id=chunk_id,
            type=chunk_type,
            text=text,
            speaker=speaker,
            timestamp=timestamp,
            start_pos=start_pos,
            end_pos=end_pos,
            metadata=metadata or {}
        )
    
    def _get_or_create_speaker(self, name: str) -> Speaker:
        """Holt oder erstellt einen Speaker."""
        if name not in self._speaker_map:
            speaker_id = f"speaker_{len(self._speaker_map) + 1}"
            self._speaker_map[name] = Speaker(
                id=speaker_id,
                name=name
            )
        return self._speaker_map[name]
    
    def _calculate_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """Berechnet Statistiken über die Chunks."""
        if not chunks:
            return {}
        
        total_words = sum(c.word_count for c in chunks)
        total_chars = sum(c.char_count for c in chunks)
        
        # Zeitspanne
        timestamps = [c.timestamp for c in chunks if c.timestamp]
        if timestamps:
            time_span = max(timestamps) - min(timestamps)
            time_span_hours = time_span.total_seconds() / 3600
        else:
            time_span_hours = 0
        
        # Speaker-Statistiken
        speaker_stats = {}
        for chunk in chunks:
            if chunk.speaker:
                speaker_name = chunk.speaker.name
                if speaker_name not in speaker_stats:
                    speaker_stats[speaker_name] = {
                        'chunks': 0,
                        'words': 0,
                        'chars': 0
                    }
                speaker_stats[speaker_name]['chunks'] += 1
                speaker_stats[speaker_name]['words'] += chunk.word_count
                speaker_stats[speaker_name]['chars'] += chunk.char_count
        
        return {
            'total_chunks': len(chunks),
            'total_words': total_words,
            'total_chars': total_chars,
            'avg_chunk_size': total_chars / len(chunks) if chunks else 0,
            'time_span_hours': time_span_hours,
            'speaker_stats': speaker_stats,
            'chunk_types': {
                t.value: sum(1 for c in chunks if c.type == t)
                for t in ChunkType
            }
        }