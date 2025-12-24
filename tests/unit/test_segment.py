"""Unit tests for Segment domain model."""

import pytest
from datetime import datetime

from status_optimizer.domain.flight import Flight
from status_optimizer.domain.segment import Segment


class TestSegment:
    """Test cases for Segment model."""
    
    def test_create_segment_basic(self):
        """Test creating a basic segment."""
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
        
        assert segment.flight == flight
        assert segment.sequence_number == 1
    
    def test_sequence_number_must_be_positive(self):
        """Test that sequence_number must be >= 1."""
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
        
        with pytest.raises(ValueError, match="sequence_number must be >= 1"):
            Segment(flight=flight, sequence_number=0)
        
        with pytest.raises(ValueError, match="sequence_number must be >= 1"):
            Segment(flight=flight, sequence_number=-1)
    
    def test_sequence_number_can_be_greater_than_one(self):
        """Test that sequence_number can be > 1 for multi-segment itineraries."""
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
        
        segment = Segment(flight=flight, sequence_number=3)
        
        assert segment.sequence_number == 3
    
    def test_equality_comparison(self):
        """Test Segment equality comparison."""
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
        
        segment1 = Segment(flight=flight, sequence_number=1)
        segment2 = Segment(flight=flight, sequence_number=1)
        
        assert segment1 == segment2
    
    def test_inequality_different_flight(self):
        """Test Segment inequality with different flight."""
        dep_time1 = datetime(2025, 1, 15, 12, 5, 0)
        arr_time1 = datetime(2025, 1, 15, 16, 33, 0)
        
        dep_time2 = datetime(2025, 1, 15, 14, 10, 0)
        arr_time2 = datetime(2025, 1, 15, 18, 48, 0)
        
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time1,
            arrival_time=arr_time1,
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 1210",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time2,
            arrival_time=arr_time2,
            aircraft_type="777"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=1)
        
        assert segment1 != segment2
    
    def test_inequality_different_sequence_number(self):
        """Test Segment inequality with different sequence number."""
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
        
        segment1 = Segment(flight=flight, sequence_number=1)
        segment2 = Segment(flight=flight, sequence_number=2)
        
        assert segment1 != segment2
    
    def test_hash_equality(self):
        """Test that equal segments have equal hashes."""
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
        
        segment1 = Segment(flight=flight, sequence_number=1)
        segment2 = Segment(flight=flight, sequence_number=1)
        
        assert hash(segment1) == hash(segment2)
    
    def test_repr_string(self):
        """Test string representation."""
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
        
        repr_str = repr(segment)
        assert "Segment" in repr_str
        assert "1" in repr_str
        assert "UA 384" in repr_str
    
    def test_segment_with_multiple_sequence_numbers(self):
        """Test creating segments with different sequence numbers for multi-leg itinerary."""
        dep_time1 = datetime(2025, 1, 15, 12, 5, 0)
        arr_time1 = datetime(2025, 1, 15, 16, 33, 0)
        
        dep_time2 = datetime(2025, 1, 15, 18, 0, 0)
        arr_time2 = datetime(2025, 1, 15, 22, 30, 0)
        
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time1,
            arrival_time=arr_time1,
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 500",
            origin="HNL",
            destination="LAX",
            departure_time=dep_time2,
            arrival_time=arr_time2,
            aircraft_type="787"
        )
        
        segment1 = Segment(flight=flight1, sequence_number=1)
        segment2 = Segment(flight=flight2, sequence_number=2)
        
        assert segment1.sequence_number == 1
        assert segment2.sequence_number == 2
        assert segment1.flight.origin == "DEN"
        assert segment2.flight.origin == "HNL"

