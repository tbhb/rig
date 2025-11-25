"""Exception hierarchy for configuration errors.

This module defines the exception classes used throughout the configuration
system. All exceptions inherit from ConfigError, enabling catch-all handling
when needed.

Exception classes use frozen dataclasses with slots for immutability and
memory efficiency, while still providing structured error data for
programmatic handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from pathlib import Path


class ConfigError(Exception):
    """Base exception for all configuration errors.

    All config-related exceptions inherit from this class, enabling
    catch-all handling when needed.
    """


@dataclass(slots=True, frozen=True)
class ConfigParseError(ConfigError):
    """Raised when a config file cannot be parsed as valid TOML.

    Attributes:
        path: Absolute path to the config file.
        line: Line number where the error occurred (1-indexed), or None.
        column: Column number where the error occurred (1-indexed), or None.
        detail: Specific error message from the TOML parser.
    """

    path: Path
    line: int | None
    column: int | None
    detail: str

    @override
    def __str__(self) -> str:
        """Format the error message with location information."""
        location = ""
        if self.line is not None:
            location = f":{self.line}"
            if self.column is not None:
                location += f":{self.column}"
        return f"Failed to parse {self.path}{location}: {self.detail}"


@dataclass(slots=True, frozen=True)
class ConfigValidationError(ConfigError):
    """Raised when a config file has invalid structure or values.

    Attributes:
        path: Absolute path to the config file.
        key: Dot-notation key path where the error occurred.
        detail: Description of the validation failure.
    """

    path: Path
    key: str
    detail: str

    @override
    def __str__(self) -> str:
        """Format the error message with key context."""
        return f"Invalid config at {self.path}: [{self.key}] {self.detail}"


@dataclass(slots=True, frozen=True)
class ConfigFileAccessError(ConfigError):
    """Raised when a config file cannot be accessed.

    Attributes:
        path: Absolute path to the config file.
        detail: Description of the access error.
    """

    path: Path
    detail: str

    @override
    def __str__(self) -> str:
        """Format the error message with path context."""
        return f"Cannot access {self.path}: {self.detail}"
