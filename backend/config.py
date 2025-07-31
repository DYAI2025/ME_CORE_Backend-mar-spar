import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import Optional
import sys

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = Field(..., description="MongoDB connection string")
    MONGO_DB_NAME: str = Field(default="marker_engine", description="Database name")
    
    # API configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    
    # Detector configuration
    DETECTOR_PATH: str = Field(
        default="/Users/benjaminpoersch/Projekte/XEXPERIMENTE/Gemini_cli/gemini-cli/claude-flow/resources/",
        description="Path to detector scripts"
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
        if not v:
            print("ERROR: DATABASE_URL environment variable is not set!")
            print("Please create a .env file with your MongoDB connection string.")
            print("See .env.example for the required format.")
            sys.exit(1)
        
        if "<PASSWORD>" in v or "<DEIN_PASSWORT_HIER_EINFÜGEN>" in v:
            print("ERROR: DATABASE_URL still contains placeholder password!")
            print("Please replace <PASSWORD> with your actual MongoDB password in the .env file.")
            sys.exit(1)
            
        return v
    
    @validator('KIMI_API_KEY', always=True)
    def set_kimi_api_key(cls, v, values):
        """Use MOONSHOT_API_KEY if KIMI_API_KEY not set"""
        if not v and 'MOONSHOT_API_KEY' in values:
            return values['MOONSHOT_API_KEY']
        return v

# Try to load settings with error handling
try:
    settings = Settings()
except Exception as e:
    print(f"ERROR: Failed to load configuration: {e}")
    print("Please ensure .env file exists and contains valid configuration.")
    sys.exit(1)