"""ExcelFlightFeed implementation for reading United routes from Excel file."""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd

from status_optimizer.data.feeds.flight_feed import FlightFeed
from status_optimizer.data.providers.normalizers import (
    date_matches_dow,
    excel_row_to_flight,
    normalize_airport_code,
    parse_dow,
)
from status_optimizer.domain.flight import Flight

logger = logging.getLogger(__name__)


class ExcelFlightFeed(FlightFeed):
    """FlightFeed implementation that reads from United routes Excel file.
    
    Reads flight schedule data from `data/united-routes.xlsx` and converts
    it to Flight domain models. Handles timezone conversion, data normalization,
    and Day of Week (DOW) filtering.
    
    The Excel file contains recurring schedules (not specific dates), so this
    implementation generates Flight objects for each date in the requested range
    that matches the DOW pattern.
    """
    
    # Excel column mappings
    COL_ORIGIN = 'Org'
    COL_DESTINATION = 'Des'
    COL_FLIGHT_NUMBER = 'Flight #'
    COL_DEPARTS = 'Departs'
    COL_ARRIVES = 'Arrives'
    COL_AIRCRAFT_TYPE = 'A/C type'
    COL_DOW = 'DOW'
    COL_CARRIER = 'Carrier'
    
    def __init__(self, excel_path: Optional[str] = None):
        """Initialize ExcelFlightFeed.
        
        Args:
            excel_path: Path to Excel file. If None, uses default
                       `data/united-routes.xlsx` relative to project root.
        """
        if excel_path is None:
            # Default to data/united-routes.xlsx relative to project root
            # File is at: src/status_optimizer/data/providers/excel_flight_feed.py
            # Go up 4 levels to get to project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            excel_path = project_root / 'data' / 'united-routes.xlsx'
        
        self.excel_path = Path(excel_path)
        
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.excel_path}")
        
        # Cache for loaded Excel data
        self._df: Optional[pd.DataFrame] = None
    
    def _load_excel(self) -> pd.DataFrame:
        """Load Excel file into DataFrame.
        
        Returns:
            DataFrame with flight schedule data
            
        Raises:
            FileNotFoundError: If Excel file doesn't exist
            ValueError: If Excel file cannot be parsed
        """
        if self._df is not None:
            return self._df
        
        try:
            self._df = pd.read_excel(self.excel_path)
            logger.info(f"Loaded {len(self._df)} rows from {self.excel_path}")
            return self._df
        except Exception as e:
            raise ValueError(f"Failed to load Excel file {self.excel_path}: {e}") from e
    
    def _row_to_flights(
        self,
        row: pd.Series,
        date_range: tuple[date, date],
    ) -> List[Flight]:
        """Convert a single Excel row to Flight objects for matching dates.
        
        Uses the excel_row_to_flight normalizer function to convert Excel data
        to Flight domain models. Generates flights for each date in the range
        that matches the Day of Week pattern.
        
        Args:
            row: DataFrame row with flight schedule data
            date_range: Tuple of (start_date, end_date) inclusive
            
        Returns:
            List of Flight objects (one per matching date)
        """
        flights = []
        
        # Parse DOW to filter dates
        dow_set = parse_dow(row.get(self.COL_DOW))
        
        # Generate flights for each date in range that matches DOW
        start_date, end_date = date_range
        current_date = start_date
        
        while current_date <= end_date:
            # Check if this date matches the DOW pattern
            if date_matches_dow(current_date, dow_set):
                # Use normalizer function to convert row to Flight
                flight = excel_row_to_flight(
                    row,
                    current_date,
                    col_origin=self.COL_ORIGIN,
                    col_destination=self.COL_DESTINATION,
                    col_flight_number=self.COL_FLIGHT_NUMBER,
                    col_departs=self.COL_DEPARTS,
                    col_arrives=self.COL_ARRIVES,
                    col_aircraft_type=self.COL_AIRCRAFT_TYPE,
                )
                
                if flight is not None:
                    flights.append(flight)
            
            current_date += timedelta(days=1)
        
        return flights
    
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
        """
        if date_range[0] > date_range[1]:
            raise ValueError(f"Invalid date range: start {date_range[0]} > end {date_range[1]}")
        
        origin_norm = normalize_airport_code(origin)
        dest_norm = normalize_airport_code(destination)
        
        if not origin_norm or not dest_norm:
            raise ValueError(f"Invalid airport codes: origin={origin}, destination={destination}")
        
        df = self._load_excel()
        
        # Filter by origin and destination
        mask = (
            (df[self.COL_ORIGIN].str.upper().str.strip() == origin_norm) &
            (df[self.COL_DESTINATION].str.upper().str.strip() == dest_norm)
        )
        matching_rows = df[mask]
        
        # Convert rows to Flight objects
        all_flights = []
        for _, row in matching_rows.iterrows():
            flights = self._row_to_flights(row, date_range)
            all_flights.extend(flights)
        
        logger.info(
            f"Found {len(all_flights)} flights for {origin_norm} -> {dest_norm} "
            f"in date range {date_range[0]} to {date_range[1]}"
        )
        
        return all_flights
    
    def get_flights_by_airport(
        self,
        airport: str,
        date_range: tuple[date, date],
    ) -> List[Flight]:
        """Get all flights from or to a specific airport within a date range.
        
        Args:
            airport: Airport IATA code (e.g., "DEN")
            date_range: Tuple of (start_date, end_date) inclusive
            
        Returns:
            List of Flight objects where airport is origin or destination,
            with times in UTC
        """
        if date_range[0] > date_range[1]:
            raise ValueError(f"Invalid date range: start {date_range[0]} > end {date_range[1]}")
        
        airport_norm = normalize_airport_code(airport)
        
        if not airport_norm:
            raise ValueError(f"Invalid airport code: {airport}")
        
        df = self._load_excel()
        
        # Filter by airport (origin or destination)
        mask = (
            (df[self.COL_ORIGIN].str.upper().str.strip() == airport_norm) |
            (df[self.COL_DESTINATION].str.upper().str.strip() == airport_norm)
        )
        matching_rows = df[mask]
        
        # Convert rows to Flight objects
        all_flights = []
        for _, row in matching_rows.iterrows():
            flights = self._row_to_flights(row, date_range)
            all_flights.extend(flights)
        
        logger.info(
            f"Found {len(all_flights)} flights for airport {airport_norm} "
            f"in date range {date_range[0]} to {date_range[1]}"
        )
        
        return all_flights
    
    def get_all_flights(self, date_range: tuple[date, date]) -> List[Flight]:
        """Get all flights in the date range, regardless of airports.
        
        This is useful for building a complete flight graph for multi-leg searches.
        
        Args:
            date_range: Tuple of (start_date, end_date) inclusive
            
        Returns:
            List of all Flight objects in the date range, with times in UTC
        """
        if date_range[0] > date_range[1]:
            raise ValueError(f"Invalid date range: start {date_range[0]} > end {date_range[1]}")
        
        df = self._load_excel()
        
        # Convert all rows to Flight objects
        all_flights = []
        for _, row in df.iterrows():
            flights = self._row_to_flights(row, date_range)
            all_flights.extend(flights)
        
        logger.info(
            f"Found {len(all_flights)} total flights "
            f"in date range {date_range[0]} to {date_range[1]}"
        )
        
        return all_flights

