"""Segment domain model representing a flight leg within an itinerary."""

from dataclasses import dataclass
from typing import Optional

from status_optimizer.domain.flight import Flight


@dataclass(frozen=True)
class Segment:
    """A flight leg with its position in an itinerary (1-indexed)."""
    flight: Flight
    sequence_number: int

    def __post_init__(self):
        if self.sequence_number < 1:
            raise ValueError(f"sequence_number must be >= 1, got {self.sequence_number}")

    def __repr__(self) -> str:
        return f"Segment({self.sequence_number}: {self.flight})"

