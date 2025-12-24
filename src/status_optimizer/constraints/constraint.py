"""
Constraint interface for itinerary validation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from status_optimizer.domain.itinerary import Itinerary


class Constraint(ABC):
    """Abstract base class for itinerary constraints.
    
    - is_satisfied: Check if a complete itinerary meets the constraint
    - violation: Return reason if constraint is violated (for error messages)
    - partial_ok: Optional early pruning during search
    """
    @abstractmethod
    def is_satisfied(self, itinerary: Itinerary) -> bool:
        """
        Check if an itinerary satisfies this constraint.
        
        Args:
            itinerary: The itinerary to validate
            
        Returns:
            True if constraint is satisfied, False otherwise
        """
        pass
    
    @abstractmethod
    def violation(self, itinerary: Itinerary) -> Optional[str]:
        """
        Get violation reason if constraint is not satisfied.
        
        Args:
            itinerary: The itinerary to check
            
        Returns:
            Human-readable violation reason, or None if satisfied
        """
        pass
    
    def partial_ok(self, state: Dict[str, Any]) -> bool:
        """Check if a partial search state can still satisfy this constraint.
        
        This method allows early pruning during search by checking if a
        partial path can still lead to a valid solution. Not all constraints
        can be checked partially, so this defaults to True (allow continuation).
        
        Args:
            state: Dictionary containing partial search state, e.g.:
                - 'airport': current airport (str)
                - 'time': current time (datetime)
                - 'legs_used': number of segments used so far (int)
                - 'legs_remaining': number of segments remaining (int)
                - 'elapsed': elapsed time so far (timedelta)
                - 'origin': origin airport (str)
                
        Returns:
            True if partial state can still satisfy constraint, False to prune
        """
        # Default: allow continuation (cannot determine violation from partial state)
        return True

