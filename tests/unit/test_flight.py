"""Unit tests for Flight domain model."""

import pytest
from datetime import datetime, timedelta, timezone

from status_optimizer.domain.flight import Flight


class TestFlight:
    """Test cases for Flight model."""
    
    def test_create_flight_basic(self):
        """Test creating a basic flight."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)  # Naive UTC
        arr_time = datetime(2025, 1, 15, 16, 33, 0)  # Naive UTC
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        assert flight.flight_number == "UA 384"
        assert flight.origin == "DEN"
        assert flight.destination == "HNL"
        assert flight.departure_time == dep_time
        assert flight.arrival_time == arr_time
        assert flight.aircraft_type == "777"
    
    def test_airport_codes_normalized_to_uppercase(self):
        """Test that airport codes are normalized to uppercase."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)
        arr_time = datetime(2025, 1, 15, 16, 33, 0)
        
        flight = Flight(
            flight_number="UA 384",
            origin="den",
            destination="hnl",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        assert flight.origin == "DEN"
        assert flight.destination == "HNL"
    
    def test_duration_property(self):
        """Test duration computed property."""
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
        
        expected_duration = timedelta(hours=4, minutes=28)
        assert flight.duration == expected_duration
    
    def test_duration_crosses_midnight(self):
        """Test duration calculation when flight crosses midnight."""
        dep_time = datetime(2025, 1, 15, 23, 59, 0)
        arr_time = datetime(2025, 1, 16, 5, 19, 0)  # Next day
        
        flight = Flight(
            flight_number="UA 1924",
            origin="DEN",
            destination="IAD",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        expected_duration = timedelta(hours=5, minutes=20)
        assert flight.duration == expected_duration
    
    def test_raises_error_if_departure_after_arrival(self):
        """Test that ValueError is raised if departure >= arrival."""
        dep_time = datetime(2025, 1, 15, 16, 33, 0)
        arr_time = datetime(2025, 1, 15, 12, 5, 0)  # Before departure
        
        with pytest.raises(ValueError, match="Departure time.*must be before arrival time"):
            Flight(
                flight_number="UA 384",
                origin="DEN",
                destination="HNL",
                departure_time=dep_time,
                arrival_time=arr_time,
                aircraft_type="777"
            )
    
    def test_raises_error_if_departure_equals_arrival(self):
        """Test that ValueError is raised if departure == arrival."""
        same_time = datetime(2025, 1, 15, 12, 5, 0)
        
        with pytest.raises(ValueError, match="Departure time.*must be before arrival time"):
            Flight(
                flight_number="UA 384",
                origin="DEN",
                destination="HNL",
                departure_time=same_time,
                arrival_time=same_time,
                aircraft_type="777"
            )
    
    def test_accepts_naive_datetime_as_utc(self):
        """Test that naive datetime objects are accepted (assumed UTC)."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)  # Naive
        arr_time = datetime(2025, 1, 15, 16, 33, 0)  # Naive
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        assert flight.departure_time == dep_time
        assert flight.arrival_time == arr_time
    
    def test_accepts_utc_timezone_aware_datetime(self):
        """Test that timezone-aware UTC datetime objects are accepted."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0, tzinfo=timezone.utc)
        arr_time = datetime(2025, 1, 15, 16, 33, 0, tzinfo=timezone.utc)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        assert flight.departure_time == dep_time
        assert flight.arrival_time == arr_time

    def test_equality_comparison(self):
        """Test Flight equality comparison."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)
        arr_time = datetime(2025, 1, 15, 16, 33, 0)
        
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        assert flight1 == flight2
    
    def test_inequality_different_flight_number(self):
        """Test Flight inequality with different flight number."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)
        arr_time = datetime(2025, 1, 15, 16, 33, 0)
        
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 385",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        assert flight1 != flight2
    
    def test_hash_equality(self):
        """Test that equal flights have equal hashes."""
        dep_time = datetime(2025, 1, 15, 12, 5, 0)
        arr_time = datetime(2025, 1, 15, 16, 33, 0)
        
        flight1 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        flight2 = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        assert hash(flight1) == hash(flight2)
    
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
        
        repr_str = repr(flight)
        assert "UA 384" in repr_str
        assert "DEN" in repr_str
        assert "HNL" in repr_str
        assert "dep:" in repr_str.lower()
        assert "arr:" in repr_str.lower()
    
    def test_dst_boundary_handling(self):
        """Test that DST boundaries don't cause issues (using UTC avoids this)."""
        # DST transition dates vary, but using UTC avoids the issue
        # Test with dates that would be problematic in local timezones
        dep_time = datetime(2025, 3, 10, 2, 0, 0)  # DST spring forward date
        arr_time = datetime(2025, 3, 10, 6, 0, 0)
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=dep_time,
            arrival_time=arr_time,
            aircraft_type="777"
        )
        
        assert flight.duration == timedelta(hours=4)

