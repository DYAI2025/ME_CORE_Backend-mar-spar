import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import Optional
from .core.exceptions import ConfigurationError

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = Field(default="mongodb://localhost:27017/test", description="MongoDB connection string")
    MONGO_DB_NAME: str = Field(default="marker_engine", description="Database name")
    
    # API configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    
    # Detector configuration
    DETECTOR_PATH: Optional[str] = Field(
        default=None,
        description="Path to detector scripts (defaults to ../resources relative to backend dir)"
    )
    
    # LLM API Keys (optional - will work without them but no interpretation)
    MOONSHOT_API_KEY: Optional[str] = Field(None, description="Moonshot.ai Kimi K2 API Key")
    KIMI_API_KEY: Optional[str] = Field(None, description="Alias for MOONSHOT_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API Key (fallback)")
    
    # NLP Service configuration
    SPARK_NLP_ENABLED: bool = Field(
        default=False, 
        description="Enable Spark NLP service (requires pyspark and spark-nlp)"
    )
    
    # Cache configuration
    CACHE_TYPE: str = Field(
        default="memory",
        description="Cache type: 'memory' or 'redis'"
    )
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL (redis://host:port/db)"
    )
    CACHE_DEFAULT_TTL: int = Field(
        default=3600,
        description="Default cache TTL in seconds"
    )
    
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    
    # Monitoring configuration
    ENABLE_METRICS: bool = Field(
        default=True,
        description="Enable Prometheus metrics collection"
    )
    METRICS_PORT: int = Field(
        default=9090,
        description="Port for Prometheus metrics endpoint"
    )
    
    # Notification configuration
    NOTIFICATION_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="Webhook URL for notifications"
    )
    
    # Performance configuration
    MAX_TEXT_LENGTH: int = Field(
        default=100000,
        description="Maximum text length for analysis"
    )
    REQUEST_TIMEOUT: int = Field(
        default=300,
        description="Request timeout in seconds"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True
    )
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        """Validate that DATABASE_URL is set and not contains placeholder"""
        # Allow deployment without MongoDB for testing
        if v == "mongodb://localhost:27017/test":
            import logging
            logging.warning("Using default test DATABASE_URL - MongoDB features will be limited")
            return v
        
        if "<PASSWORD>" in v or "<DEIN_PASSWORT_HIER_EINFÜGEN>" in v:
            raise ConfigurationError(
                "DATABASE_URL still contains placeholder password! "
                "Please replace <PASSWORD> with your actual MongoDB password in the .env file.",
                config_key="DATABASE_URL"
            )
            
        return v
    
    @validator('DETECTOR_PATH', always=True)
    def validate_detector_path(cls, v):
        """Validate and set detector path with intelligent defaults"""
        if v:
            path = Path(v)
        else:
            # Use a safe default - create resources in parent directory
            backend_dir = Path(__file__).parent
            path = backend_dir.parent / "resources"
            
        # Ensure path exists
        path.mkdir(parents=True, exist_ok=True)
        
        return str(path.absolute())
    
    @validator('KIMI_API_KEY', always=True)
    def set_kimi_api_key(cls, v, values):
        """Use MOONSHOT_API_KEY if KIMI_API_KEY not set"""
        if not v and 'MOONSHOT_API_KEY' in values:
            return values['MOONSHOT_API_KEY']
        return v

# Create settings instance - let exceptions propagate to be handled by the application
settings = Settings()