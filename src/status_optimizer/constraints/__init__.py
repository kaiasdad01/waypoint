"""Consolidated constraint system for itinerary validation."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from status_optimizer.domain.itinerary import Itinerary


class Constraint(ABC):
    """Base class for itinerary constraints."""

    @abstractmethod
    def is_satisfied(self, itinerary: Itinerary) -> bool:
        """Check if an itinerary satisfies this constraint."""
        pass

    @abstractmethod
    def violation(self, itinerary: Itinerary) -> Optional[str]:
        """Get violation reason if constraint is not satisfied."""
        pass

    def partial_ok(self, state: Dict[str, Any]) -> bool:
        """Check if a partial search state can still satisfy this constraint."""
        return True


class LegCountConstraint(Constraint):
    """Constraint enforcing exact, minimum, or maximum leg count."""

    def __init__(
        self,
        exact: Optional[int] = None,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
    ):
        if exact is None and minimum is None and maximum is None:
            raise ValueError("At least one of exact, minimum, or maximum must be specified")

        if exact is not None and exact < 1:
            raise ValueError(f"exact must be >= 1, got {exact}")
        if minimum is not None and minimum < 1:
            raise ValueError(f"minimum must be >= 1, got {minimum}")
        if maximum is not None and maximum < 1:
            raise ValueError(f"maximum must be >= 1, got {maximum}")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError(f"minimum ({minimum}) cannot exceed maximum ({maximum})")
        if exact is not None:
            if minimum is not None and exact < minimum:
                raise ValueError(f"exact ({exact}) cannot be less than minimum ({minimum})")
            if maximum is not None and exact > maximum:
                raise ValueError(f"exact ({exact}) cannot exceed maximum ({maximum})")

        self.exact = exact
        self.minimum = minimum
        self.maximum = maximum

    def is_satisfied(self, itinerary: Itinerary) -> bool:
        leg_count = itinerary.leg_count

        if self.exact is not None and leg_count != self.exact:
            return False
        if self.minimum is not None and leg_count < self.minimum:
            return False
        if self.maximum is not None and leg_count > self.maximum:
            return False

        return True

    def violation(self, itinerary: Itinerary) -> Optional[str]:
        leg_count = itinerary.leg_count

        if self.exact is not None and leg_count != self.exact:
            return f"Leg count is {leg_count}, required exactly {self.exact}"
        if self.minimum is not None and leg_count < self.minimum:
            return f"Leg count is {leg_count}, required at least {self.minimum}"
        if self.maximum is not None and leg_count > self.maximum:
            return f"Leg count is {leg_count}, required at most {self.maximum}"

        return None

    def partial_ok(self, state: dict) -> bool:
        legs_used = state.get('legs_used', 0)

        if self.maximum is not None and legs_used > self.maximum:
            return False
        if self.exact is not None and legs_used > self.exact:
            return False

        return True


class ReturnToOriginConstraint(Constraint):
    """Constraint requiring itinerary to return to origin airport."""

    def __init__(self, required: bool = True):
        self.required = required

    def is_satisfied(self, itinerary: Itinerary) -> bool:
        if not self.required:
            return True

        return itinerary.origin_airport == itinerary.destination_airport

    def violation(self, itinerary: Itinerary) -> Optional[str]:
        if not self.required:
            return None

        if itinerary.origin_airport != itinerary.destination_airport:
            return (
                f"Itinerary does not return to origin: "
                f"starts at {itinerary.origin_airport}, ends at {itinerary.destination_airport}"
            )

        return None

    def partial_ok(self, state: dict) -> bool:
        if not self.required:
            return True

        current_airport = state.get('airport')
        origin = state.get('origin')
        legs_remaining = state.get('legs_remaining', 0)

        if current_airport == origin and legs_remaining == 0:
            return True
        if current_airport != origin and legs_remaining == 0:
            return False

        return True


class MinLayoverConstraint(Constraint):
    """Constraint requiring all layovers to be at least a minimum duration."""

    def __init__(self, min_minutes: int):
        if min_minutes < 0:
            raise ValueError(f"min_minutes must be >= 0, got {min_minutes}")

        self.min_minutes = min_minutes
        self.min_timedelta = timedelta(minutes=min_minutes)

    def is_satisfied(self, itinerary: Itinerary) -> bool:
        if itinerary.leg_count <= 1:
            return True

        layover_times = itinerary.get_layover_times()
        return all(layover >= self.min_timedelta for layover in layover_times)

    def violation(self, itinerary: Itinerary) -> Optional[str]:
        if itinerary.leg_count <= 1:
            return None

        layover_times = itinerary.get_layover_times()
        violations = []

        for i, layover in enumerate(layover_times, start=1):
            if layover < self.min_timedelta:
                layover_minutes = int(layover.total_seconds() / 60)
                violations.append(
                    f"Layover {i} is {layover_minutes} minutes "
                    f"(minimum {self.min_minutes} minutes)"
                )

        if violations:
            return "; ".join(violations)

        return None


class MaxElapsedConstraint(Constraint):
    """Constraint requiring total elapsed time to be at most a maximum duration."""

    def __init__(self, max_hours: float):
        if max_hours <= 0:
            raise ValueError(f"max_hours must be > 0, got {max_hours}")

        self.max_hours = max_hours
        self.max_timedelta = timedelta(hours=max_hours)

    def is_satisfied(self, itinerary: Itinerary) -> bool:
        return itinerary.total_elapsed_time <= self.max_timedelta

    def violation(self, itinerary: Itinerary) -> Optional[str]:
        elapsed = itinerary.total_elapsed_time
        if elapsed > self.max_timedelta:
            elapsed_hours = elapsed.total_seconds() / 3600
            return (
                f"Total elapsed time is {elapsed_hours:.1f} hours "
                f"(maximum {self.max_hours} hours)"
            )

        return None

    def partial_ok(self, state: dict) -> bool:
        elapsed = state.get('elapsed')

        if elapsed is None:
            return True

        if elapsed > self.max_timedelta:
            return False

        return True


class TimeWindowConstraint(Constraint):
    """Constraint requiring itinerary to fit within a time window."""

    def __init__(self, start_time: datetime, end_time: datetime):
        if start_time >= end_time:
            raise ValueError(
                f"start_time ({start_time}) must be before end_time ({end_time})"
            )

        self.start_time = start_time
        self.end_time = end_time

    def is_satisfied(self, itinerary: Itinerary) -> bool:
        departure = itinerary.departure_time
        arrival = itinerary.arrival_time

        if departure < self.start_time:
            return False
        if arrival > self.end_time:
            return False

        return True

    def violation(self, itinerary: Itinerary) -> Optional[str]:
        departure = itinerary.departure_time
        arrival = itinerary.arrival_time

        if departure < self.start_time:
            return (
                f"Departure time {departure} is before window start {self.start_time}"
            )
        if arrival > self.end_time:
            return (
                f"Arrival time {arrival} is after window end {self.end_time}"
            )

        return None

    def partial_ok(self, state: dict) -> bool:
        current_time = state.get('time')
        elapsed = state.get('elapsed')

        if current_time is None:
            return True

        if current_time < self.start_time:
            return True
        if current_time > self.end_time:
            return False

        if elapsed is not None:
            estimated_arrival = current_time + elapsed
            if estimated_arrival > self.end_time:
                return False

        return True


__all__ = [
    "Constraint",
    "LegCountConstraint",
    "ReturnToOriginConstraint",
    "MinLayoverConstraint",
    "MaxElapsedConstraint",
    "TimeWindowConstraint",
]
