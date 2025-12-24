"""Graph structure for flight route search."""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set

from status_optimizer.domain.flight import Flight


class FlightGraph:
    """Directed graph structure for flight route search.
    
    Nodes represent airports (IATA codes).
    Edges represent flights between airports, with departure/arrival times.
    
    The graph supports efficient queries like:
    - "What flights depart from airport X after time T?"
    - "What flights arrive at airport X before time T?"
    """
    
    def __init__(self, flights: List[Flight]):
        """Initialize FlightGraph from a list of Flight objects.
        
        Args:
            flights: List of Flight objects to build the graph from
        """
        # Outgoing edges: airport -> list of flights departing from that airport
        self._outgoing: Dict[str, List[Flight]] = defaultdict(list)
        
        # Incoming edges: airport -> list of flights arriving at that airport
        self._incoming: Dict[str, List[Flight]] = defaultdict(list)
        
        # All airports in the graph
        self._airports: Set[str] = set()
        
        # Build graph from flights
        for flight in flights:
            self.add_flight(flight)
    
    def add_flight(self, flight: Flight) -> None:
        """Add a flight to the graph.
        
        Args:
            flight: Flight object to add
        """
        origin = flight.origin
        destination = flight.destination
        
        self._outgoing[origin].append(flight)
        self._incoming[destination].append(flight)
        self._airports.add(origin)
        self._airports.add(destination)
    
    def get_outgoing_flights(
        self,
        airport: str,
        after_time: datetime,
    ) -> List[Flight]:
        """Get all flights departing from an airport after a given time.
        
        Args:
            airport: Origin airport IATA code
            after_time: Minimum departure time (inclusive)
            
        Returns:
            List of Flight objects departing from airport at or after after_time,
            sorted by departure time
        """
        flights = [
            flight for flight in self._outgoing.get(airport, [])
            if flight.departure_time >= after_time
        ]
        
        # Sort by departure time for consistent ordering
        flights.sort(key=lambda f: f.departure_time)
        
        return flights
    
    def get_incoming_flights(
        self,
        airport: str,
        before_time: datetime,
    ) -> List[Flight]:
        """Get all flights arriving at an airport before a given time.
        
        Args:
            airport: Destination airport IATA code
            before_time: Maximum arrival time (inclusive)
            
        Returns:
            List of Flight objects arriving at airport at or before before_time,
            sorted by arrival time
        """
        flights = [
            flight for flight in self._incoming.get(airport, [])
            if flight.arrival_time <= before_time
        ]
        
        # Sort by arrival time for consistent ordering
        flights.sort(key=lambda f: f.arrival_time)
        
        return flights
    
    def get_all_outgoing_flights(self, airport: str) -> List[Flight]:
        """Get all flights departing from an airport (regardless of time).
        
        Args:
            airport: Origin airport IATA code
            
        Returns:
            List of all Flight objects departing from airport,
            sorted by departure time
        """
        flights = self._outgoing.get(airport, [])
        flights.sort(key=lambda f: f.departure_time)
        return flights
    
    def get_all_incoming_flights(self, airport: str) -> List[Flight]:
        """Get all flights arriving at an airport (regardless of time).
        
        Args:
            airport: Destination airport IATA code
            
        Returns:
            List of all Flight objects arriving at airport,
            sorted by arrival time
        """
        flights = self._incoming.get(airport, [])
        flights.sort(key=lambda f: f.arrival_time)
        return flights
    
    def has_airport(self, airport: str) -> bool:
        """Check if an airport exists in the graph.
        
        Args:
            airport: Airport IATA code
            
        Returns:
            True if airport has any flights (incoming or outgoing)
        """
        return airport in self._airports
    
    def get_airports(self) -> Set[str]:
        """Get all airports in the graph.
        
        Returns:
            Set of all airport IATA codes
        """
        return self._airports.copy()
    
    def get_flight_count(self) -> int:
        """Get total number of flights in the graph.
        
        Returns:
            Total number of flights
        """
        return sum(len(flights) for flights in self._outgoing.values())
    
    def __repr__(self) -> str:
        """String representation of FlightGraph."""
        airport_count = len(self._airports)
        flight_count = self.get_flight_count()
        return f"FlightGraph({airport_count} airports, {flight_count} flights)"

