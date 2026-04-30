"""
Configuration management using Pydantic Settings
Loads from environment variables and .env file
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    serial_port: str = "COM3"
    serial_baudrate: int = 57600
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/rocket_telemetry"
    mock_mode: bool = True
    mock_data_rate: int = 10
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
