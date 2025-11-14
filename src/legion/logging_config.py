"""
Centralized logging configuration for Legion framework.

This module provides a standardized logging setup for all Legion components,
including console and file logging with rotation, structured formatting,
and different log levels for different components.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class LegionLogger:
    """
    Centralized logger for Legion framework.
    
    Provides console and file logging with automatic rotation,
    structured formatting, and component-specific log levels.
    """
    
    def __init__(
        self,
        name: str = "Legion",
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        log_to_file: bool = True,
        log_to_console: bool = True,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ):
        """
        Initialize logger configuration.
        
        Args:
            name: Logger name (default: "Legion")
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (default: ./logs)
            log_to_file: Enable file logging
            log_to_console: Enable console logging
            max_bytes: Maximum log file size before rotation (default: 10MB)
            backup_count: Number of backup files to keep (default: 5)
        """
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Setup logger with handlers and formatters.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Remove existing handlers
        logger.handlers = []
        
        # Console handler
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.log_to_file:
            # Create log directory if it doesn't exist
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate log filename with timestamp
            log_filename = self.log_dir / f"{self.name.lower()}_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_filename,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.
        
        Returns:
            Logger instance
        """
        return self.logger


def setup_logging(
    component: str = "Legion",
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    Quick setup function for component-specific logging.
    
    Args:
        component: Component name (e.g., "Core", "Agent", "Queue")
        log_level: Log level from environment or default to INFO
        log_dir: Log directory from environment or default to ./logs
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logging("TaskQueue", "DEBUG")
        >>> logger.info("Queue initialized")
    """
    # Get configuration from environment variables if not provided
    if log_level is None:
        log_level = os.getenv("LEGION_LOG_LEVEL", "INFO")
    
    if log_dir is None:
        log_dir = os.getenv("LEGION_LOG_DIR", "logs")
    
    # Create logger
    legion_logger = LegionLogger(
        name=f"Legion.{component}",
        log_level=log_level,
        log_dir=log_dir
    )
    
    return legion_logger.get_logger()


# Convenience loggers for common components
def get_core_logger() -> logging.Logger:
    """Get logger for LegionCore component."""
    return setup_logging("Core")


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get logger for specific agent."""
    return setup_logging(f"Agent.{agent_name}")


def get_queue_logger() -> logging.Logger:
    """Get logger for TaskQueue component."""
    return setup_logging("Queue")


def get_database_logger() -> logging.Logger:
    """Get logger for database operations."""
    return setup_logging("Database")


# Example usage
if __name__ == "__main__":
    # Setup logging for different components
    core_logger = get_core_logger()
    agent_logger = get_agent_logger("TestAgent")
    queue_logger = get_queue_logger()
    
    # Log some test messages
    core_logger.info("Legion Core initialized")
    agent_logger.debug("Agent created with ID: test-123")
    queue_logger.warning("Queue is running low on tasks")
    core_logger.error("Failed to connect to Supabase")
    
    print("\nLogs written to ./logs directory")
