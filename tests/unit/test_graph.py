"""Unit tests for FlightGraph."""

import pytest
from datetime import datetime

from status_optimizer.domain.flight import Flight
from status_optimizer.search.graph import FlightGraph


class TestFlightGraph:
    """Test cases for FlightGraph."""
    
    @pytest.fixture
    def sample_flights(self):
        """Create sample flights for testing."""
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
        
        flight3 = Flight(
            flight_number="UA 600",
            origin="DEN",
            destination="LAX",
            departure_time=datetime(2025, 1, 15, 10, 0, 0),
            arrival_time=datetime(2025, 1, 15, 12, 0, 0),
            aircraft_type="737"
        )
        
        return [flight1, flight2, flight3]
    
    def test_create_graph_from_flights(self, sample_flights):
        """Test creating graph from list of flights."""
        graph = FlightGraph(sample_flights)
        
        assert graph.get_flight_count() == 3
        assert len(graph.get_airports()) == 3
        assert "DEN" in graph.get_airports()
        assert "HNL" in graph.get_airports()
        assert "LAX" in graph.get_airports()
    
    def test_get_outgoing_flights(self, sample_flights):
        """Test getting outgoing flights from an airport."""
        graph = FlightGraph(sample_flights)
        
        flights = graph.get_outgoing_flights(
            "DEN",
            datetime(2025, 1, 15, 11, 0, 0)
        )
        
        assert len(flights) == 1  # Only UA 384 (UA 600 departs at 10:00, before 11:00)
        assert flights[0].flight_number == "UA 384"
    
    def test_get_outgoing_flights_time_filter(self, sample_flights):
        """Test that outgoing flights are filtered by time."""
        graph = FlightGraph(sample_flights)
        
        # Get flights after 10:00 (should include both UA 600 and UA 384)
        flights = graph.get_outgoing_flights(
            "DEN",
            datetime(2025, 1, 15, 10, 0, 0)
        )
        
        assert len(flights) == 2
        assert flights[0].flight_number == "UA 600"  # Earlier departure
        assert flights[1].flight_number == "UA 384"
        
        # Get flights after 13:00 (should include none, UA 384 departs at 12:05)
        flights = graph.get_outgoing_flights(
            "DEN",
            datetime(2025, 1, 15, 13, 0, 0)
        )
        
        assert len(flights) == 0
    
    def test_get_outgoing_flights_no_matches(self, sample_flights):
        """Test getting outgoing flights when none match."""
        graph = FlightGraph(sample_flights)
        
        flights = graph.get_outgoing_flights(
            "DEN",
            datetime(2025, 1, 16, 0, 0, 0)  # After all flights
        )
        
        assert len(flights) == 0
    
    def test_get_outgoing_flights_nonexistent_airport(self, sample_flights):
        """Test getting outgoing flights from nonexistent airport."""
        graph = FlightGraph(sample_flights)
        
        flights = graph.get_outgoing_flights(
            "SFO",
            datetime(2025, 1, 15, 0, 0, 0)
        )
        
        assert len(flights) == 0
    
    def test_get_incoming_flights(self, sample_flights):
        """Test getting incoming flights to an airport."""
        graph = FlightGraph(sample_flights)
        
        flights = graph.get_incoming_flights(
            "LAX",
            datetime(2025, 1, 15, 23, 0, 0)
        )
        
        assert len(flights) == 2  # UA 500 and UA 600
        assert flights[0].flight_number == "UA 600"  # Earlier arrival
        assert flights[1].flight_number == "UA 500"
    
    def test_get_incoming_flights_time_filter(self, sample_flights):
        """Test that incoming flights are filtered by time."""
        graph = FlightGraph(sample_flights)
        
        # Get flights arriving before 15:00
        flights = graph.get_incoming_flights(
            "LAX",
            datetime(2025, 1, 15, 15, 0, 0)
        )
        
        assert len(flights) == 1
        assert flights[0].flight_number == "UA 600"
    
    def test_get_all_outgoing_flights(self, sample_flights):
        """Test getting all outgoing flights regardless of time."""
        graph = FlightGraph(sample_flights)
        
        flights = graph.get_all_outgoing_flights("DEN")
        
        assert len(flights) == 2
        assert flights[0].flight_number == "UA 600"
        assert flights[1].flight_number == "UA 384"
    
    def test_get_all_incoming_flights(self, sample_flights):
        """Test getting all incoming flights regardless of time."""
        graph = FlightGraph(sample_flights)
        
        flights = graph.get_all_incoming_flights("LAX")
        
        assert len(flights) == 2
        assert flights[0].flight_number == "UA 600"
        assert flights[1].flight_number == "UA 500"
    
    def test_has_airport(self, sample_flights):
        """Test checking if airport exists in graph."""
        graph = FlightGraph(sample_flights)
        
        assert graph.has_airport("DEN") is True
        assert graph.has_airport("HNL") is True
        assert graph.has_airport("LAX") is True
        assert graph.has_airport("SFO") is False
    
    def test_get_airports(self, sample_flights):
        """Test getting all airports."""
        graph = FlightGraph(sample_flights)
        
        airports = graph.get_airports()
        
        assert airports == {"DEN", "HNL", "LAX"}
        assert isinstance(airports, set)
    
    def test_add_flight(self, sample_flights):
        """Test adding a flight to existing graph."""
        graph = FlightGraph(sample_flights)
        
        new_flight = Flight(
            flight_number="UA 700",
            origin="SFO",
            destination="DEN",
            departure_time=datetime(2025, 1, 15, 14, 0, 0),
            arrival_time=datetime(2025, 1, 15, 18, 0, 0),
            aircraft_type="737"
        )
        
        graph.add_flight(new_flight)
        
        assert graph.get_flight_count() == 4
        assert "SFO" in graph.get_airports()
        assert len(graph.get_all_outgoing_flights("SFO")) == 1
        assert len(graph.get_all_incoming_flights("DEN")) == 1
    
    def test_empty_graph(self):
        """Test creating graph with no flights."""
        graph = FlightGraph([])
        
        assert graph.get_flight_count() == 0
        assert len(graph.get_airports()) == 0
        assert graph.get_outgoing_flights("DEN", datetime(2025, 1, 15, 0, 0, 0)) == []
    
    def test_flights_sorted_by_time(self, sample_flights):
        """Test that flights are returned sorted by time."""
        graph = FlightGraph(sample_flights)
        
        # Add another flight with time between existing ones
        flight4 = Flight(
            flight_number="UA 450",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 11, 0, 0),  # Between UA 600 and UA 384
            arrival_time=datetime(2025, 1, 15, 15, 0, 0),
            aircraft_type="787"
        )
        graph.add_flight(flight4)
        
        flights = graph.get_all_outgoing_flights("DEN")
        
        assert len(flights) == 3
        assert flights[0].departure_time == datetime(2025, 1, 15, 10, 0, 0)
        assert flights[1].departure_time == datetime(2025, 1, 15, 11, 0, 0)
        assert flights[2].departure_time == datetime(2025, 1, 15, 12, 5, 0)
    
    def test_repr_string(self, sample_flights):
        """Test string representation."""
        graph = FlightGraph(sample_flights)
        
        repr_str = repr(graph)
        assert "FlightGraph" in repr_str
        assert "3 airports" in repr_str
        assert "3 flights" in repr_str

