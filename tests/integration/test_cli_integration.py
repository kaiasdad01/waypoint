"""Integration tests for CLI interface."""

import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from status_optimizer.cli.main import main, parse_args, validate_args
from status_optimizer.cli.output import format_results
from status_optimizer.data.feeds.flight_feed import FlightFeed
from status_optimizer.domain.flight import Flight
from status_optimizer.domain.segment import Segment
from status_optimizer.domain.itinerary import Itinerary
from status_optimizer.search.search import ItinerarySearchResult


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""
    
    def test_parse_args_basic(self):
        """Test parsing basic arguments."""
        args = parse_args([
            "--origin", "EWR",
            "--date", "2025-01-15",
            "--legs", "4",
        ])

        assert args.origin == "EWR"
        assert args.date == datetime(2025, 1, 15).date()
        assert args.legs == 4
        assert args.min_layover == 45  # default
        assert args.max_elapsed == 48.0  # default
        assert args.max_results == 10  # default
    
    def test_parse_args_with_options(self):
        """Test parsing arguments with all options."""
        args = parse_args([
            "--origin", "EWR",
            "--date", "2025-01-15",
            "--legs", "4",
            "--min-layover", "60",
            "--max-elapsed", "24",
            "--max-results", "5",
            "--destination", "SFO",
        ])
        
        assert args.min_layover == 60
        assert args.max_elapsed == 24.0
        assert args.max_results == 5
        assert args.destination == "SFO"
    
    def test_parse_args_date_range(self):
        """Test parsing date range."""
        args = parse_args([
            "--origin", "EWR",
            "--date-range", "2025-01-15", "2025-01-17",
            "--legs", "4",
        ])

        assert args.date_range == [datetime(2025, 1, 15).date(), datetime(2025, 1, 17).date()]
        assert args.date is None
    
    def test_validate_args_valid(self):
        """Test validating valid arguments."""
        args = parse_args([
            "--origin", "EWR",
            "--date", "2025-01-15",
            "--legs", "4",
        ])
        validate_args(args)
        
        assert args.origin == "EWR"
        assert args.start_date.year == 2025
    
    def test_validate_args_invalid_airport(self):
        """Test validating invalid airport code."""
        # Argparse now validates airport codes during parsing
        with pytest.raises(SystemExit):
            parse_args([
                "--origin", "EW",
                "--date", "2025-01-15",
                "--legs", "4",
            ])
    
    def test_validate_args_invalid_date(self):
        """Test validating invalid date."""
        # Argparse now validates dates during parsing
        with pytest.raises(SystemExit):
            parse_args([
                "--origin", "EWR",
                "--date", "2025/01/15",
                "--legs", "4",
            ])
    
    def test_validate_args_invalid_legs(self):
        """Test validating invalid leg count."""
        # Argparse now validates legs during parsing
        with pytest.raises(SystemExit):
            parse_args([
                "--origin", "EWR",
                "--date", "2025-01-15",
                "--legs", "0",
            ])


class TestCLIIntegration:
    """Integration tests for CLI workflow."""
    
    @pytest.fixture
    def mock_flight_feed(self):
        """Create a mock FlightFeed."""
        feed = Mock(spec=FlightFeed)
        return feed
    
    @pytest.fixture
    def sample_flights(self):
        """Create sample flights for testing."""
        return [
            Flight(
                flight_number="UA100",
                origin="EWR",
                destination="ORD",
                departure_time=datetime(2025, 1, 15, 9, 0, 0),
                arrival_time=datetime(2025, 1, 15, 11, 0, 0),
                aircraft_type="737",
            ),
            Flight(
                flight_number="UA200",
                origin="ORD",
                destination="DEN",
                departure_time=datetime(2025, 1, 15, 12, 0, 0),
                arrival_time=datetime(2025, 1, 15, 14, 0, 0),
                aircraft_type="737",
            ),
            Flight(
                flight_number="UA300",
                origin="DEN",
                destination="SFO",
                departure_time=datetime(2025, 1, 15, 15, 0, 0),
                arrival_time=datetime(2025, 1, 15, 17, 0, 0),
                aircraft_type="737",
            ),
            Flight(
                flight_number="UA400",
                origin="SFO",
                destination="EWR",
                departure_time=datetime(2025, 1, 15, 18, 0, 0),
                arrival_time=datetime(2025, 1, 15, 23, 0, 0),
                aircraft_type="777",
            ),
        ]
    
    @pytest.fixture
    def sample_itinerary(self, sample_flights):
        """Create a sample itinerary."""
        segments = [
            Segment(flight=sample_flights[0], sequence_number=1),
            Segment(flight=sample_flights[1], sequence_number=2),
            Segment(flight=sample_flights[2], sequence_number=3),
            Segment(flight=sample_flights[3], sequence_number=4),
        ]
        return Itinerary(segments)
    
    @patch('status_optimizer.cli.main.ExcelFlightFeed')
    @patch('status_optimizer.cli.main.ItinerarySearch')
    def test_main_with_solutions(
        self,
        mock_search_class,
        mock_feed_class,
        mock_flight_feed,
        sample_itinerary,
    ):
        """Test main function with successful search results."""
        # Setup mocks
        mock_feed_instance = Mock()
        mock_feed_class.return_value = mock_feed_instance
        
        mock_search_instance = Mock()
        mock_search_class.return_value = mock_search_instance
        
        # Create search result with solutions
        result = ItinerarySearchResult(
            itineraries=[sample_itinerary],
            stats={},
            no_solution_reason=None,
        )
        mock_search_instance.search.return_value = result
        
        # Run main
        exit_code = main([
            "--origin", "EWR",
            "--date", "2025-01-15",
            "--legs", "4",
        ])
        
        # Verify
        assert exit_code == 0
        mock_feed_class.assert_called_once()
        mock_search_class.assert_called_once_with(mock_feed_instance)
        mock_search_instance.search.assert_called_once()
    
    @patch('status_optimizer.cli.main.ExcelFlightFeed')
    def test_main_file_not_found(self, mock_feed_class):
        """Test main function when Excel file is not found."""
        # Setup mock to raise FileNotFoundError
        mock_feed_class.side_effect = FileNotFoundError("File not found")
        
        # Run main
        exit_code = main([
            "--origin", "EWR",
            "--date", "2025-01-15",
            "--legs", "4",
        ])
        
        # Should return error code
        assert exit_code == 1
    
    @patch('status_optimizer.cli.main.ExcelFlightFeed')
    @patch('status_optimizer.cli.main.ItinerarySearch')
    def test_main_no_solutions(
        self,
        mock_search_class,
        mock_feed_class,
        mock_flight_feed,
    ):
        """Test main function when no solutions are found."""
        # Setup mocks
        mock_feed_instance = Mock()
        mock_feed_class.return_value = mock_feed_instance
        
        mock_search_instance = Mock()
        mock_search_class.return_value = mock_search_instance
        
        # Create search result with no solutions
        result = ItinerarySearchResult(
            itineraries=[],
            stats={},
            no_solution_reason="No flights available",
        )
        mock_search_instance.search.return_value = result
        
        # Run main
        exit_code = main([
            "--origin", "EWR",
            "--date", "2025-01-15",
            "--legs", "4",
        ])
        
        # Should return error code for no solutions
        assert exit_code == 1
    
    def test_main_invalid_args(self):
        """Test main function with invalid arguments."""
        # Argparse now raises SystemExit for invalid args
        with pytest.raises(SystemExit) as exc_info:
            main([
                "--origin", "EW",  # Invalid airport code
                "--date", "2025-01-15",
                "--legs", "4",
            ])

        # Argparse exits with code 2 for usage errors
        assert exc_info.value.code == 2

