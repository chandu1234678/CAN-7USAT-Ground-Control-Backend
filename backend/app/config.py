"""
Configuration management using Pydantic Settings
Loads from environment variables and .env file
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    # Serial Port (XBee)
    serial_port: str = Field(default="COM3", description="Serial port for XBee")
    serial_baudrate: int = Field(default=57600, description="Serial baud rate")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/rocket_telemetry",
        description="PostgreSQL connection URL"
    )
    
    # Mock Mode (for testing without hardware)
    mock_mode: bool = Field(default=True, description="Use mock data generator")
    mock_data_rate: int = Field(default=10, description="Mock data rate in Hz")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
