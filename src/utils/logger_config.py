"""
Logger Configuration Module

Provides centralized logging configuration with:
- Console output (INFO level, colored)
- File output (DEBUG level, rotated daily)
- Separate error file (ERROR level)
- Automatic log rotation and compression
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    log_dir: str = "logs",
    app_name: str = "crawl",
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    rotation: str = "00:00",
    retention: str = "30 days",
    compression: str = "zip"
):
    """
    Configure loguru logger for the application

    Args:
        log_dir: Directory to store log files (default: "logs")
        app_name: Application name for log file prefix (default: "crawl")
        console_level: Logging level for console output (default: "INFO")
        file_level: Logging level for file output (default: "DEBUG")
        rotation: When to rotate log files (default: "00:00" = midnight)
        retention: How long to keep old logs (default: "30 days")
        compression: Compression format for old logs (default: "zip")

    Returns:
        Configured logger instance
    """

    # Create logs directory if not exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Remove default logger
    logger.remove()

    # 1. Console Handler - Colored, INFO level
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=console_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # 2. General Log File - DEBUG level, rotated daily
    logger.add(
        log_path / f"{app_name}_{{time:YYYY-MM-DD}}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level=file_level,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )

    # 3. Error Log File - ERROR level only, separate file
    logger.add(
        log_path / f"{app_name}_errors_{{time:YYYY-MM-DD}}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )

    logger.info(f"📝 Logger configured:")
    logger.info(f"   📺 Console: {console_level} level (colored)")
    logger.info(f"   📄 Files: {log_path}/{app_name}_YYYY-MM-DD.log ({file_level} level)")
    logger.info(f"   ❌ Errors: {log_path}/{app_name}_errors_YYYY-MM-DD.log (ERROR level)")
    logger.info(f"   🔄 Rotation: {rotation}, Retention: {retention}, Compression: {compression}")

    return logger


def get_logger():
    """
    Get the configured logger instance

    Returns:
        Logger instance
    """
    return logger
