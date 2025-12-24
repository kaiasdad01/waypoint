"""Itinerary domain model representing a complete flight journey."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

from status_optimizer.domain.segment import Segment


@dataclass
class Itinerary:
    """A complete flight itinerary. Segments must be sequential and feasible."""
    segments: List[Segment]
    origin_airport: str = field(init=False)
    destination_airport: str = field(init=False)

    def __post_init__(self):
        if not self.segments:
            raise ValueError("Itinerary must have at least one segment")

        # Validate sequence numbers are sequential starting at 1
        for i, segment in enumerate(self.segments, start=1):
            if segment.sequence_number != i:
                raise ValueError(
                    f"Segments must be sequential starting at 1, "
                    f"found sequence_number {segment.sequence_number} at position {i}"
                )

        # Validate feasibility: each segment must depart after previous segment arrives
        for i in range(1, len(self.segments)):
            prev_segment = self.segments[i - 1]
            curr_segment = self.segments[i]

            # Check that previous segment's destination matches current segment's origin
            if prev_segment.flight.destination != curr_segment.flight.origin:
                raise ValueError(
                    f"Segment {curr_segment.sequence_number} origin ({curr_segment.flight.origin}) "
                    f"does not match previous segment destination ({prev_segment.flight.destination})"
                )

            # Check that current segment departs after previous segment arrives
            if curr_segment.flight.departure_time <= prev_segment.flight.arrival_time:
                raise ValueError(
                    f"Segment {curr_segment.sequence_number} departure time "
                    f"({curr_segment.flight.departure_time}) must be after "
                    f"segment {prev_segment.sequence_number} arrival time "
                    f"({prev_segment.flight.arrival_time})"
                )

        # Set derived fields
        self.origin_airport = self.segments[0].flight.origin
        self.destination_airport = self.segments[-1].flight.destination

    @property
    def leg_count(self) -> int:
        return len(self.segments)

    @property
    def departure_time(self) -> datetime:
        return self.segments[0].flight.departure_time

    @property
    def arrival_time(self) -> datetime:
        return self.segments[-1].flight.arrival_time

    @property
    def total_elapsed_time(self) -> timedelta:
        return self.arrival_time - self.departure_time

    @property
    def total_airtime(self) -> timedelta:
        return sum((segment.flight.duration for segment in self.segments), start=timedelta(0))

    @property
    def total_layover_time(self) -> timedelta:
        """Total layover time between segments (time at connecting airports)."""
        if len(self.segments) <= 1:
            return timedelta(0)
        
        total_layover = timedelta(0)
        for i in range(1, len(self.segments)):
            prev_arrival = self.segments[i - 1].flight.arrival_time
            curr_departure = self.segments[i].flight.departure_time
            layover = curr_departure - prev_arrival
            total_layover += layover
        
        return total_layover

    def get_layover_times(self) -> List[timedelta]:
        """Layover times between each segment."""
        if len(self.segments) <= 1:
            return []
        
        layovers = []
        for i in range(1, len(self.segments)):
            prev_arrival = self.segments[i - 1].flight.arrival_time
            curr_departure = self.segments[i].flight.departure_time
            layover = curr_departure - prev_arrival
            layovers.append(layover)
        
        return layovers

    def __repr__(self) -> str:
        route = " -> ".join(
            f"{seg.flight.origin}" for seg in self.segments
        ) + f" -> {self.destination_airport}"
        return f"Itinerary({self.leg_count} segments: {route})"

    def __hash__(self) -> int:
        return hash(tuple(self.segments))

