"""Unit tests for Constraint interface."""

import pytest
from abc import ABC
from datetime import datetime

from status_optimizer.constraints import Constraint
from status_optimizer.domain.flight import Flight
from status_optimizer.domain.segment import Segment
from status_optimizer.domain.itinerary import Itinerary


class TestConstraint:
    """Test cases for Constraint abstract base class."""
    
    def test_constraint_is_abstract(self):
        """Test that Constraint cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Constraint()
    
    def test_constraint_subclass_must_implement_is_satisfied(self):
        """Test that subclasses must implement is_satisfied."""
        class IncompleteConstraint(Constraint):
            def violation(self, itinerary: Itinerary):
                return None
        
        with pytest.raises(TypeError):
            IncompleteConstraint()
    
    def test_constraint_subclass_must_implement_violation(self):
        """Test that subclasses must implement violation."""
        class IncompleteConstraint(Constraint):
            def is_satisfied(self, itinerary: Itinerary):
                return True
        
        with pytest.raises(TypeError):
            IncompleteConstraint()
    
    def test_complete_constraint_subclass(self):
        """Test a complete constraint subclass implementation."""
        class AlwaysSatisfiedConstraint(Constraint):
            def is_satisfied(self, itinerary: Itinerary) -> bool:
                return True
            
            def violation(self, itinerary: Itinerary):
                return None
        
        constraint = AlwaysSatisfiedConstraint()
        assert constraint is not None
        
        # Create a test itinerary
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is True
        assert constraint.violation(itinerary) is None
    
    def test_constraint_with_violation(self):
        """Test a constraint that can be violated."""
        class NeverSatisfiedConstraint(Constraint):
            def is_satisfied(self, itinerary: Itinerary) -> bool:
                return False
            
            def violation(self, itinerary: Itinerary):
                return "This constraint is never satisfied"
        
        constraint = NeverSatisfiedConstraint()
        
        flight = Flight(
            flight_number="UA 384",
            origin="DEN",
            destination="HNL",
            departure_time=datetime(2025, 1, 15, 12, 5, 0),
            arrival_time=datetime(2025, 1, 15, 16, 33, 0),
            aircraft_type="777"
        )
        segment = Segment(flight=flight, sequence_number=1)
        itinerary = Itinerary([segment])
        
        assert constraint.is_satisfied(itinerary) is False
        assert constraint.violation(itinerary) == "This constraint is never satisfied"
    
    def test_partial_ok_defaults_to_true(self):
        """Test that partial_ok defaults to True (allow continuation)."""
        class TestConstraint(Constraint):
            def is_satisfied(self, itinerary: Itinerary) -> bool:
                return True
            
            def violation(self, itinerary: Itinerary):
                return None
        
        constraint = TestConstraint()
        
        # Default behavior: allow continuation
        state = {
            'airport': 'DEN',
            'time': datetime(2025, 1, 15, 12, 0, 0),
            'legs_used': 1,
            'legs_remaining': 3,
        }
        
        assert constraint.partial_ok(state) is True
    
    def test_partial_ok_can_be_overridden(self):
        """Test that partial_ok can be overridden for early pruning."""
        class PruningConstraint(Constraint):
            def is_satisfied(self, itinerary: Itinerary) -> bool:
                return True
            
            def violation(self, itinerary: Itinerary):
                return None
            
            def partial_ok(self, state: dict) -> bool:
                # Prune if we've used more than 5 legs
                legs_used = state.get('legs_used', 0)
                return legs_used <= 5
        
        constraint = PruningConstraint()
        
        state1 = {'legs_used': 3}
        assert constraint.partial_ok(state1) is True
        
        state2 = {'legs_used': 6}
        assert constraint.partial_ok(state2) is False
    
    def test_constraint_is_abc_subclass(self):
        """Test that Constraint is a subclass of ABC."""
        assert issubclass(Constraint, ABC)
    
    def test_constraint_methods_are_abstract(self):
        """Test that is_satisfied and violation are abstract methods."""
        assert hasattr(Constraint, 'is_satisfied')
        assert hasattr(Constraint, 'violation')
        assert hasattr(Constraint.is_satisfied, '__isabstractmethod__')
        assert hasattr(Constraint.violation, '__isabstractmethod__')

