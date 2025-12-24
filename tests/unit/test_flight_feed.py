"""Unit tests for FlightFeed interface."""

import pytest
from abc import ABC
from datetime import date

from status_optimizer.data.feeds.flight_feed import FlightFeed
from status_optimizer.domain.flight import Flight


class TestFlightFeed:
    """Test cases for FlightFeed abstract base class."""
    
    def test_flight_feed_is_abstract(self):
        """Test that FlightFeed cannot be instantiated directly."""
        with pytest.raises(TypeError):
            FlightFeed()
    
    def test_flight_feed_is_abc_subclass(self):
        """Test that FlightFeed is a subclass of ABC."""
        assert issubclass(FlightFeed, ABC)
    
    def test_flight_feed_subclass_must_implement_get_flights(self):
        """Test that subclasses must implement get_flights."""
        class IncompleteFeed(FlightFeed):
            def get_flights_by_airport(self, airport: str, date_range: tuple[date, date]):
                return []
        
        with pytest.raises(TypeError):
            IncompleteFeed()
    
    def test_flight_feed_subclass_must_implement_get_flights_by_airport(self):
        """Test that subclasses must implement get_flights_by_airport."""
        class IncompleteFeed(FlightFeed):
            def get_flights(self, origin: str, destination: str, date_range: tuple[date, date]):
                return []
        
        with pytest.raises(TypeError):
            IncompleteFeed()
    
    def test_complete_flight_feed_implementation(self):
        """Test a complete FlightFeed implementation."""
        class MockFlightFeed(FlightFeed):
            def get_flights(
                self,
                origin: str,
                destination: str,
                date_range: tuple[date, date],
            ):
                return []
            
            def get_flights_by_airport(
                self,
                airport: str,
                date_range: tuple[date, date],
            ):
                return []
        
        feed = MockFlightFeed()
        assert feed is not None
        
        # Test methods exist and can be called
        result = feed.get_flights("DEN", "HNL", (date(2025, 1, 15), date(2025, 1, 15)))
        assert isinstance(result, list)
        
        result = feed.get_flights_by_airport("DEN", (date(2025, 1, 15), date(2025, 1, 15)))
        assert isinstance(result, list)
    
    def test_get_flights_signature(self):
        """Test that get_flights has correct signature."""
        import inspect
        
        sig = inspect.signature(FlightFeed.get_flights)
        params = list(sig.parameters.keys())
        
        assert 'origin' in params
        assert 'destination' in params
        assert 'date_range' in params
    
    def test_get_flights_by_airport_signature(self):
        """Test that get_flights_by_airport has correct signature."""
        import inspect
        
        sig = inspect.signature(FlightFeed.get_flights_by_airport)
        params = list(sig.parameters.keys())
        
        assert 'airport' in params
        assert 'date_range' in params

