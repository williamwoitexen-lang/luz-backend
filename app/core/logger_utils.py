"""
Centralized logging utilities to standardize log formats across the application.
Removes emojis from logs for better searchability while keeping them in print() for UX.
"""
import logging
from typing import Optional

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with standardized formatting."""
    return logging.getLogger(name)


def log_info(logger: logging.Logger, context: str, message: str):
    """Log info with standardized format: [context] message"""
    logger.info(f"[{context}] {message}")


def log_error(logger: logging.Logger, context: str, message: str, exc_info: bool = False):
    """Log error with standardized format: [context] message"""
    logger.error(f"[{context}] {message}", exc_info=exc_info)


def log_warning(logger: logging.Logger, context: str, message: str):
    """Log warning with standardized format: [context] message"""
    logger.warning(f"[{context}] {message}")


def log_debug(logger: logging.Logger, context: str, message: str):
    """Log debug with standardized format: [context] message"""
    logger.debug(f"[{context}] {message}")


def print_success(message: str):
    """Print success message with emoji for terminal UX."""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message with emoji for terminal UX."""
    print(f"❌ {message}")


def print_warning(message: str):
    """Print warning message with emoji for terminal UX."""
    print(f"⚠️  {message}")


def print_info(message: str):
    """Print info message with emoji for terminal UX."""
    print(f"ℹ️  {message}")
