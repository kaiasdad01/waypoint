"""Beam search algorithm for itinerary optimization."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from status_optimizer.config import config
from status_optimizer.constraints import Constraint
from status_optimizer.domain.itinerary import Itinerary
from status_optimizer.search.graph import FlightGraph
from status_optimizer.search.state import SearchState

logger = logging.getLogger(__name__)


class BeamSearch:
    """Beam search for finding feasible itineraries.

    Keeps top K candidates at each depth level to prevent combinatorial explosion.
    """

    def __init__(
        self,
        graph: FlightGraph,
        constraints: List[Constraint],
        beam_width: int = config.search.beam_width,
        max_candidates: int = config.search.max_candidates,
    ):
        self.graph = graph
        self.constraints = constraints
        self.beam_width = beam_width
        self.max_candidates = max_candidates

        self.stats = {
            "candidates_generated": 0,
            "states_expanded": 0,
            "states_pruned_by_constraints": 0,
            "states_pruned_by_beam": 0,
            "complete_itineraries_found": 0,
        }

    def search(
        self,
        origin: str,
        start_time: datetime,
        target_legs: int,
        min_layover: timedelta,
        time_window_end: datetime,
    ) -> List[Itinerary]:
        """Find feasible itineraries using beam search."""
        logger.info(f"Beam search: origin={origin}, target_legs={target_legs}, beam_width={self.beam_width}")

        self.stats = {k: 0 for k in self.stats}
        current_beam: List[SearchState] = [SearchState.initial(origin, start_time)]
        complete_itineraries: List[Itinerary] = []

        for depth in range(target_legs):
            if not current_beam:
                logger.warning(f"Beam empty at depth {depth}, no solutions found")
                break

            next_beam: List[SearchState] = []

            for state in current_beam:
                self.stats["states_expanded"] += 1

                candidate_flights = self.graph.get_outgoing_flights(
                    state.current_airport,
                    state.current_time + min_layover,
                )

                for flight in candidate_flights:
                    if self.stats["candidates_generated"] >= self.max_candidates:
                        break

                    self.stats["candidates_generated"] += 1

                    try:
                        new_state = state.expand(flight)
                    except ValueError:
                        continue

                    is_feasible, _ = self._is_partial_feasible(new_state, time_window_end, target_legs)
                    if not is_feasible:
                        self.stats["states_pruned_by_constraints"] += 1
                        continue

                    new_state.score = self._score_state(new_state, target_legs)

                    if new_state.legs_used == target_legs and new_state.is_complete(target_legs):
                        # Complete itinerary found
                        try:
                            itinerary = Itinerary(new_state.segments)
                            if self._is_fully_feasible(itinerary):
                                complete_itineraries.append(itinerary)
                                self.stats["complete_itineraries_found"] += 1
                        except ValueError:
                            pass
                    elif new_state.legs_used < target_legs:
                        next_beam.append(new_state)

            # Keep top beam_width states
            if next_beam:
                next_beam.sort(key=lambda s: s.score, reverse=True)
                if len(next_beam) > self.beam_width:
                    self.stats["states_pruned_by_beam"] += len(next_beam) - self.beam_width
                current_beam = next_beam[:self.beam_width]
            else:
                current_beam = []

        # Sort by elapsed time
        complete_itineraries.sort(key=lambda itin: itin.total_elapsed_time)
        logger.info(f"Found {len(complete_itineraries)} complete itineraries")

        return complete_itineraries

    def _is_partial_feasible(
        self,
        state: SearchState,
        time_window_end: datetime,
        target_legs: int,
    ) -> tuple[bool, Optional[str]]:
        """Check if partial state can still lead to valid solution."""
        if state.current_time > time_window_end:
            return False, "Exceeded time window"

        for constraint in self.constraints:
            state_dict = {
                "airport": state.current_airport,
                "origin": state.origin_airport,
                "time": state.current_time,
                "elapsed": state.elapsed_time,
                "legs_used": state.legs_used,
                "legs_remaining": target_legs - state.legs_used,
            }
            if not constraint.partial_ok(state_dict):
                return False, constraint.__class__.__name__

        return True, None

    def _is_fully_feasible(self, itinerary: Itinerary) -> bool:
        """Check if complete itinerary satisfies all constraints."""
        return all(c.is_satisfied(itinerary) for c in self.constraints)

    def _score_state(self, state: SearchState, target_legs: int) -> float:
        """Score state (higher is better)."""
        score = 0.0

        # Prefer states closer to target
        progress = state.legs_used / target_legs
        score += progress * 100

        # Penalize longer elapsed times
        elapsed_hours = state.elapsed_time.total_seconds() / 3600
        score -= elapsed_hours * 0.1

        # Bonus for returning to origin when at target
        if state.legs_used == target_legs and state.current_airport == state.origin_airport:
            score += 50

        return score

    def get_stats(self) -> Dict[str, int]:
        """Get search statistics."""
        return self.stats.copy()

