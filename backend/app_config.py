#!/usr/bin/env python3
"""
Configuration loader for TransRapport Desktop MVP

Loads configuration from config/app.yaml and integrates with existing settings.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AppConfigLoader:
    """Loads and manages application configuration from config/app.yaml"""
    
    def __init__(self):
        self.config_path = Path("config/app.yaml")
        self.config: Optional[Dict[str, Any]] = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from app.yaml"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self.config = self._get_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "server": {
                "host": "127.0.0.1",
                "port": 8710,
                "title": "TransRapport Desktop MVP",
                "environment": "desktop"
            },
            "models": {
                "whisper": {
                    "path": "./models/whisper",
                    "model_size": "base",
                    "device": "cpu",
                    "compute_type": "int8"
                },
                "llm": {
                    "enabled": False,
                    "base_url": "http://127.0.0.1:1234/v1",
                    "model": "local-model",
                    "api_key": "not-needed",
                    "mode": "llm"
                }
            },
            "markers": {
                "directories": [
                    "./backend/markers/markers_yaml",
                    "./backend/markers/markers_json",
                    "./bundles"
                ],
                "bundles": [
                    {
                        "path": "./bundles/SerapiCore_1.0.yaml",
                        "enabled": True,
                        "categories": ["ATO", "SEM", "CLU", "INTUITION"]
                    }
                ],
                "allowed_types": ["ATO", "SEM", "CLU", "INTUITION"],
                "realtime": {
                    "enabled": True,
                    "buffer_size": 1024,
                    "chunk_duration": 0.5,
                    "confidence_threshold": 0.7
                }
            },
            "audio": {
                "capture": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "chunk_size": 1024,
                    "format": "int16",
                    "device": None
                },
                "websocket": {
                    "endpoint": "/ws/audio",
                    "buffer_size": 4096,
                    "compression": True
                },
                "libraries": ["sounddevice", "pyaudio"]
            },
            "prosody": {
                "enabled": True,
                "features": ["f0", "rms", "zcr", "flatness", "voicing"],
                "frame_length": 1024,
                "hop_length": 512,
                "window": "hann"
            },
            "events": {
                "websocket": {
                    "endpoint": "/ws/events",
                    "heartbeat_interval": 30,
                    "max_connections": 10
                },
                "types": [
                    "marker_detected",
                    "audio_chunk_processed",
                    "prosody_features",
                    "transcription_result",
                    "llm_interpretation"
                ],
                "buffer": {
                    "size": 100,
                    "persist": False
                }
            },
            "sessions": {
                "storage": "./sessions",
                "auto_cleanup": True,
                "max_duration": 3600,
                "save_audio": False
            },
            "offline": {
                "enforce": True,
                "block_external": True,
                "local_only": True
            },
            "logging": {
                "level": "INFO",
                "file": "./logs/transrapport.log",
                "max_size": "10MB",
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "ui": {
                "path": "./frontend/dist",
                "serve_static": True,
                "enable_dashboard": True,
                "theme": "dark"
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value by key path (e.g., 'server.host')"""
        if not self.config:
            return default
        
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return self.get('server', {})
    
    def get_marker_config(self) -> Dict[str, Any]:
        """Get marker configuration"""
        return self.get('markers', {})
    
    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio configuration"""
        return self.get('audio', {})
    
    def get_events_config(self) -> Dict[str, Any]:
        """Get events configuration"""
        return self.get('events', {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self.get('models.llm', {})
    
    def is_offline_mode(self) -> bool:
        """Check if offline mode is enforced"""
        return self.get('offline.enforce', True)
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()

# Global configuration instance
app_config = AppConfigLoader()