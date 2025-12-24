"""Unit tests for Itinerary domain model."""

import pytest
from datetime import datetime, timedelta

from status_optimizer.domain.flight import Flight
from status_optimizer.domain.segment import Segment
from status_optimizer.domain.itinerary import Itinerary


class TestItinerary:
    """Test cases for Itinerary model."""
    
    def test_create_single_segment_itinerary(self):
        """Test creating an itinerary with a single segment."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)
        arr_time = datetime(2025, 1, 15, 16, 33, 0)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert itinerary.leg_count == 1
        assert itinerary.origin_airport == "DEN"
        assert itinerary.destination_airport == "HNL"
        assert itinerary.departure_time == dep_time
        assert itinerary.arrival_time == arr_time
    
    def test_create_multi_segment_itinerary(self):
        """Test creating an itinerary with multiple segments."""
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
            departure_time=datetime(2025, 1, 15, 18, 0, 0),  # After flight1 arrives
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        
        itinerary = Itinerary([segment1, segment2])
        
        assert itinerary.leg_count == 2
        assert itinerary.origin_airport == "DEN"
        assert itinerary.destination_airport == "LAX"
    
    def test_raises_error_if_empty_segments(self):
        """Test that ValueError is raised if segments list is empty."""
        with pytest.raises(ValueError, match="Itinerary must have at least one segment"):
            Itinerary([])
    
    def test_raises_error_if_segments_not_sequential(self):
        """Test that ValueError is raised if sequence numbers are not sequential."""
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        
        segment = Segment(flight=flight, sequence_number=2)  # Should be 1
        
        with pytest.raises(ValueError, match="Segments must be sequential"):
            Itinerary([segment])
    
    def test_raises_error_if_next_departure_before_previous_arrival(self):
        """Test that ValueError is raised if next segment departs before previous arrives."""
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
            departure_time=datetime(2025, 1, 15, 16, 0, 0),  # Before flight1 arrives!
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        
        with pytest.raises(ValueError, match="must be after"):
            Itinerary([segment1, segment2])
    
    def test_raises_error_if_next_departure_equals_previous_arrival(self):
        """Test that ValueError is raised if next segment departs exactly when previous arrives."""
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
            departure_time=datetime(2025, 1, 15, 16, 33, 0),  # Exactly when flight1 arrives
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        
        with pytest.raises(ValueError, match="must be after"):
            Itinerary([segment1, segment2])
    
    def test_raises_error_if_airports_dont_connect(self):
        """Test that ValueError is raised if segment origins don't match previous destinations."""
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
            origin="LAX",  # Doesn't match flight1 destination (HNL)
            destination="SFO",
            departure_time=datetime(2025, 1, 15, 18, 0, 0),
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        
        with pytest.raises(ValueError, match="does not match previous segment destination"):
            Itinerary([segment1, segment2])
    
    def test_total_elapsed_time_single_segment(self):
        """Test total elapsed time for single segment."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)
        arr_time = datetime(2025, 1, 15, 16, 33, 0)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert itinerary.total_elapsed_time == timedelta(hours=4, minutes=28)
    
    def test_total_elapsed_time_multi_segment(self):
        """Test total elapsed time for multi-segment itinerary."""
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
            departure_time=datetime(2025, 1, 15, 18, 0, 0),
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        itinerary = Itinerary([segment1, segment2])
        
        # Total elapsed: 12:05 to 22:30 = 10 hours 25 minutes
        assert itinerary.total_elapsed_time == timedelta(hours=10, minutes=25)
    
    def test_total_airtime_single_segment(self):
        """Test total airtime for single segment."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)
        arr_time = datetime(2025, 1, 15, 16, 33, 0)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert itinerary.total_airtime == timedelta(hours=4, minutes=28)
    
    def test_total_airtime_multi_segment(self):
        """Test total airtime for multi-segment itinerary."""
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),  # 4h 28m
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 500",
            origin="HNL",
            destination="LAX",
            departure_time=datetime(2025, 1, 15, 18, 0, 0),
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),  # 4h 30m
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        itinerary = Itinerary([segment1, segment2])
        
        # Total airtime: 4h 28m + 4h 30m = 8h 58m
        assert itinerary.total_airtime == timedelta(hours=8, minutes=58)
    
    def test_total_layover_time_single_segment(self):
        """Test total layover time for single segment (should be zero)."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)
        arr_time = datetime(2025, 1, 15, 16, 33, 0)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert itinerary.total_layover_time == timedelta(0)
    
    def test_total_layover_time_multi_segment(self):
        """Test total layover time calculation (time between flights at airports)."""
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
            departure_time=datetime(2025, 1, 15, 18, 0, 0),  # 1h 27m after flight1 arrives
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        itinerary = Itinerary([segment1, segment2])
        
        # Layover: 18:00 - 16:33 = 1h 27m
        assert itinerary.total_layover_time == timedelta(hours=1, minutes=27)
    
    def test_total_layover_time_multiple_connections(self):
        """Test total layover time with multiple connections."""
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
        
        flight3 = Flight(
            flight_number="UA 600",
            origin="LAX",
            destination="SFO",
            departure_time=datetime(2025, 1, 16, 1, 0, 0),  # 2h 30m layover (crosses midnight)
            arrival_time=datetime(2025, 1, 16, 2, 15, 0),
            aircraft_type="737"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        segment3 = Segment(flight=flight3, sequence_number=3)
        itinerary = Itinerary([segment1, segment2, segment3])
        
        # Total layover: 1h 27m + 2h 30m = 3h 57m
        assert itinerary.total_layover_time == timedelta(hours=3, minutes=57)
    
    def test_get_layover_times(self):
        """Test get_layover_times method returns list of individual layovers."""
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
            departure_time=datetime(2025, 1, 15, 18, 0, 0),
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        itinerary = Itinerary([segment1, segment2])
        
        layovers = itinerary.get_layover_times()
        assert len(layovers) == 1
        assert layovers[0] == timedelta(hours=1, minutes=27)
    
    def test_get_layover_times_single_segment(self):
        """Test get_layover_times returns empty list for single segment."""
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
        
        assert itinerary.get_layover_times() == []
    
    def test_equality_comparison(self):
        """Test Itinerary equality comparison."""
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        itinerary1 = Itinerary([segment1])
        itinerary2 = Itinerary([segment1])
        
        assert itinerary1 == itinerary2
    
    def test_repr_string(self):
        """Test string representation."""
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
            departure_time=datetime(2025, 1, 15, 18, 0, 0),
            arrival_time=datetime(2025, 1, 15, 22, 30, 0),
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        itinerary = Itinerary([segment1, segment2])
        
        repr_str = repr(itinerary)
        assert "Itinerary" in repr_str
        assert "2 segments" in repr_str
        assert "DEN" in repr_str
        assert "LAX" in repr_str
    
    def test_return_to_origin_itinerary(self):
        """Test return-to-origin itinerary (loop)."""
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
            destination="DEN",  # Returns to origin
            departure_time=datetime(2025, 1, 15, 18, 0, 0),
            arrival_time=datetime(2025, 1, 16, 0, 30, 0),  # Next day
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        itinerary = Itinerary([segment1, segment2])
        
        assert itinerary.origin_airport == "DEN"
        assert itinerary.destination_airport == "DEN"  # Returned to origin
        assert itinerary.leg_count == 2

