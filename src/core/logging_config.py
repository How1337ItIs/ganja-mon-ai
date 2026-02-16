"""
Logging Configuration
=====================

structlog setup for the unified agent.
JSON in production, colored console in development.

Usage:
    from src.core.logging_config import setup_logging
    setup_logging()  # Call once at startup

    import structlog
    log = structlog.get_logger()
    log.info("sensor_read", temp=77.2, humidity=55.0)
"""

import logging
import os
import sys

import structlog


def setup_logging(level: str = "INFO", json_output: bool = False) -> None:
    """
    Configure structlog + stdlib logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_output: True for JSON lines (production), False for colored console
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Auto-detect: JSON if running as systemd service (no TTY)
    if json_output is False and not sys.stderr.isatty():
        json_output = True

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging (for uvicorn, sqlalchemy, etc.)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=log_level,
    )

    # Quiet noisy libraries
    for name in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str = "") -> structlog.BoundLogger:
    """Get a named logger."""
    return structlog.get_logger(name)
