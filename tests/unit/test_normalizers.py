"""Unit tests for data normalization utilities."""

import pytest
import pandas as pd
from datetime import date, datetime, time

from status_optimizer.data.providers.normalizers import (
    excel_row_to_flight,
    hhmm_float_to_time,
    local_time_to_utc_datetime,
    normalize_airport_code,
    normalize_aircraft_type,
    parse_dow,
    date_matches_dow,
)
from status_optimizer.domain.flight import Flight


class TestNormalizers:
    """Test cases for normalization utilities."""
    
    def test_hhmm_float_to_time(self):
        """Test HHMM float to time conversion."""
        assert hhmm_float_to_time(1205.0) == time(12, 5)
        assert hhmm_float_to_time(1633.0) == time(16, 33)
        assert hhmm_float_to_time(2359.0) == time(23, 59)
        assert hhmm_float_to_time(0.0) == time(0, 0)
        assert hhmm_float_to_time(519.0) == time(5, 19)
    
    def test_hhmm_float_to_time_invalid(self):
        """Test HHMM float conversion with invalid values."""
        assert hhmm_float_to_time(None) is None
        assert hhmm_float_to_time(-1.0) is None
        assert hhmm_float_to_time(2400.0) is None
        assert hhmm_float_to_time(2500.0) is None
        assert hhmm_float_to_time(1260.0) is None  # Invalid minutes
    
    def test_normalize_airport_code(self):
        """Test airport code normalization."""
        assert normalize_airport_code("DEN") == "DEN"
        assert normalize_airport_code("den") == "DEN"
        assert normalize_airport_code("  HNL  ") == "HNL"
        assert normalize_airport_code("LAX") == "LAX"
    
    def test_normalize_airport_code_invalid(self):
        """Test airport code normalization with invalid values."""
        assert normalize_airport_code(None) is None
        assert normalize_airport_code("") is None
        assert normalize_airport_code("AB") is None  # Too short
        assert normalize_airport_code("ABCD") is None  # Too long
        assert normalize_airport_code("12A") is None  # Not all letters
    
    def test_normalize_aircraft_type(self):
        """Test aircraft type normalization."""
        assert normalize_aircraft_type("777") == "777"
        assert normalize_aircraft_type("  CRJ  ") == "CRJ"
        assert normalize_aircraft_type("787") == "787"
    
    def test_normalize_aircraft_type_invalid(self):
        """Test aircraft type normalization with invalid values."""
        assert normalize_aircraft_type(None) is None
        assert normalize_aircraft_type("") is None
    
    def test_parse_dow(self):
        """Test Day of Week parsing."""
        # All days (1234567 = Sun-Sat)
        dow_set = parse_dow(1234567)
        assert dow_set == {0, 1, 2, 3, 4, 5, 6}
        
        # Single day (Saturday = 7)
        dow_set = parse_dow(7)
        assert dow_set == {5}  # Saturday → Python weekday 5
        
        # Single day (Sunday = 1)
        dow_set = parse_dow(1)
        assert dow_set == {6}  # Sunday → Python weekday 6
        
        # Single day (Monday = 2)
        dow_set = parse_dow(2)
        assert dow_set == {0}  # Monday → Python weekday 0
        
        # Sun-Thu (12345)
        dow_set = parse_dow(12345)
        assert dow_set == {6, 0, 1, 2, 3}  # Sun, Mon, Tue, Wed, Thu
    
    def test_parse_dow_invalid(self):
        """Test DOW parsing with invalid values."""
        assert parse_dow(None) is None
        assert parse_dow(0) is None  # No valid days
    
    def test_date_matches_dow(self):
        """Test date matching against DOW set."""
        # Wednesday (2025-01-15 is a Wednesday, weekday=2)
        check_date = date(2025, 1, 15)
        
        # All days - should match
        assert date_matches_dow(check_date, {0, 1, 2, 3, 4, 5, 6}) is True
        
        # Wednesday only - should match
        assert date_matches_dow(check_date, {2}) is True
        
        # Monday only - should not match
        assert date_matches_dow(check_date, {0}) is False
        
        # No DOW restriction - should match
        assert date_matches_dow(check_date, None) is True
        assert date_matches_dow(check_date, set()) is True
    
    def test_local_time_to_utc_datetime(self):
        """Test local time to UTC datetime conversion."""
        flight_date = date(2025, 1, 15)
        local_time = time(12, 5)
        
        utc_dt = local_time_to_utc_datetime(flight_date, local_time, "DEN")
        
        assert isinstance(utc_dt, datetime)
        assert utc_dt.date() == flight_date
        assert utc_dt.time() == local_time  # Simplified for Phase 0
    
    def test_excel_row_to_flight(self):
        """Test converting Excel row to Flight model."""
        row = pd.Series({
            'Org': 'DEN',
            'Des': 'HNL',
            'Flight #': 'UA 384',
            'Departs': 1205.0,
            'Arrives': 1633.0,
            'A/C type': '777',
            'DOW': 1234567,
            'Carrier': 'United Mainline'
        })
        
        flight = excel_row_to_flight(row, date(2025, 1, 15))
        
        assert flight is not None
        assert isinstance(flight, Flight)
        assert flight.flight_number == 'UA 384'
        assert flight.origin == 'DEN'
        assert flight.destination == 'HNL'
        assert flight.aircraft_type == '777'
        assert flight.departure_time.date() == date(2025, 1, 15)
        assert flight.arrival_time.date() == date(2025, 1, 15)
    
    def test_excel_row_to_flight_invalid_data(self):
        """Test excel_row_to_flight with invalid data."""
        # Missing origin
        row = pd.Series({
            'Org': None,
            'Des': 'HNL',
            'Flight #': 'UA 384',
            'Departs': 1205.0,
            'Arrives': 1633.0,
            'A/C type': '777',
        })
        
        flight = excel_row_to_flight(row, date(2025, 1, 15))
        assert flight is None
        
        # Invalid times
        row = pd.Series({
            'Org': 'DEN',
            'Des': 'HNL',
            'Flight #': 'UA 384',
            'Departs': None,
            'Arrives': 1633.0,
            'A/C type': '777',
        })
        
        flight = excel_row_to_flight(row, date(2025, 1, 15))
        assert flight is None
    
    def test_excel_row_to_flight_next_day_arrival(self):
        """Test excel_row_to_flight handles next-day arrivals."""
        row = pd.Series({
            'Org': 'DEN',
            'Des': 'HNL',
            'Flight #': 'UA 1924',
            'Departs': 2359.0,  # 23:59
            'Arrives': 519.0,   # 05:19 next day
            'A/C type': '777',
        })
        
        flight = excel_row_to_flight(row, date(2025, 1, 15))
        
        assert flight is not None
        assert flight.departure_time.date() == date(2025, 1, 15)
        assert flight.arrival_time.date() == date(2025, 1, 16)  # Next day
    
    def test_excel_row_to_flight_custom_columns(self):
        """Test excel_row_to_flight with custom column names."""
        row = pd.Series({
            'origin': 'DEN',
            'dest': 'HNL',
            'flight': 'UA 384',
            'dep': 1205.0,
            'arr': 1633.0,
            'ac': '777',
        })
        
        flight = excel_row_to_flight(
            row,
            date(2025, 1, 15),
            col_origin='origin',
            col_destination='dest',
            col_flight_number='flight',
            col_departs='dep',
            col_arrives='arr',
            col_aircraft_type='ac',
        )
        
        assert flight is not None
        assert flight.origin == 'DEN'
        assert flight.destination == 'HNL'

