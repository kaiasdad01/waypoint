"""Flight domain model representing a single flight leg."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass(frozen=True)
class Flight:
    """A single flight leg with origin, destination, and timing. All times are UTC."""
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: str

    def __post_init__(self):
        if self.departure_time >= self.arrival_time:
            raise ValueError(
                f"Departure time {self.departure_time} must be before arrival time {self.arrival_time}"
            )
        # Normalize airport codes to uppercase (frozen dataclass uses object.__setattr__)
        object.__setattr__(self, 'origin', self.origin.upper())
        object.__setattr__(self, 'destination', self.destination.upper())
    
    @property
    def duration(self) -> timedelta:
        """Flight duration (arrival - departure)."""
        return self.arrival_time - self.departure_time

    def __repr__(self) -> str:
        return (
            f"Flight({self.flight_number}, {self.origin} -> {self.destination}, "
            f"dep: {self.departure_time}, arr: {self.arrival_time})"
        )

