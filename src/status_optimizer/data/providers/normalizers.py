"""Data normalization utilities for converting Excel data to domain models."""

import logging
from datetime import date, datetime, time, timedelta
from typing import Optional

import pandas as pd

from status_optimizer.domain.flight import Flight

logger = logging.getLogger(__name__)


def hhmm_float_to_time(hhmm_float: float) -> Optional[time]:
    """Convert time float to time object (handles HHMM format or day fraction)."""
    if hhmm_float is None:
        return None

    # Check if this is a day fraction (0.0 to < 1.0) or HHMM format (>= 1.0)
    if 0.0 <= hhmm_float < 1.0:
        # Day fraction format (Excel default)
        total_seconds = hhmm_float * 86400  # seconds in a day
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)

        # Validate
        if hours < 0 or hours >= 24 or minutes < 0 or minutes >= 60:
            return None

        try:
            return time(hours, minutes, seconds)
        except ValueError:
            return None

    elif hhmm_float >= 1.0 and hhmm_float < 2400:
        # HHMM format
        hhmm_int = int(hhmm_float)
        hours = hhmm_int // 100
        minutes = hhmm_int % 100

        # Validate
        if hours < 0 or hours >= 24 or minutes < 0 or minutes >= 60:
            return None

        try:
            return time(hours, minutes)
        except ValueError:
            return None

    else:
        return None


def local_time_to_utc_datetime(
    date: datetime.date,
    local_time: time,
    airport_code: str,
) -> datetime:
    """Combine date and time. Phase 0: assumes times are already UTC-equivalent."""
    return datetime.combine(date, local_time)


def normalize_airport_code(code: str) -> Optional[str]:
    """Normalize airport code to uppercase IATA format (3 letters)."""
    if not code or not isinstance(code, str):
        return None
    
    normalized = code.strip().upper()
    
    # Basic validation: IATA codes are 3 letters
    if len(normalized) == 3 and normalized.isalpha():
        return normalized
    
    return None


def normalize_aircraft_type(aircraft_type: str) -> Optional[str]:
    """Normalize aircraft type code."""
    if not aircraft_type or not isinstance(aircraft_type, str):
        return None
    
    # Strip whitespace and normalize
    normalized = str(aircraft_type).strip()
    
    if normalized:
        return normalized
    
    return None


def parse_dow(dow_value) -> Optional[set]:
    """Parse DOW value (1=Sun..7=Sat) to Python weekday set (0=Mon..6=Sun)."""
    if dow_value is None:
        return None
    
    # Convert to string to parse digits
    dow_str = str(int(dow_value))
    
    if not dow_str or not dow_str.isdigit():
        return None
    
    # Parse each digit as a weekday
    # Excel DOW: 1=Sunday, 2=Monday, 3=Tuesday, 4=Wednesday, 5=Thursday, 6=Friday, 7=Saturday
    # Python weekday: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
    # Mapping formula: (day_num + 5) % 7
    # Excel 1 (Sun) → (1+5)%7 = 6 (Sun) ✓
    # Excel 2 (Mon) → (2+5)%7 = 0 (Mon) ✓
    # Excel 7 (Sat) → (7+5)%7 = 5 (Sat) ✓
    weekdays = set()
    for digit in dow_str:
        day_num = int(digit)
        if 1 <= day_num <= 7:
            # Convert Excel DOW to Python weekday
            python_weekday = (day_num + 5) % 7
            weekdays.add(python_weekday)
    
    return weekdays if weekdays else None


def date_matches_dow(check_date: datetime.date, dow_set: set) -> bool:
    """Check if date's weekday is in the DOW set."""
    if not dow_set:
        return True  # No DOW restriction
    
    weekday = check_date.weekday()  # 0=Monday, 6=Sunday
    return weekday in dow_set


def excel_row_to_flight(
    row: pd.Series,
    flight_date: date,
    col_origin: str = 'Org',
    col_destination: str = 'Des',
    col_flight_number: str = 'Flight #',
    col_departs: str = 'Departs',
    col_arrives: str = 'Arrives',
    col_aircraft_type: str = 'A/C type',
) -> Optional[Flight]:
    """Convert Excel row to Flight. Returns None if invalid."""
    # Extract and normalize data
    origin = normalize_airport_code(row.get(col_origin))
    destination = normalize_airport_code(row.get(col_destination))
    flight_number = row.get(col_flight_number)
    aircraft_type = normalize_aircraft_type(row.get(col_aircraft_type))
    
    # Validate required fields
    if not origin or not destination or not flight_number:
        logger.debug(
            f"Skipping row with missing required fields: "
            f"origin={origin}, destination={destination}, flight_number={flight_number}"
        )
        return None
    
    # Parse times
    dep_time_local = hhmm_float_to_time(row.get(col_departs))
    arr_time_local = hhmm_float_to_time(row.get(col_arrives))
    
    if dep_time_local is None or arr_time_local is None:
        logger.debug(
            f"Skipping row with invalid times: "
            f"departs={row.get(col_departs)}, arrives={row.get(col_arrives)}"
        )
        return None
    
    try:
        # Convert local times to UTC datetimes
        dep_datetime_utc = local_time_to_utc_datetime(
            flight_date, dep_time_local, origin
        )
        arr_datetime_utc = local_time_to_utc_datetime(
            flight_date, arr_time_local, destination
        )
        
        # Handle next-day arrivals (if arrival time < departure time)
        if arr_time_local < dep_time_local:
            arr_datetime_utc += timedelta(days=1)
        
        # Create Flight object
        flight = Flight(
            flight_number=str(flight_number),
            origin=origin,
            destination=destination,
            departure_time=dep_datetime_utc,
            arrival_time=arr_datetime_utc,
            aircraft_type=aircraft_type or "UNKNOWN",
        )
        
        return flight
    except ValueError as e:
        logger.debug(f"Skipping invalid flight {flight_number} on {flight_date}: {e}")
        return None

