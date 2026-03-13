"""Structured logging utilities for detail-forge (REQ-EH-008).

Provides:
- get_logger(): Returns a configured standard Logger
- SensitiveDataFilter: Masks API keys, passwords from log records
"""

from __future__ import annotations

import logging
import re

# Patterns to mask in log messages (keys followed by = or : and value)
_SENSITIVE_PATTERNS = [
    re.compile(r"(api[_-]?key\s*[=:]\s*)([^\s,;\"']+)", re.IGNORECASE),
    re.compile(r"(password\s*[=:]\s*)([^\s,;\"']+)", re.IGNORECASE),
    re.compile(r"(secret\s*[=:]\s*)([^\s,;\"']+)", re.IGNORECASE),
    re.compile(r"(token\s*[=:]\s*)([^\s,;\"']+)", re.IGNORECASE),
    re.compile(r"(auth\s*[=:]\s*)([^\s,;\"']+)", re.IGNORECASE),
]

_MASK = "***REDACTED***"


class SensitiveDataFilter(logging.Filter):
    """Removes sensitive data (API keys, passwords) from log records.

    Modifies the log record's message in-place before emission.
    Always returns True so the record is still logged (just masked).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _mask_sensitive(str(record.msg))
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: _mask_sensitive(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, (tuple, list)):
                record.args = tuple(
                    _mask_sensitive(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )
        return True


def _mask_sensitive(text: str) -> str:
    """Replace sensitive values in a text string with the mask."""
    for pattern in _SENSITIVE_PATTERNS:
        text = pattern.sub(lambda m: m.group(1) + _MASK, text)
    return text


def get_logger(name: str) -> logging.Logger:
    """Return a logger with SensitiveDataFilter attached.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A standard :class:`logging.Logger` with sensitive-data filtering.
    """
    logger = logging.getLogger(name)
    if not any(isinstance(f, SensitiveDataFilter) for f in logger.filters):
        logger.addFilter(SensitiveDataFilter())
    return logger
