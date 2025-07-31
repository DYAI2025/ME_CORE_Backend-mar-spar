"""
Shared configuration module for MarkerEngine services.

This module provides common configuration structures and utilities
that can be reused across different services and components.
"""
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PathConfig(BaseModel):
    """Configuration for various paths used in the system."""
    
    resources_path: Path = Field(description="Path to detector resources")
    data_path: Optional[Path] = Field(None, description="Path to data directory")
    logs_path: Optional[Path] = Field(None, description="Path to logs directory")
    temp_path: Optional[Path] = Field(None, description="Path to temporary files")
    
    class Config:
        arbitrary_types_allowed = True
    
    def ensure_paths_exist(self):
        """Create directories if they don't exist."""
        for field_name, field_value in self:
            if field_value and isinstance(field_value, Path):
                field_value.mkdir(parents=True, exist_ok=True)


class APIConfig(BaseModel):
    """Configuration for API settings."""
    
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    base_path: str = Field(default="/api", description="API base path")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    request_timeout: int = Field(default=300, description="Request timeout in seconds")
    max_request_size: int = Field(default=10_485_760, description="Max request size in bytes (10MB)")


class CacheConfig(BaseModel):
    """Configuration for caching."""
    
    type: str = Field(default="memory", description="Cache type: memory or redis")
    redis_url: Optional[str] = Field(None, description="Redis connection URL")
    default_ttl: int = Field(default=3600, description="Default TTL in seconds")
    max_memory_items: int = Field(default=1000, description="Max items in memory cache")


class MonitoringConfig(BaseModel):
    """Configuration for monitoring and metrics."""
    
    enabled: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Prometheus metrics port")
    log_level: str = Field(default="INFO", description="Logging level")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")


class LLMConfig(BaseModel):
    """Configuration for LLM integrations."""
    
    moonshot_api_key: Optional[str] = Field(None, description="Moonshot API key")
    kimi_api_key: Optional[str] = Field(None, description="Kimi API key") 
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    default_model: str = Field(default="kimi-k2", description="Default LLM model")
    max_tokens: int = Field(default=4096, description="Max tokens for LLM response")
    temperature: float = Field(default=0.7, description="LLM temperature")


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""
    
    name: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    testing: bool = Field(default=False, description="Testing mode")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.name.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.name.lower() == "development"


class SharedConfig(BaseModel):
    """Complete shared configuration."""
    
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    @classmethod
    def from_settings(cls, settings: Any) -> "SharedConfig":
        """Create SharedConfig from settings object."""
        return cls(
            environment=EnvironmentConfig(
                name=getattr(settings, "ENVIRONMENT", "development"),
                debug=getattr(settings, "DEBUG", False),
                testing=getattr(settings, "TESTING", False)
            ),
            paths=PathConfig(
                resources_path=Path(settings.DETECTOR_PATH),
                data_path=Path(getattr(settings, "DATA_PATH", "./data")) if hasattr(settings, "DATA_PATH") else None,
                logs_path=Path(getattr(settings, "LOGS_PATH", "./logs")) if hasattr(settings, "LOGS_PATH") else None,
                temp_path=Path(getattr(settings, "TEMP_PATH", "./tmp")) if hasattr(settings, "TEMP_PATH") else None
            ),
            api=APIConfig(
                host=settings.API_HOST,
                port=settings.API_PORT,
                request_timeout=settings.REQUEST_TIMEOUT,
                cors_origins=getattr(settings, "CORS_ORIGINS", ["*"])
            ),
            cache=CacheConfig(
                type=settings.CACHE_TYPE,
                redis_url=settings.REDIS_URL,
                default_ttl=settings.CACHE_DEFAULT_TTL
            ),
            monitoring=MonitoringConfig(
                enabled=settings.ENABLE_METRICS,
                metrics_port=settings.METRICS_PORT,
                log_level=getattr(settings, "LOG_LEVEL", "INFO")
            ),
            llm=LLMConfig(
                moonshot_api_key=settings.MOONSHOT_API_KEY,
                kimi_api_key=settings.KIMI_API_KEY,
                openai_api_key=settings.OPENAI_API_KEY
            )
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.model_dump(mode="json", exclude_none=True)


# Singleton instance
_shared_config: Optional[SharedConfig] = None


def get_shared_config() -> SharedConfig:
    """Get the shared configuration instance."""
    global _shared_config
    
    if _shared_config is None:
        from backend.config import settings
        _shared_config = SharedConfig.from_settings(settings)
    
    return _shared_config


def init_shared_config(settings: Any) -> SharedConfig:
    """Initialize shared configuration with settings."""
    global _shared_config
    _shared_config = SharedConfig.from_settings(settings)
    return _shared_config