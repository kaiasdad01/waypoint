"""Search orchestrator for itinerary optimization."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from status_optimizer.constraints import Constraint
from status_optimizer.data.feeds.flight_feed import FlightFeed
from status_optimizer.domain.itinerary import Itinerary
from status_optimizer.search.beam_search import BeamSearch
from status_optimizer.search.graph import FlightGraph

logger = logging.getLogger(__name__)


class ItinerarySearchResult:
    """Result of an itinerary search.

    Attributes:
        itineraries: List of feasible itineraries found
        stats: Search statistics
        no_solution_reason: Explanation if no itineraries found
    """

    def __init__(
        self,
        itineraries: List[Itinerary],
        stats: dict,
        no_solution_reason: Optional[str] = None,
    ):
        """Initialize ItinerarySearchResult.

        Args:
            itineraries: List of feasible itineraries
            stats: Search statistics dictionary
            no_solution_reason: Reason for no solutions (if applicable)
        """
        self.itineraries = itineraries
        self.stats = stats
        self.no_solution_reason = no_solution_reason

    @property
    def found_solutions(self) -> bool:
        """Check if any itineraries were found."""
        return len(self.itineraries) > 0

    def __repr__(self) -> str:
        """String representation of search result."""
        if self.found_solutions:
            return f"ItinerarySearchResult({len(self.itineraries)} itineraries found)"
        else:
            return f"ItinerarySearchResult(no solutions: {self.no_solution_reason})"


class ItinerarySearch:
    """Orchestrator for itinerary search.

    This class coordinates:
    - Loading flight data
    - Building flight graph
    - Running beam search with constraints
    - Returning results with helpful feedback

    Example:
        >>> search = ItinerarySearch(flight_feed)
        >>> result = search.search(
        ...     origin="EWR",
        ...     start_date=date(2025, 1, 15),
        ...     target_legs=4,
        ...     constraints=[...],
        ...     beam_width=200,
        ... )
        >>> if result.found_solutions:
        ...     for itinerary in result.itineraries[:10]:
        ...         print(itinerary)
    """

    def __init__(self, flight_feed: FlightFeed):
        """Initialize ItinerarySearch.

        Args:
            flight_feed: FlightFeed instance for loading flight data
        """
        self.flight_feed = flight_feed

    def search(
        self,
        origin: str,
        start_time: datetime,
        target_legs: int,
        constraints: List[Constraint],
        min_layover: timedelta = timedelta(minutes=45),
        max_elapsed: timedelta = timedelta(hours=48),
        beam_width: int = 200,
        max_candidates: int = 10000,
        max_results: int = 100,
    ) -> ItinerarySearchResult:
        """Search for feasible itineraries.

        Args:
            origin: Origin airport IATA code
            start_time: Search start time (UTC)
            target_legs: Target number of flight legs
            constraints: List of constraints to satisfy
            min_layover: Minimum layover time (default 45 minutes)
            max_elapsed: Maximum elapsed time (default 48 hours)
            beam_width: Beam width for search (default 200)
            max_candidates: Maximum candidates to generate (default 10000)
            max_results: Maximum results to return (default 100)

        Returns:
            ItinerarySearchResult containing feasible itineraries and stats
        """
        logger.info(
            f"Starting itinerary search: origin={origin}, "
            f"start_time={start_time}, target_legs={target_legs}"
        )

        # Calculate time window
        time_window_end = start_time + max_elapsed
        
        # For multi-leg searches, we need a wider date range to load flights
        # because loops can span multiple days and we need more flight options
        load_date_start = start_time.date()
        load_date_end = time_window_end.date()
        if target_legs >= 4:
            # Add extra days for 4+ leg searches to ensure we have enough flight options
            # This doesn't change the time window constraint, just loads more data
            extra_days = max(2, target_legs - 2)  # Add 2+ extra days for 4+ legs
            load_date_end = (time_window_end + timedelta(days=extra_days)).date()
            logger.info(
                f"Expanding flight data range for {target_legs}-leg search: "
                f"{load_date_start} to {load_date_end} (time window still {start_time.date()} to {time_window_end.date()})"
            )

        # Load flight data
        # For multi-leg searches, we need ALL flights in the network, not just
        # flights touching the origin airport, to build a complete graph
        logger.info("Loading flight data...")
        # Use get_all_flights if available, otherwise fall back to get_flights_by_airport
        if hasattr(self.flight_feed, 'get_all_flights'):
            flights = self.flight_feed.get_all_flights(
                (load_date_start, load_date_end),
            )
        else:
            # Fallback: load flights touching origin (less optimal but works)
            flights = self.flight_feed.get_flights_by_airport(
                origin,
                (load_date_start, load_date_end),
            )

        if not flights:
            logger.warning(f"No flights found for airport {origin}")
            return ItinerarySearchResult(
                itineraries=[],
                stats={},
                no_solution_reason=f"No flights available from {origin} in date range",
            )

        logger.info(f"Loaded {len(flights)} flights")

        # Build flight graph
        logger.info("Building flight graph...")
        graph = FlightGraph(flights)
        logger.info(f"Graph built: {graph}")

        # Verify origin airport exists
        if not graph.has_airport(origin):
            return ItinerarySearchResult(
                itineraries=[],
                stats={},
                no_solution_reason=f"Origin airport {origin} not found in flight data",
            )
        
        # Adjust start time to first available flight from origin if needed
        # This avoids starting at midnight when flights don't begin until later
        # Note: We do NOT adjust time_window_end here, as that would cut off
        # feasible loops that start later in the day. The time_window_end
        # remains based on the original start_time + max_elapsed.
        first_flights = graph.get_outgoing_flights(origin, start_time)
        if first_flights and first_flights[0].departure_time > start_time:
            original_start = start_time
            start_time = first_flights[0].departure_time
            logger.info(
                f"Adjusted start time from {original_start} to {start_time} "
                f"(first available flight from {origin}). "
                f"Time window still ends at {time_window_end} (based on original start + max_elapsed)"
            )

        # Run beam search
        logger.info("Running beam search...")
        # Increase beam width and max candidates for multi-leg searches
        # 4+ legs require significantly more exploration due to combinatorial explosion
        adjusted_beam_width = beam_width
        adjusted_max_candidates = max_candidates
        if target_legs >= 4:
            # Scale beam width with number of legs (4 legs needs ~1000, 5+ needs even more)
            adjusted_beam_width = max(beam_width, 1000)
            # Scale max candidates exponentially with depth - 4-leg searches need 500k+
            # to complete all depth levels with large route networks (293 airports)
            adjusted_max_candidates = max(max_candidates, 500000)
            logger.info(
                f"Adjusted search parameters for {target_legs}-leg search: "
                f"beam_width={adjusted_beam_width}, max_candidates={adjusted_max_candidates}"
            )
        
        beam_search = BeamSearch(
            graph=graph,
            constraints=constraints,
            beam_width=adjusted_beam_width,
            max_candidates=adjusted_max_candidates,
        )

        itineraries = beam_search.search(
            origin=origin,
            start_time=start_time,
            target_legs=target_legs,
            min_layover=min_layover,
            time_window_end=time_window_end,
        )

        stats = beam_search.get_stats()

        # Limit results
        if len(itineraries) > max_results:
            logger.info(f"Limiting results to top {max_results}")
            itineraries = itineraries[:max_results]

        # Determine no-solution reason if needed
        no_solution_reason = None
        if not itineraries:
            no_solution_reason = self._diagnose_no_solution(stats, target_legs)

        logger.info(f"Search complete: found {len(itineraries)} itineraries")

        return ItinerarySearchResult(
            itineraries=itineraries,
            stats=stats,
            no_solution_reason=no_solution_reason,
        )

    def _diagnose_no_solution(self, stats: dict, target_legs: int) -> str:
        """Diagnose why no solutions were found.

        Args:
            stats: Search statistics
            target_legs: Target number of legs

        Returns:
            Human-readable explanation
        """
        reasons = []

        if stats["candidates_generated"] == 0:
            reasons.append("No candidate paths could be generated")

        if stats["states_pruned_by_constraints"] > 0:
            reasons.append(
                f"{stats['states_pruned_by_constraints']} paths violated constraints"
            )

        if stats["complete_itineraries_found"] == 0:
            if stats["candidates_generated"] > 0:
                reasons.append(
                    f"No paths returned to origin with exactly {target_legs} legs"
                )

        if not reasons:
            reasons.append("Unknown reason - no feasible itineraries found")

        explanation = "; ".join(reasons)

        # Add suggestions
        suggestions = []
        if stats["states_pruned_by_constraints"] > stats["candidates_generated"] * 0.8:
            suggestions.append("Try relaxing constraints (e.g., increase max elapsed time)")

        if suggestions:
            explanation += ". Suggestions: " + "; ".join(suggestions)

        return explanation
