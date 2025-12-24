"""Unit tests for concrete constraint implementations."""

import pytest
from datetime import datetime, timedelta

from status_optimizer.constraints import (
    LegCountConstraint,
    ReturnToOriginConstraint,
    TimeWindowConstraint,
    MinLayoverConstraint,
    MaxElapsedConstraint,
)
from status_optimizer.domain.flight import Flight
from status_optimizer.domain.segment import Segment
from status_optimizer.domain.itinerary import Itinerary


class TestLegCountConstraint:
    """Test cases for LegCountConstraint."""
    
    def test_exact_leg_count(self):
        """Test exact leg count constraint."""
        constraint = LegCountConstraint(exact=4)
        
        # Create 4-segment itinerary with proper layovers
        flight1 = Flight(
            flight_number="UA 100",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 0, 0),
            arrival_time=datetime(2025, 1, 15, 16, 0, 0),
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 101",
            origin="HNL",
            destination="LAX",
            departure_time=datetime(2025, 1, 15, 17, 0, 0),  # After flight1 arrives
            arrival_time=datetime(2025, 1, 15, 22, 0, 0),
            aircraft_type="787"
        )
        
        flight3 = Flight(
            flight_number="UA 102",
            origin="LAX",
            destination="SFO",
            departure_time=datetime(2025, 1, 15, 23, 0, 0),  # After flight2 arrives
            arrival_time=datetime(2025, 1, 16, 0, 30, 0),
            aircraft_type="737"
        )
        
        flight4 = Flight(
            flight_number="UA 103",
            origin="SFO",
            destination="DEN",
            departure_time=datetime(2025, 1, 16, 1, 30, 0),  # After flight3 arrives
            arrival_time=datetime(2025, 1, 16, 5, 0, 0),
            aircraft_type="777"
        )
        
        segments = [
            Segment(flight=flight1, sequence_number=1),
            Segment(flight=flight2, sequence_number=2),
            Segment(flight=flight3, sequence_number=3),
            Segment(flight=flight4, sequence_number=4),
        ]
        itinerary = Itinerary(segments)
        
        assert constraint.is_satisfied(itinerary) is True
        assert constraint.violation(itinerary) is None
    
    def test_exact_leg_count_violation(self):
        """Test exact leg count constraint violation."""
        constraint = LegCountConstraint(exact=4)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is False
        assert "required exactly 4" in constraint.violation(itinerary)
    
    def test_minimum_leg_count(self):
        """Test minimum leg count constraint."""
        constraint = LegCountConstraint(minimum=3)
        
        # Create 4-segment itinerary with proper layovers
        flight1 = Flight(
            flight_number="UA 100",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 0, 0),
            arrival_time=datetime(2025, 1, 15, 16, 0, 0),
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 101",
            origin="HNL",
            destination="LAX",
            departure_time=datetime(2025, 1, 15, 17, 0, 0),  # After flight1 arrives
            arrival_time=datetime(2025, 1, 15, 22, 0, 0),
            aircraft_type="787"
        )
        
        flight3 = Flight(
            flight_number="UA 102",
            origin="LAX",
            destination="SFO",
            departure_time=datetime(2025, 1, 15, 23, 0, 0),  # After flight2 arrives
            arrival_time=datetime(2025, 1, 16, 0, 30, 0),
            aircraft_type="737"
        )
        
        flight4 = Flight(
            flight_number="UA 103",
            origin="SFO",
            destination="DEN",
            departure_time=datetime(2025, 1, 16, 1, 30, 0),  # After flight3 arrives
            arrival_time=datetime(2025, 1, 16, 5, 0, 0),
            aircraft_type="777"
        )
        
        segments = [
            Segment(flight=flight1, sequence_number=1),
            Segment(flight=flight2, sequence_number=2),
            Segment(flight=flight3, sequence_number=3),
            Segment(flight=flight4, sequence_number=4),
        ]
        itinerary = Itinerary(segments)
        
        assert constraint.is_satisfied(itinerary) is True
    
    def test_maximum_leg_count(self):
        """Test maximum leg count constraint."""
        constraint = LegCountConstraint(maximum=2)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is True
    
    def test_partial_ok_pruning(self):
        """Test partial_ok for early pruning."""
        constraint = LegCountConstraint(maximum=3)
        
        state1 = {'legs_used': 2}
        assert constraint.partial_ok(state1) is True
        
        state2 = {'legs_used': 4}
        assert constraint.partial_ok(state2) is False


class TestReturnToOriginConstraint:
    """Test cases for ReturnToOriginConstraint."""
    
    def test_return_to_origin_satisfied(self):
        """Test return-to-origin constraint when satisfied."""
        constraint = ReturnToOriginConstraint(required=True)
        
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 500",
            origin="HNL",
            destination="DEN",
            departure_time=datetime(2025, 1, 15, 18, 0, 0),
            arrival_time=datetime(2025, 1, 16, 0, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        itinerary = Itinerary([segment1, segment2])
        
        assert constraint.is_satisfied(itinerary) is True
        assert constraint.violation(itinerary) is None
    
    def test_return_to_origin_violation(self):
        """Test return-to-origin constraint violation."""
        constraint = ReturnToOriginConstraint(required=True)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is False
        assert "does not return to origin" in constraint.violation(itinerary)
    
    def test_return_to_origin_disabled(self):
        """Test return-to-origin constraint when disabled."""
        constraint = ReturnToOriginConstraint(required=False)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is True


class TestTimeWindowConstraint:
    """Test cases for TimeWindowConstraint."""
    
    def test_time_window_satisfied(self):
        """Test time window constraint when satisfied."""
        start_time = datetime(2025, 1, 15, 10, 0, 0)
        end_time = datetime(2025, 1, 15, 20, 0, 0)
        constraint = TimeWindowConstraint(start_time=start_time, end_time=end_time)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is True
        assert constraint.violation(itinerary) is None
    
    def test_time_window_departure_too_early(self):
        """Test time window constraint violation - departure too early."""
        start_time = datetime(2025, 1, 15, 10, 0, 0)
        end_time = datetime(2025, 1, 15, 20, 0, 0)
        constraint = TimeWindowConstraint(start_time=start_time, end_time=end_time)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 9, 0, 0),  # Before start
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is False
        assert "before window start" in constraint.violation(itinerary)
    
    def test_time_window_arrival_too_late(self):
        """Test time window constraint violation - arrival too late."""
        start_time = datetime(2025, 1, 15, 10, 0, 0)
        end_time = datetime(2025, 1, 15, 20, 0, 0)
        constraint = TimeWindowConstraint(start_time=start_time, end_time=end_time)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 21, 0, 0),  # After end
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is False
        assert "after window end" in constraint.violation(itinerary)
    
    def test_time_window_midnight_crossing(self):
        """Test time window constraint with midnight crossing."""
        start_time = datetime(2025, 1, 15, 22, 0, 0)
        end_time = datetime(2025, 1, 16, 6, 0, 0)  # Next day
        constraint = TimeWindowConstraint(start_time=start_time, end_time=end_time)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 23, 59, 0),
            arrival_time=datetime(2025, 1, 16, 5, 30, 0),  # Next day
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is True


class TestMinLayoverConstraint:
    """Test cases for MinLayoverConstraint."""
    
    def test_min_layover_satisfied(self):
        """Test minimum layover constraint when satisfied."""
        constraint = MinLayoverConstraint(min_minutes=60)
        
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 500",
            origin="HNL",
            destination="LAX",
            departure_time=datetime(2025, 1, 15, 18, 0, 0),  # 1h 27m layover
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        itinerary = Itinerary([segment1, segment2])
        
        assert constraint.is_satisfied(itinerary) is True
        assert constraint.violation(itinerary) is None
    
    def test_min_layover_violation(self):
        """Test minimum layover constraint violation."""
        constraint = MinLayoverConstraint(min_minutes=90)
        
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 500",
            origin="HNL",
            destination="LAX",
            departure_time=datetime(2025, 1, 15, 17, 30, 0),  # Only 57m layover
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        itinerary = Itinerary([segment1, segment2])
        
        assert constraint.is_satisfied(itinerary) is False
        assert "minimum 90 minutes" in constraint.violation(itinerary)
    
    def test_min_layover_single_segment(self):
        """Test minimum layover constraint with single segment (no layovers)."""
        constraint = MinLayoverConstraint(min_minutes=60)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is True


class TestMaxElapsedConstraint:
    """Test cases for MaxElapsedConstraint."""
    
    def test_max_elapsed_satisfied(self):
        """Test maximum elapsed time constraint when satisfied."""
        constraint = MaxElapsedConstraint(max_hours=24.0)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),  # 4h 28m
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is True
        assert constraint.violation(itinerary) is None
    
    def test_max_elapsed_violation(self):
        """Test maximum elapsed time constraint violation."""
        constraint = MaxElapsedConstraint(max_hours=2.0)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),  # 4h 28m
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is False
        assert "maximum 2.0 hours" in constraint.violation(itinerary)
    
    def test_max_elapsed_partial_ok(self):
        """Test maximum elapsed time partial_ok for pruning."""
        constraint = MaxElapsedConstraint(max_hours=5.0)
        
        state1 = {'elapsed': timedelta(hours=3)}
        assert constraint.partial_ok(state1) is True
        
        state2 = {'elapsed': timedelta(hours=6)}
        assert constraint.partial_ok(state2) is False

