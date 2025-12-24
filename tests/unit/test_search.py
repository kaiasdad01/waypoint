"""Unit tests for search orchestrator."""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, MagicMock

from status_optimizer.data.feeds.flight_feed import FlightFeed
from status_optimizer.domain.flight import Flight
from status_optimizer.search.search import ItinerarySearch, ItinerarySearchResult


class TestItinerarySearchResult:
    """Tests for ItinerarySearchResult class."""

    def test_found_solutions(self):
        """Test found_solutions property."""
        result = ItinerarySearchResult(
            itineraries=[Mock()],
            stats={},
        )
        assert result.found_solutions

    def test_no_solutions(self):
        """Test no solutions case."""
        result = ItinerarySearchResult(
            itineraries=[],
            stats={},
            no_solution_reason="No flights available",
        )
        assert not result.found_solutions
        assert result.no_solution_reason == "No flights available"


class TestItinerarySearch:
    """Tests for ItinerarySearch orchestrator."""

    @pytest.fixture
    def mock_flight_feed(self):
        """Create a mock FlightFeed."""
        feed = Mock(spec=FlightFeed)
        return feed

    @pytest.fixture
    def sample_flights(self):
        """Create sample flights for testing."""
        return [
            Flight("UA100", "EWR", "ORD",
                  datetime(2025, 1, 15, 9, 0, 0),
                  datetime(2025, 1, 15, 11, 0, 0), "737"),
            Flight("UA200", "ORD", "DEN",
                  datetime(2025, 1, 15, 12, 0, 0),
                  datetime(2025, 1, 15, 14, 0, 0), "737"),
            Flight("UA300", "DEN", "SFO",
                  datetime(2025, 1, 15, 15, 0, 0),
                  datetime(2025, 1, 15, 17, 0, 0), "737"),
            Flight("UA400", "SFO", "EWR",
                  datetime(2025, 1, 15, 18, 0, 0),
                  datetime(2025, 1, 15, 23, 0, 0), "777"),
        ]

    def test_search_basic(self, mock_flight_feed, sample_flights):
        """Test basic search functionality."""
        # Mock flight feed to return sample flights
        mock_flight_feed.get_flights_by_airport.return_value = sample_flights

        search = ItinerarySearch(mock_flight_feed)

        result = search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=4,
            constraints=[],
            beam_width=100,
        )

        # Verify flight feed was called
        mock_flight_feed.get_flights_by_airport.assert_called_once()
        call_args = mock_flight_feed.get_flights_by_airport.call_args
        assert call_args[0][0] == "EWR"  # origin

        # Should find the 4-leg loop
        assert result.found_solutions
        assert len(result.itineraries) >= 1

        # Verify itinerary
        itinerary = result.itineraries[0]
        assert itinerary.leg_count == 4
        assert itinerary.origin_airport == "EWR"
        assert itinerary.destination_airport == "EWR"

    def test_search_no_flights_available(self, mock_flight_feed):
        """Test search when no flights are available."""
        # Mock flight feed to return empty list
        mock_flight_feed.get_flights_by_airport.return_value = []

        search = ItinerarySearch(mock_flight_feed)

        result = search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=4,
            constraints=[],
        )

        assert not result.found_solutions
        assert "No flights available" in result.no_solution_reason

    def test_search_max_results_limiting(self, mock_flight_feed):
        """Test that max_results limits returned itineraries."""
        # Create many duplicate flights to generate multiple itineraries
        flights = []
        for i, hour in enumerate(range(8, 16)):  # Limit to prevent hour > 23
            flights.extend([
                Flight(f"UA{100+i}", "EWR", "ORD",
                      datetime(2025, 1, 15, hour, 0, 0),
                      datetime(2025, 1, 15, min(hour+2, 23), 0, 0), "737"),
                Flight(f"UA{200+i}", "ORD", "EWR",
                      datetime(2025, 1, 15, min(hour+3, 23), 0, 0),
                      datetime(2025, 1, 15, 23, 59, 0), "737"),
            ])

        mock_flight_feed.get_flights_by_airport.return_value = flights

        search = ItinerarySearch(mock_flight_feed)

        result = search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 7, 0, 0),
            target_legs=2,
            constraints=[],
            max_results=5,
        )

        # Should find solutions but limit to 5
        if result.found_solutions:
            assert len(result.itineraries) <= 5

    def test_search_respects_min_layover(self, mock_flight_feed):
        """Test that search respects minimum layover time."""
        # Create flights with tight connection
        flights = [
            Flight("UA100", "EWR", "ORD",
                  datetime(2025, 1, 15, 9, 0, 0),
                  datetime(2025, 1, 15, 11, 0, 0), "737"),
            Flight("UA200", "ORD", "EWR",
                  datetime(2025, 1, 15, 11, 30, 0),  # Only 30 min layover
                  datetime(2025, 1, 15, 14, 0, 0), "737"),
        ]

        mock_flight_feed.get_flights_by_airport.return_value = flights

        search = ItinerarySearch(mock_flight_feed)

        # With 45-minute min layover, should find no solution
        result = search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=2,
            constraints=[],
            min_layover=timedelta(minutes=45),
        )
        assert not result.found_solutions

    def test_search_respects_max_elapsed(self, mock_flight_feed):
        """Test that search respects maximum elapsed time."""
        # Create a long journey
        flights = [
            Flight("UA100", "EWR", "ORD",
                  datetime(2025, 1, 15, 9, 0, 0),
                  datetime(2025, 1, 15, 11, 0, 0), "737"),
            Flight("UA200", "ORD", "EWR",
                  datetime(2025, 1, 16, 20, 0, 0),  # Next day!
                  datetime(2025, 1, 17, 1, 0, 0), "737"),
        ]

        mock_flight_feed.get_flights_by_airport.return_value = flights

        search = ItinerarySearch(mock_flight_feed)

        # With 12-hour max elapsed, should find no solution
        result = search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=2,
            constraints=[],
            max_elapsed=timedelta(hours=12),
        )
        assert not result.found_solutions

    def test_search_with_constraints(self, mock_flight_feed, sample_flights):
        """Test search with constraints."""
        mock_flight_feed.get_flights_by_airport.return_value = sample_flights

        # Create a mock constraint that rejects all itineraries
        mock_constraint = Mock()
        mock_constraint.partial_ok.return_value = True
        mock_constraint.is_satisfied.return_value = False
        mock_constraint.violation.return_value = "Mock constraint violation"

        search = ItinerarySearch(mock_flight_feed)

        result = search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=4,
            constraints=[mock_constraint],
        )

        # Should find no solutions due to constraint
        assert not result.found_solutions

    def test_search_statistics(self, mock_flight_feed, sample_flights):
        """Test that search returns statistics."""
        mock_flight_feed.get_flights_by_airport.return_value = sample_flights

        search = ItinerarySearch(mock_flight_feed)

        result = search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=4,
            constraints=[],
        )

        # Should have statistics
        assert result.stats is not None
        assert isinstance(result.stats, dict)
        assert "candidates_generated" in result.stats

    def test_diagnose_no_solution(self, mock_flight_feed, sample_flights):
        """Test no-solution diagnosis."""
        mock_flight_feed.get_flights_by_airport.return_value = sample_flights

        search = ItinerarySearch(mock_flight_feed)

        # Search for impossible number of legs
        result = search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=10,  # Impossible with 4 available flights
            constraints=[],
        )

        assert not result.found_solutions
        assert result.no_solution_reason is not None
        assert len(result.no_solution_reason) > 0
