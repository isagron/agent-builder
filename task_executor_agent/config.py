"""Configuration management for the task executor agent."""

import os
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Task Executor Configuration
    task_executor_url: str = Field(
        default="http://localhost:8000",
        env="TASK_EXECUTOR_URL",
        description="Task executor server URL"
    )
    task_executor_timeout: int = Field(
        default=30,
        env="TASK_EXECUTOR_TIMEOUT",
        description="Request timeout in seconds"
    )
    task_executor_retry_attempts: int = Field(
        default=3,
        env="TASK_EXECUTOR_RETRY_ATTEMPTS",
        description="Number of retry attempts"
    )
    task_executor_retry_delay: float = Field(
        default=1.0,
        env="TASK_EXECUTOR_RETRY_DELAY",
        description="Delay between retries in seconds"
    )
    
    # Agent Configuration
    default_context_id: Optional[str] = Field(
        default=None,
        env="DEFAULT_CONTEXT_ID",
        description="Default runtime context ID"
    )
    max_execution_time: int = Field(
        default=300,
        env="MAX_EXECUTION_TIME",
        description="Maximum execution time in seconds"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    enable_logging: bool = Field(
        default=True,
        env="ENABLE_LOGGING",
        description="Enable detailed logging"
    )
    
    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        env="HOST",
        description="Server host"
    )
    port: int = Field(
        default=8001,
        env="PORT",
        description="Server port"
    )
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Debug mode"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
