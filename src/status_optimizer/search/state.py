"""Search state representation for itinerary beam search."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from status_optimizer.domain.flight import Flight
from status_optimizer.domain.segment import Segment


@dataclass
class SearchState:
    """Represents a partial path state during beam search.

    A search state captures the current position in the search space:
    - Where we are (current airport)
    - When we are (current time)
    - How we got here (segments so far)
    - Progress metrics (legs used, elapsed time)

    Attributes:
        current_airport: Current airport IATA code
        current_time: Current time (arrival time of last flight, or search start time)
        segments: List of segments in this partial path
        origin_airport: Original starting airport
        legs_used: Number of segments used so far
        elapsed_time: Total elapsed time from start to current_time
        score: Heuristic score for beam search ranking (lower is better)
    """

    current_airport: str
    current_time: datetime
    segments: List[Segment]
    origin_airport: str
    legs_used: int
    elapsed_time: timedelta
    score: float = 0.0

    @classmethod
    def initial(cls, origin: str, start_time: datetime) -> "SearchState":
        """Create initial search state.

        Args:
            origin: Origin airport IATA code
            start_time: Search start time (UTC)

        Returns:
            Initial SearchState with no segments
        """
        return cls(
            current_airport=origin,
            current_time=start_time,
            segments=[],
            origin_airport=origin,
            legs_used=0,
            elapsed_time=timedelta(0),
            score=0.0,
        )

    def expand(self, flight: Flight) -> "SearchState":
        """Expand this state by adding a flight.

        Creates a new state by appending a flight to the current path.

        Args:
            flight: Flight to add to the path

        Returns:
            New SearchState with the flight added

        Raises:
            ValueError: If flight doesn't depart from current airport or
                       departs before current time
        """
        if flight.origin != self.current_airport:
            raise ValueError(
                f"Flight origin {flight.origin} doesn't match "
                f"current airport {self.current_airport}"
            )

        if flight.departure_time < self.current_time:
            raise ValueError(
                f"Flight departs at {flight.departure_time} which is before "
                f"current time {self.current_time}"
            )

        # Create new segment
        new_segment = Segment(flight=flight, sequence_number=self.legs_used + 1)

        # Calculate new elapsed time
        new_elapsed = flight.arrival_time - (
            self.segments[0].flight.departure_time if self.segments
            else flight.departure_time
        )

        return SearchState(
            current_airport=flight.destination,
            current_time=flight.arrival_time,
            segments=self.segments + [new_segment],
            origin_airport=self.origin_airport,
            legs_used=self.legs_used + 1,
            elapsed_time=new_elapsed,
            score=0.0,  # Will be set by scoring function
        )

    def is_complete(self, target_legs: int) -> bool:
        """Check if this state represents a complete itinerary.

        A state is complete if it has used the target number of legs
        and returned to the origin airport (for return-to-origin searches).

        Args:
            target_legs: Target number of legs

        Returns:
            True if state is complete
        """
        return (
            self.legs_used == target_legs and
            self.current_airport == self.origin_airport
        )

    def __lt__(self, other: "SearchState") -> bool:
        """Less-than comparison for priority queue ordering.

        States with lower scores are considered "less than" (better).
        """
        return self.score < other.score

    def __repr__(self) -> str:
        """String representation of SearchState."""
        route = " -> ".join(seg.flight.origin for seg in self.segments)
        if route:
            route += f" -> {self.current_airport}"
        else:
            route = self.current_airport
        return (
            f"SearchState({self.legs_used} legs, {route}, "
            f"elapsed={self.elapsed_time}, score={self.score:.2f})"
        )
