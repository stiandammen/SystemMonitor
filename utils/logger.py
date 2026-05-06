"""
Professional Logging System for SystemMonitor
Provides centralized logging with rotating files, timestamps, and proper categorization
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Optional
import threading


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SystemLogger:
    """Centralized professional logging system"""

    _instance: Optional['SystemLogger'] = None
    _lock = threading.Lock()

    def __init__(self):
        self._loggers = {}
        self._log_dir = self._get_log_dir()
        self._max_bytes = 5 * 1024 * 1024  # 5MB per file
        self._backup_count = 3  # Keep 3 backup files
        self._initialized = False

    @staticmethod
    def _get_log_dir() -> Path:
        """Get log directory based on environment"""
        if getattr(sys, 'frozen', False):
            log_dir = Path(os.environ.get('TEMP', '')) / 'SystemMonitor' / 'logs'
        else:
            # Development mode - use project logs folder
            log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    @classmethod
    def get_instance(cls) -> 'SystemLogger':
        """Get singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _get_logger(self, name: str) -> logging.Logger:
        """Get or create logger by name"""
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Avoid adding multiple handlers
        if not logger.handlers:
            # File handler with rotation
            log_file = self._log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self._max_bytes,
                backupCount=self._backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)

            # Formatter with timestamp
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)-8s] [%(threadName)-10s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # Console handler for development
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        self._loggers[name] = logger
        return logger

    def log(self, level: LogLevel, category: str, message: str):
        """Log a message with category and level"""
        logger = self._get_logger(category)
        getattr(logger, level.value.lower())(message)

    def debug(self, category: str, message: str):
        self.log(LogLevel.DEBUG, category, message)

    def info(self, category: str, message: str):
        self.log(LogLevel.INFO, category, message)

    def warning(self, category: str, message: str):
        self.log(LogLevel.WARNING, category, message)

    def error(self, category: str, message: str):
        self.log(LogLevel.ERROR, category, message)

    def critical(self, category: str, message: str):
        self.log(LogLevel.CRITICAL, category, message)


# Convenience functions
def get_logger() -> SystemLogger:
    return SystemLogger.get_instance()


def log_debug(category: str, message: str):
    get_logger().debug(category, message)


def log_info(category: str, message: str):
    get_logger().info(category, message)


def log_warning(category: str, message: str):
    get_logger().warning(category, message)


def log_error(category: str, message: str):
    get_logger().error(category, message)


def log_critical(category: str, message: str):
    get_logger().critical(category, message)


def log_exception(category: str, message: str, exc: Exception):
    """Log exception with full traceback"""
    import traceback
    log_error(category, f"{message}: {exc}")
    log_error(category, f"Traceback: {traceback.format_exc()}")


# Log categories
class LogCategory:
    APP = "App"
    COLLECTOR = "Collector"
    CPU = "CPU"
    MEMORY = "Memory"
    GPU = "GPU"
    DISK = "Disk"
    NETWORK = "Network"
    UI = "UI"
    WINDOW = "Window"
    THEMES = "Themes"
    SCALING = "Scaling"
    HARDWARE = "Hardware"
    SERVICES = "Services"