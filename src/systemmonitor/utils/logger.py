"""Minimal logging system for SystemMonitor.
Provides the symbols imported by the application: LogLevel, SystemLogger,
get_logger, log_info, log_error, log_warning, log_exception, LogCategory.
The implementation writes logs to stdout and optionally to a file in the project
'logs' directory.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from enum import Enum
from typing import Optional

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SystemLogger:
    _instance: Optional['SystemLogger'] = None
    _loggers: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._log_dir = self._get_log_dir()
        self._max_bytes = 5 * 1024 * 1024
        self._backup_count = 3
        self._initialized = True

    @property
    def log_dir(self) -> Path:
        return self._log_dir

    @staticmethod
    def _get_log_dir() -> Path:
        if getattr(sys, "frozen", False):
            log_dir = Path(os.environ.get("TEMP", "")) / "SystemMonitor" / "logs"
        else:
            log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _get_logger(self, name: str) -> logging.Logger:
        if name in self._loggers:
            return self._loggers[name]
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            # File handler
            log_file = self._log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file, maxBytes=self._max_bytes, backupCount=self._backup_count, encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)-8s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            # Console handler
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            logger.addHandler(console)
        self._loggers[name] = logger
        return logger

    def log(self, level: LogLevel, category: str, message: str):
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

def get_logger() -> SystemLogger:
    return SystemLogger()

def log_debug(category: str, message: str):
    get_logger().debug(category, message)

def log_info(category: str, message: str):
    get_logger().info(category, message)

def log_error(category: str, message: str):
    get_logger().error(category, message)

def log_warning(category: str, message: str):
    get_logger().warning(category, message)

def log_exception(category: str, message: str, exc: Exception):
    log_error(category, f"{message}: {exc}")
    import traceback
    log_error(category, f"Traceback: {traceback.format_exc()}")

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
