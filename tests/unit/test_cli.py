"""Unit tests for CLI components."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from status_optimizer.cli.output import (
    format_datetime,
    format_itinerary,
    format_no_solutions,
    format_results,
    format_segment,
    format_time_delta,
)
from status_optimizer.cli.main import (
    build_constraints,
    parse_date_arg,
    validate_airport_code,
)
from status_optimizer.domain.flight import Flight
from status_optimizer.domain.segment import Segment
from status_optimizer.domain.itinerary import Itinerary
from status_optimizer.search.search import ItinerarySearchResult


class TestTimeFormatting:
    """Test time formatting functions."""
    
    def test_format_time_delta_hours_and_minutes(self):
        """Test formatting timedelta with hours and minutes."""
        td = timedelta(hours=2, minutes=30)
        assert format_time_delta(td) == "2h 30m"
    
    def test_format_time_delta_hours_only(self):
        """Test formatting timedelta with only hours."""
        td = timedelta(hours=3)
        assert format_time_delta(td) == "3h"
    
    def test_format_time_delta_minutes_only(self):
        """Test formatting timedelta with only minutes."""
        td = timedelta(minutes=45)
        assert format_time_delta(td) == "45m"
    
    def test_format_time_delta_zero(self):
        """Test formatting zero timedelta."""
        td = timedelta(0)
        assert format_time_delta(td) == "0m"
    
    def test_format_datetime(self):
        """Test datetime formatting."""
        dt = datetime(2025, 1, 15, 8, 30, 0)
        assert format_datetime(dt) == "2025-01-15 08:30 UTC"


class TestSegmentFormatting:
    """Test segment formatting functions."""
    
    def test_format_segment(self):
        """Test formatting a single segment."""
        flight = Flight(
            flight_number="UA 384",
            origin="EWR",
            destination="DEN",
            departure_time=datetime(2025, 1, 15, 8, 0, 0),
            arrival_time=datetime(2025, 1, 15, 10, 30, 0),
            aircraft_type="777",
        )
        segment = Segment(flight=flight, sequence_number=1)
        
        result = format_segment(segment)
        assert "Leg 1" in result
        assert "UA 384" in result
        assert "EWR → DEN" in result
        assert "2025-01-15 08:00 UTC" in result
        assert "2025-01-15 10:30 UTC" in result
        assert "(2h 30m)" in result
    
    def test_format_segment_second_leg(self):
        """Test formatting second segment."""
        flight = Flight(
            flight_number="UA 500",
            origin="DEN",
            destination="SFO",
            departure_time=datetime(2025, 1, 15, 11, 45, 0),
            arrival_time=datetime(2025, 1, 15, 14, 20, 0),
            aircraft_type="787",
        )
        segment = Segment(flight=flight, sequence_number=2)
        
        result = format_segment(segment)
        assert "Leg 2" in result
        assert "UA 500" in result
        assert "DEN → SFO" in result


class TestItineraryFormatting:
    """Test itinerary formatting functions."""
    
    @pytest.fixture
    def sample_itinerary(self):
        """Create a sample 2-segment itinerary."""
        flight1 = Flight(
            flight_number="UA 384",
            origin="EWR",
            destination="DEN",
            departure_time=datetime(2025, 1, 15, 8, 0, 0),
            arrival_time=datetime(2025, 1, 15, 10, 30, 0),
            aircraft_type="777",
        )
        flight2 = Flight(
            flight_number="UA 500",
            origin="DEN",
            destination="EWR",
            departure_time=datetime(2025, 1, 15, 11, 45, 0),
            arrival_time=datetime(2025, 1, 15, 16, 20, 0),
            aircraft_type="787",
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        
        return Itinerary([segment1, segment2])
    
    def test_format_itinerary(self, sample_itinerary):
        """Test formatting a complete itinerary."""
        result = format_itinerary(sample_itinerary, rank=1)
        
        assert "Itinerary 1" in result
        assert "Leg 1" in result
        assert "Leg 2" in result
        assert "Summary:" in result
        assert "Total elapsed time" in result
        assert "Total airtime" in result
        assert "Total layover time" in result
        assert "Legs: 2" in result
    
    def test_format_no_solutions(self):
        """Test formatting no solutions message."""
        reason = "No flights available"
        result = format_no_solutions(reason)
        
        assert "No feasible itineraries found" in result
        assert reason in result
        assert "Suggestions:" in result


class TestResultsFormatting:
    """Test results formatting functions."""
    
    @pytest.fixture
    def sample_itineraries(self):
        """Create sample itineraries."""
        flight1 = Flight(
            flight_number="UA 384",
            origin="EWR",
            destination="DEN",
            departure_time=datetime(2025, 1, 15, 8, 0, 0),
            arrival_time=datetime(2025, 1, 15, 10, 30, 0),
            aircraft_type="777",
        )
        flight2 = Flight(
            flight_number="UA 500",
            origin="DEN",
            destination="EWR",
            departure_time=datetime(2025, 1, 15, 11, 45, 0),
            arrival_time=datetime(2025, 1, 15, 16, 20, 0),
            aircraft_type="787",
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        
        itinerary = Itinerary([segment1, segment2])
        return [itinerary]
    
    def test_format_results_with_solutions(self, sample_itineraries):
        """Test formatting results with solutions."""
        result = ItinerarySearchResult(
            itineraries=sample_itineraries,
            stats={},
            no_solution_reason=None,
        )
        
        output = format_results(result, max_results=10)
        
        assert "Found" in output
        assert "Itinerary" in output
    
    def test_format_results_no_solutions(self):
        """Test formatting results with no solutions."""
        result = ItinerarySearchResult(
            itineraries=[],
            stats={},
            no_solution_reason="No flights available",
        )
        
        output = format_results(result, max_results=10)
        
        assert "No feasible itineraries found" in output
        assert "No flights available" in output
    
    def test_format_results_max_results_limit(self, sample_itineraries):
        """Test that max_results limits displayed results."""
        # Create multiple itineraries
        itineraries = sample_itineraries * 5
        
        result = ItinerarySearchResult(
            itineraries=itineraries,
            stats={},
            no_solution_reason=None,
        )
        
        output = format_results(result, max_results=3)
        
        assert "showing top 3" in output


class TestArgumentValidation:
    """Test argument validation functions."""
    
    def test_validate_airport_code_valid(self):
        """Test validating valid airport codes."""
        assert validate_airport_code("EWR") == "EWR"
        assert validate_airport_code("ewr") == "EWR"
        assert validate_airport_code("  DEN  ") == "DEN"
    
    def test_validate_airport_code_invalid(self):
        """Test validating invalid airport codes."""
        from argparse import ArgumentTypeError
        with pytest.raises(ArgumentTypeError, match="Invalid airport code"):
            validate_airport_code("EW")

        with pytest.raises(ArgumentTypeError, match="Invalid airport code"):
            validate_airport_code("EWRR")

        with pytest.raises(ArgumentTypeError, match="Invalid airport code"):
            validate_airport_code("123")
    
    def test_parse_date_valid(self):
        """Test parsing valid dates."""
        from argparse import ArgumentTypeError
        assert parse_date_arg("2025-01-15") == datetime(2025, 1, 15).date()

    def test_parse_date_invalid(self):
        """Test parsing invalid dates."""
        from argparse import ArgumentTypeError
        with pytest.raises(ArgumentTypeError, match="Invalid date"):
            parse_date_arg("2025/01/15")

        with pytest.raises(ArgumentTypeError, match="Invalid date"):
            parse_date_arg("01-15-2025")

        with pytest.raises(ArgumentTypeError):
            parse_date_arg("invalid")


class TestConstraintBuilding:
    """Test constraint building from CLI arguments."""
    
    def test_build_constraints_return_to_origin(self):
        """Test building constraints for return-to-origin loop."""
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        end_time = datetime(2025, 1, 17, 8, 0, 0)
        
        constraints = build_constraints(
            origin="EWR",
            destination=None,  # None means return-to-origin
            legs=4,
            min_layover_minutes=45,
            max_elapsed_hours=48.0,
            start_time=start_time,
            end_time=end_time,
        )
        
        assert len(constraints) == 5  # LegCount, ReturnToOrigin, MinLayover, MaxElapsed, TimeWindow

        # Check that ReturnToOriginConstraint is included
        from status_optimizer.constraints import ReturnToOriginConstraint
        assert any(isinstance(c, ReturnToOriginConstraint) for c in constraints)
    
    def test_build_constraints_with_destination(self):
        """Test building constraints with specific destination."""
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        end_time = datetime(2025, 1, 17, 8, 0, 0)
        
        constraints = build_constraints(
            origin="EWR",
            destination="SFO",  # Different destination
            legs=2,
            min_layover_minutes=60,
            max_elapsed_hours=24.0,
            start_time=start_time,
            end_time=end_time,
        )
        
        # Should not have ReturnToOriginConstraint when destination differs
        from status_optimizer.constraints import ReturnToOriginConstraint
        assert not any(isinstance(c, ReturnToOriginConstraint) for c in constraints)

        # Should have LegCountConstraint with exact=2
        from status_optimizer.constraints import LegCountConstraint
        leg_constraint = next(c for c in constraints if isinstance(c, LegCountConstraint))
        assert leg_constraint.exact == 2

