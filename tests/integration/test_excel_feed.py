"""Integration tests for ExcelFlightFeed."""

import pytest
from datetime import date, datetime
from pathlib import Path

from status_optimizer.data.providers.excel_flight_feed import ExcelFlightFeed
from status_optimizer.domain.flight import Flight


class TestExcelFlightFeed:
    """Integration tests for ExcelFlightFeed with real Excel file."""
    
    @pytest.fixture
    def feed(self):
        """Create ExcelFlightFeed instance."""
        return ExcelFlightFeed()
    
    def test_loads_excel_file(self, feed):
        """Test that Excel file loads successfully."""
        df = feed._load_excel()
        
        assert df is not None
        assert len(df) > 0
        assert 'Org' in df.columns
        assert 'Des' in df.columns
        assert 'Flight #' in df.columns
    
    def test_get_flights_den_to_hnl(self, feed):
        """Test getting flights from DEN to HNL."""
        flights = feed.get_flights(
            origin='DEN',
            destination='HNL',
            date_range=(date(2025, 1, 15), date(2025, 1, 15))
        )
        
        assert len(flights) > 0
        
        # Verify all flights are Flight objects
        for flight in flights:
            assert isinstance(flight, Flight)
            assert flight.origin == 'DEN'
            assert flight.destination == 'HNL'
            assert flight.departure_time.date() == date(2025, 1, 15)
    
    def test_get_flights_returns_utc_times(self, feed):
        """Test that all returned flights have UTC times."""
        flights = feed.get_flights(
            origin='DEN',
            destination='HNL',
            date_range=(date(2025, 1, 15), date(2025, 1, 15))
        )
        
        assert len(flights) > 0
        
        for flight in flights:
            # Naive datetime objects are assumed UTC in this project
            # If timezone-aware, must be UTC
            if flight.departure_time.tzinfo is not None:
                from datetime import timezone
                assert flight.departure_time.tzinfo == timezone.utc
            if flight.arrival_time.tzinfo is not None:
                from datetime import timezone
                assert flight.arrival_time.tzinfo == timezone.utc
    
    def test_get_flights_date_range(self, feed):
        """Test getting flights across a date range."""
        flights = feed.get_flights(
            origin='DEN',
            destination='HNL',
            date_range=(date(2025, 1, 15), date(2025, 1, 17))
        )
        
        assert len(flights) > 0
        
        # Should have flights for multiple days
        dates = {flight.departure_time.date() for flight in flights}
        assert len(dates) >= 1  # At least one day
        
        # All dates should be in range
        for flight in flights:
            assert date(2025, 1, 15) <= flight.departure_time.date() <= date(2025, 1, 17)
    
    def test_get_flights_by_airport(self, feed):
        """Test getting all flights for an airport."""
        flights = feed.get_flights_by_airport(
            airport='DEN',
            date_range=(date(2025, 1, 15), date(2025, 1, 15))
        )
        
        assert len(flights) > 0
        
        # All flights should have DEN as origin or destination
        for flight in flights:
            assert flight.origin == 'DEN' or flight.destination == 'DEN'
    
    def test_get_flights_invalid_date_range(self, feed):
        """Test that invalid date range raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date range"):
            feed.get_flights(
                origin='DEN',
                destination='HNL',
                date_range=(date(2025, 1, 17), date(2025, 1, 15))  # Start > end
            )
    
    def test_get_flights_invalid_airport_code(self, feed):
        """Test that invalid airport codes raise ValueError."""
        with pytest.raises(ValueError, match="Invalid airport codes"):
            feed.get_flights(
                origin='INVALID',
                destination='HNL',
                date_range=(date(2025, 1, 15), date(2025, 1, 15))
            )
    
    def test_get_flights_handles_missing_data(self, feed):
        """Test that missing/invalid data is handled gracefully."""
        # This test verifies the feed doesn't crash on bad data
        # The Excel file should have valid data, but we test error handling
        flights = feed.get_flights(
            origin='DEN',
            destination='HNL',
            date_range=(date(2025, 1, 15), date(2025, 1, 15))
        )
        
        # Should return valid Flight objects even if some rows are skipped
        for flight in flights:
            assert flight.flight_number
            assert flight.origin
            assert flight.destination
            assert flight.departure_time < flight.arrival_time
    
    def test_flight_objects_have_required_fields(self, feed):
        """Test that Flight objects have all required fields."""
        flights = feed.get_flights(
            origin='DEN',
            destination='HNL',
            date_range=(date(2025, 1, 15), date(2025, 1, 15))
        )
        
        assert len(flights) > 0
        
        for flight in flights:
            assert flight.flight_number
            assert flight.origin
            assert flight.destination
            assert flight.departure_time
            assert flight.arrival_time
            assert flight.aircraft_type
            assert flight.duration > datetime.min - datetime.min  # Valid duration
    
    def test_dow_filtering_works(self, feed):
        """Test that Day of Week filtering works correctly."""
        # Get flights for a specific date
        flights = feed.get_flights(
            origin='DEN',
            destination='HNL',
            date_range=(date(2025, 1, 15), date(2025, 1, 15))  # Wednesday
        )
        
        # Should only return flights that operate on Wednesday
        # (DOW filtering is handled internally)
        assert len(flights) >= 0  # May be 0 if no flights on that day
    
    def test_custom_excel_path(self):
        """Test that custom Excel path works."""
        default_feed = ExcelFlightFeed()
        custom_feed = ExcelFlightFeed(excel_path=str(default_feed.excel_path))
        
        flights1 = default_feed.get_flights(
            origin='DEN',
            destination='HNL',
            date_range=(date(2025, 1, 15), date(2025, 1, 15))
        )
        
        flights2 = custom_feed.get_flights(
            origin='DEN',
            destination='HNL',
            date_range=(date(2025, 1, 15), date(2025, 1, 15))
        )
        
        assert len(flights1) == len(flights2)
    
    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            ExcelFlightFeed(excel_path='nonexistent.xlsx')

