"""FlightFeed interface for flight schedule data providers."""

from abc import ABC, abstractmethod
from datetime import date
from typing import List

from status_optimizer.domain.flight import Flight


class FlightFeed(ABC):
    """Abstract base class for flight schedule data providers.
    
    FlightFeed implementations provide access to flight schedule data from
    various sources (Excel files, APIs, databases, etc.). All implementations
    must normalize data into Flight domain models with UTC times.
    
    Subclasses should implement:
    - get_flights: Get flights for a specific origin-destination pair
    - get_flights_by_airport: Get all flights from/to a specific airport
    """
    
    @abstractmethod
    def get_flights(
        self,
        origin: str,
        destination: str,
        date_range: tuple[date, date],
    ) -> List[Flight]:
        """Get flights for a specific origin-destination pair within a date range.
        
        Args:
            origin: Origin airport IATA code (e.g., "DEN")
            destination: Destination airport IATA code (e.g., "HNL")
            date_range: Tuple of (start_date, end_date) inclusive
            
        Returns:
            List of Flight objects matching the criteria, with times in UTC
            
        Raises:
            ValueError: If date_range is invalid (start > end)
            FileNotFoundError: If data source file doesn't exist (for file-based feeds)
        """
        pass
    
    @abstractmethod
    def get_flights_by_airport(
        self,
        airport: str,
        date_range: tuple[date, date],
    ) -> List[Flight]:
        """Get all flights from or to a specific airport within a date range.
        
        This method returns flights where the airport is either the origin
        or destination, useful for finding all connections at an airport.
        
        Args:
            airport: Airport IATA code (e.g., "DEN")
            date_range: Tuple of (start_date, end_date) inclusive
            
        Returns:
            List of Flight objects where airport is origin or destination,
            with times in UTC
            
        Raises:
            ValueError: If date_range is invalid (start > end)
            FileNotFoundError: If data source file doesn't exist (for file-based feeds)
        """
        pass

