"""Application configuration with sensible defaults."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SearchConfig:
    """beam search algorithm configuration."""
    beam_width: int = 200
    max_candidates: int = 10000


@dataclass(frozen=True)
class CLIDefaults:
    """Default values for CLI arguments."""
    min_layover_minutes: int = 45
    max_elapsed_hours: float = 48.0
    max_results: int = 10
    excel_path: str = "data/united-routes.xlsx"


@dataclass(frozen=True)
class Config:
    """Application-wide configuration."""
    search: SearchConfig = SearchConfig()
    cli: CLIDefaults = CLIDefaults()


# Global config instance
config = Config()
