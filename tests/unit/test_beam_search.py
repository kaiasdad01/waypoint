"""Unit tests for beam search algorithm."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from status_optimizer.constraints import Constraint
from status_optimizer.domain.flight import Flight
from status_optimizer.search.beam_search import BeamSearch
from status_optimizer.search.graph import FlightGraph
from status_optimizer.search.state import SearchState


class TestSearchState:
    """Tests for SearchState class."""

    def test_initial_state(self):
        """Test creating initial search state."""
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        state = SearchState.initial("EWR", start_time)

        assert state.current_airport == "EWR"
        assert state.origin_airport == "EWR"
        assert state.current_time == start_time
        assert state.legs_used == 0
        assert state.elapsed_time == timedelta(0)
        assert len(state.segments) == 0

    def test_expand_state(self):
        """Test expanding state with a flight."""
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        state = SearchState.initial("EWR", start_time)

        flight = Flight(
            flight_number="UA100",
            origin="EWR",
            destination="ORD",
            departure_time=datetime(2025, 1, 15, 9, 0, 0),
            arrival_time=datetime(2025, 1, 15, 11, 0, 0),
            aircraft_type="737",
        )

        new_state = state.expand(flight)

        assert new_state.current_airport == "ORD"
        assert new_state.current_time == datetime(2025, 1, 15, 11, 0, 0)
        assert new_state.legs_used == 1
        assert len(new_state.segments) == 1
        assert new_state.segments[0].flight == flight
        assert new_state.origin_airport == "EWR"

    def test_expand_state_invalid_origin(self):
        """Test expanding state with flight from wrong airport."""
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        state = SearchState.initial("EWR", start_time)

        flight = Flight(
            flight_number="UA200",
            origin="ORD",  # Wrong origin!
            destination="DEN",
            departure_time=datetime(2025, 1, 15, 9, 0, 0),
            arrival_time=datetime(2025, 1, 15, 11, 0, 0),
            aircraft_type="737",
        )

        with pytest.raises(ValueError, match="doesn't match current airport"):
            state.expand(flight)

    def test_expand_state_departure_before_current_time(self):
        """Test expanding state with flight departing too early."""
        start_time = datetime(2025, 1, 15, 10, 0, 0)
        state = SearchState.initial("EWR", start_time)

        flight = Flight(
            flight_number="UA100",
            origin="EWR",
            destination="ORD",
            departure_time=datetime(2025, 1, 15, 9, 0, 0),  # Before current time!
            arrival_time=datetime(2025, 1, 15, 11, 0, 0),
            aircraft_type="737",
        )

        with pytest.raises(ValueError, match="before current time"):
            state.expand(flight)

    def test_is_complete_return_to_origin(self):
        """Test checking if state is complete (return-to-origin)."""
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        state = SearchState.initial("EWR", start_time)

        # Add flights to return to origin
        f1 = Flight("UA100", "EWR", "ORD", datetime(2025, 1, 15, 9, 0, 0),
                   datetime(2025, 1, 15, 11, 0, 0), "737")
        f2 = Flight("UA200", "ORD", "DEN", datetime(2025, 1, 15, 12, 0, 0),
                   datetime(2025, 1, 15, 14, 0, 0), "737")
        f3 = Flight("UA300", "DEN", "SFO", datetime(2025, 1, 15, 15, 0, 0),
                   datetime(2025, 1, 15, 17, 0, 0), "737")
        f4 = Flight("UA400", "SFO", "EWR", datetime(2025, 1, 15, 18, 0, 0),
                   datetime(2025, 1, 15, 23, 0, 0), "737")

        state = state.expand(f1).expand(f2).expand(f3).expand(f4)

        assert state.is_complete(target_legs=4)
        assert not state.is_complete(target_legs=3)
        assert not state.is_complete(target_legs=5)

    def test_is_complete_not_at_origin(self):
        """Test that state is not complete if not at origin."""
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        state = SearchState.initial("EWR", start_time)

        f1 = Flight("UA100", "EWR", "ORD", datetime(2025, 1, 15, 9, 0, 0),
                   datetime(2025, 1, 15, 11, 0, 0), "737")

        state = state.expand(f1)

        assert not state.is_complete(target_legs=1)  # At ORD, not EWR


class TestBeamSearch:
    """Tests for BeamSearch class."""

    @pytest.fixture
    def simple_graph(self):
        """Create a simple test graph: EWR -> ORD -> DEN -> EWR."""
        flights = [
            Flight("UA100", "EWR", "ORD",
                  datetime(2025, 1, 15, 9, 0, 0),
                  datetime(2025, 1, 15, 11, 0, 0), "737"),
            Flight("UA200", "ORD", "DEN",
                  datetime(2025, 1, 15, 12, 0, 0),
                  datetime(2025, 1, 15, 14, 0, 0), "737"),
            Flight("UA300", "DEN", "EWR",
                  datetime(2025, 1, 15, 15, 0, 0),
                  datetime(2025, 1, 15, 20, 0, 0), "737"),
        ]
        return FlightGraph(flights)

    @pytest.fixture
    def loop_graph(self):
        """Create a graph with a 4-leg loop: EWR -> ORD -> DEN -> SFO -> EWR."""
        flights = [
            # Leg 1: EWR -> ORD
            Flight("UA100", "EWR", "ORD",
                  datetime(2025, 1, 15, 8, 0, 0),
                  datetime(2025, 1, 15, 10, 0, 0), "737"),
            # Leg 2: ORD -> DEN
            Flight("UA200", "ORD", "DEN",
                  datetime(2025, 1, 15, 11, 0, 0),
                  datetime(2025, 1, 15, 13, 0, 0), "737"),
            # Leg 3: DEN -> SFO
            Flight("UA300", "DEN", "SFO",
                  datetime(2025, 1, 15, 14, 0, 0),
                  datetime(2025, 1, 15, 16, 0, 0), "737"),
            # Leg 4: SFO -> EWR
            Flight("UA400", "SFO", "EWR",
                  datetime(2025, 1, 15, 17, 0, 0),
                  datetime(2025, 1, 15, 22, 0, 0), "777"),
        ]
        return FlightGraph(flights)

    def test_beam_search_simple_path(self, simple_graph):
        """Test beam search finds simple 3-leg loop."""
        beam_search = BeamSearch(
            graph=simple_graph,
            constraints=[],
            beam_width=10,
        )

        itineraries = beam_search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=3,
            min_layover=timedelta(minutes=45),
            time_window_end=datetime(2025, 1, 15, 23, 59, 59),
        )

        assert len(itineraries) == 1
        itinerary = itineraries[0]
        assert itinerary.leg_count == 3
        assert itinerary.origin_airport == "EWR"
        assert itinerary.destination_airport == "EWR"

    def test_beam_search_4_leg_loop(self, loop_graph):
        """Test beam search finds 4-leg return-to-origin loop."""
        beam_search = BeamSearch(
            graph=loop_graph,
            constraints=[],
            beam_width=10,
        )

        itineraries = beam_search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 7, 0, 0),
            target_legs=4,
            min_layover=timedelta(minutes=45),
            time_window_end=datetime(2025, 1, 15, 23, 59, 59),
        )

        assert len(itineraries) == 1
        itinerary = itineraries[0]
        assert itinerary.leg_count == 4
        assert itinerary.origin_airport == "EWR"
        assert itinerary.destination_airport == "EWR"

        # Verify route
        airports = [seg.flight.origin for seg in itinerary.segments]
        airports.append(itinerary.destination_airport)
        assert airports == ["EWR", "ORD", "DEN", "SFO", "EWR"]

    def test_beam_search_no_solution_wrong_leg_count(self, simple_graph):
        """Test beam search finds no solution when target legs is wrong."""
        beam_search = BeamSearch(
            graph=simple_graph,
            constraints=[],
            beam_width=10,
        )

        # Graph only has 3-leg path, asking for 4 legs
        itineraries = beam_search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=4,
            min_layover=timedelta(minutes=45),
            time_window_end=datetime(2025, 1, 15, 23, 59, 59),
        )

        assert len(itineraries) == 0

    def test_beam_search_no_solution_time_window(self, simple_graph):
        """Test beam search finds no solution when time window too tight."""
        beam_search = BeamSearch(
            graph=simple_graph,
            constraints=[],
            beam_width=10,
        )

        # Time window ends before last flight arrives
        itineraries = beam_search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=3,
            min_layover=timedelta(minutes=45),
            time_window_end=datetime(2025, 1, 15, 12, 0, 0),  # Too early!
        )

        assert len(itineraries) == 0

    def test_beam_search_respects_min_layover(self):
        """Test beam search respects minimum layover constraint."""
        # Create flights with tight connection
        flights = [
            Flight("UA100", "EWR", "ORD",
                  datetime(2025, 1, 15, 9, 0, 0),
                  datetime(2025, 1, 15, 11, 0, 0), "737"),
            Flight("UA200", "ORD", "DEN",
                  datetime(2025, 1, 15, 11, 30, 0),  # Only 30 min layover
                  datetime(2025, 1, 15, 13, 0, 0), "737"),
            Flight("UA300", "DEN", "EWR",
                  datetime(2025, 1, 15, 14, 0, 0),
                  datetime(2025, 1, 15, 19, 0, 0), "737"),
        ]
        graph = FlightGraph(flights)

        beam_search = BeamSearch(graph=graph, constraints=[], beam_width=10)

        # With 45-minute min layover, should find no solution
        itineraries = beam_search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=3,
            min_layover=timedelta(minutes=45),
            time_window_end=datetime(2025, 1, 15, 23, 59, 59),
        )
        assert len(itineraries) == 0

        # With 30-minute min layover, should find solution
        itineraries = beam_search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=3,
            min_layover=timedelta(minutes=30),
            time_window_end=datetime(2025, 1, 15, 23, 59, 59),
        )
        assert len(itineraries) == 1

    def test_beam_search_with_constraints(self, simple_graph):
        """Test beam search respects constraint partial_ok."""
        # Create a mock constraint that rejects all partial states
        mock_constraint = Mock(spec=Constraint)
        mock_constraint.partial_ok.return_value = False

        beam_search = BeamSearch(
            graph=simple_graph,
            constraints=[mock_constraint],
            beam_width=10,
        )

        itineraries = beam_search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=3,
            min_layover=timedelta(minutes=45),
            time_window_end=datetime(2025, 1, 15, 23, 59, 59),
        )

        assert len(itineraries) == 0
        assert mock_constraint.partial_ok.called

    def test_beam_search_statistics(self, simple_graph):
        """Test that beam search tracks statistics."""
        beam_search = BeamSearch(graph=simple_graph, constraints=[], beam_width=10)

        beam_search.search(
            origin="EWR",
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            target_legs=3,
            min_layover=timedelta(minutes=45),
            time_window_end=datetime(2025, 1, 15, 23, 59, 59),
        )

        stats = beam_search.get_stats()

        assert "candidates_generated" in stats
        assert "states_expanded" in stats
        assert "complete_itineraries_found" in stats
        assert stats["candidates_generated"] > 0
        assert stats["states_expanded"] > 0

    def test_beam_width_limiting(self):
        """Test that beam width limits number of states kept."""
        # Create a graph with many possible paths
        flights = []
        start_time = datetime(2025, 1, 15, 8, 0, 0)

        # EWR -> multiple destinations
        for i, dest in enumerate(["ORD", "DEN", "SFO", "LAX", "IAH"]):
            flights.append(
                Flight(f"UA{100+i}", "EWR", dest,
                      start_time + timedelta(hours=i),
                      start_time + timedelta(hours=i+2),
                      "737")
            )

        # Each destination -> EWR (return flights)
        for i, origin in enumerate(["ORD", "DEN", "SFO", "LAX", "IAH"]):
            flights.append(
                Flight(f"UA{200+i}", origin, "EWR",
                      start_time + timedelta(hours=i+3),
                      start_time + timedelta(hours=i+5),
                      "737")
            )

        graph = FlightGraph(flights)

        # Small beam width should still find solution
        beam_search = BeamSearch(graph=graph, constraints=[], beam_width=2)

        itineraries = beam_search.search(
            origin="EWR",
            start_time=start_time,
            target_legs=2,
            min_layover=timedelta(minutes=30),
            time_window_end=start_time + timedelta(hours=24),
        )

        # Should find at least some solutions despite narrow beam
        assert len(itineraries) > 0
        stats = beam_search.get_stats()
        # With beam_width=2 and 5 possible first flights, should have pruned some
        assert stats.get("states_pruned_by_beam", 0) > 0
