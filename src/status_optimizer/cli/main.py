"""Command-line interface for status optimizer."""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional

from status_optimizer.config import config
from status_optimizer.constraints import (
    Constraint,
    MaxElapsedConstraint,
    MinLayoverConstraint,
    LegCountConstraint,
    ReturnToOriginConstraint,
    TimeWindowConstraint,
)
from status_optimizer.data.providers.excel_flight_feed import ExcelFlightFeed
from status_optimizer.search.search import ItinerarySearch
from status_optimizer.cli.output import format_results

logger = logging.getLogger(__name__)


def validate_airport_code(code: str) -> str:
    """Validate and normalize airport IATA code (3 letters)."""
    code = code.upper().strip()
    if not code.isalpha() or len(code) != 3:
        raise argparse.ArgumentTypeError(f"Invalid airport code: {code}. Must be 3 letters (e.g., EWR)")
    return code


def parse_date_arg(date_str: str) -> date:
    """Parse date in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date: {date_str}. Use YYYY-MM-DD (e.g., 2025-01-15)")


def positive_int(value: str) -> int:
    """Validate positive integer."""
    try:
        ivalue = int(value)
        if ivalue < 1:
            raise argparse.ArgumentTypeError(f"Must be >= 1, got {ivalue}")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Must be an integer, got {value}")


def non_negative_int(value: str) -> int:
    """Validate non-negative integer."""
    try:
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError(f"Must be >= 0, got {ivalue}")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Must be an integer, got {value}")


def positive_float(value: str) -> float:
    """Validate positive float."""
    try:
        fvalue = float(value)
        if fvalue <= 0:
            raise argparse.ArgumentTypeError(f"Must be > 0, got {fvalue}")
        return fvalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Must be a number, got {value}")


def build_constraints(
    origin: str,
    destination: Optional[str],
    legs: int,
    min_layover_minutes: int,
    max_elapsed_hours: float,
    start_time: datetime,
    end_time: datetime,
) -> List[Constraint]:
    """Build constraint list from CLI arguments.
    
    Args:
        origin: Origin airport code
        destination: Destination airport code (None if return-to-origin)
        legs: Exact number of legs required
        min_layover_minutes: Minimum layover time in minutes
        max_elapsed_hours: Maximum elapsed time in hours
        start_time: Search start time (UTC)
        end_time: Search end time (UTC)
        
    Returns:
        List of Constraint objects
    """
    constraints: List[Constraint] = []
    
    # Leg count constraint
    constraints.append(LegCountConstraint(exact=legs))
    
    # Return-to-origin constraint
    if destination is None or destination == origin:
        constraints.append(ReturnToOriginConstraint(required=True))
    
    # Minimum layover constraint
    constraints.append(MinLayoverConstraint(min_minutes=min_layover_minutes))
    
    # Maximum elapsed time constraint
    constraints.append(MaxElapsedConstraint(max_hours=max_elapsed_hours))

    # Note: TimeWindowConstraint is NOT added here because the search already
    # enforces the time window via the time_window_end parameter.
    # Adding it here causes issues when the search adjusts start_time to the
    # first available flight.
    
    return constraints


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: Optional list of arguments (defaults to sys.argv)
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="United MileagePlus status optimizer - Find optimal flight itineraries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage: 4-leg loop from EWR on Jan 15, 2025
  python -m status_optimizer.cli.main --origin EWR --date 2025-01-15 --legs 4

  # With custom constraints
  python -m status_optimizer.cli.main \\
    --origin EWR \\
    --date 2025-01-15 \\
    --legs 4 \\
    --min-layover 60 \\
    --max-elapsed 24 \\
    --max-results 5

  # Date range
  python -m status_optimizer.cli.main \\
    --origin EWR \\
    --date-range 2025-01-15 2025-01-17 \\
    --legs 4
        """,
    )
    
    # Required arguments
    parser.add_argument(
        "--origin",
        type=validate_airport_code,
        required=True,
        help="Origin airport IATA code (e.g., EWR)",
    )

    # Date arguments (mutually exclusive)
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--date",
        type=parse_date_arg,
        help="Single date in YYYY-MM-DD format",
    )
    date_group.add_argument(
        "--date-range",
        nargs=2,
        type=parse_date_arg,
        metavar=("START", "END"),
        help="Date range: START END (both in YYYY-MM-DD format)",
    )

    parser.add_argument(
        "--legs",
        type=positive_int,
        required=True,
        help="Exact number of flight legs (segments)",
    )

    # Optional arguments
    parser.add_argument(
        "--min-layover",
        type=non_negative_int,
        default=config.cli.min_layover_minutes,
        help=f"Minimum layover time in minutes (default: {config.cli.min_layover_minutes})",
    )

    parser.add_argument(
        "--max-elapsed",
        type=positive_float,
        default=config.cli.max_elapsed_hours,
        help=f"Maximum total elapsed time in hours (default: {config.cli.max_elapsed_hours})",
    )

    parser.add_argument(
        "--max-results",
        type=positive_int,
        default=config.cli.max_results,
        help=f"Maximum number of results to display (default: {config.cli.max_results})",
    )

    parser.add_argument(
        "--destination",
        type=validate_airport_code,
        default=None,
        help="Destination airport IATA code (defaults to same as origin for loops)",
    )
    
    parser.add_argument(
        "--excel-path",
        type=str,
        default=config.cli.excel_path,
        help=f"Path to Excel file (default: {config.cli.excel_path})",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    return parser.parse_args(args)


def validate_args(args: argparse.Namespace) -> None:
    """Process and validate date arguments."""
    # Set start_date from either --date or --date-range
    if args.date:
        args.start_date = args.date
    elif args.date_range:
        start_date, end_date = args.date_range
        if start_date > end_date:
            raise ValueError(f"Start date {start_date} must be before end date {end_date}")
        args.start_date = start_date
    else:
        raise ValueError("Either --date or --date-range must be provided")


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point.
    
    Args:
        args: Optional command-line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse arguments
        parsed_args = parse_args(args)
        
        # Configure logging
        log_level = logging.DEBUG if parsed_args.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        
        # Validate arguments
        validate_args(parsed_args)
        
        # Convert date to datetime (start of day in UTC)
        start_time = datetime.combine(parsed_args.start_date, datetime.min.time())
        
        # For 4+ leg searches, increase default max_elapsed if user didn't specify
        # Multi-leg loops often need more time
        effective_max_elapsed = parsed_args.max_elapsed
        if parsed_args.legs >= 4 and parsed_args.max_elapsed == config.cli.max_elapsed_hours:
            effective_max_elapsed = 72.0  # 3 days for 4+ leg searches
            logger.info(
                f"Using extended time window for {parsed_args.legs}-leg search: "
                f"{effective_max_elapsed} hours (default for multi-leg loops)"
            )
        
        end_time = start_time + timedelta(hours=effective_max_elapsed)
        
        # Build constraints
        constraints = build_constraints(
            origin=parsed_args.origin,
            destination=parsed_args.destination,
            legs=parsed_args.legs,
            min_layover_minutes=parsed_args.min_layover,
            max_elapsed_hours=effective_max_elapsed,
            start_time=start_time,
            end_time=end_time,
        )
        
        # Create flight feed
        logger.info("Initializing flight feed...")
        try:
            flight_feed = ExcelFlightFeed(excel_path=parsed_args.excel_path)
        except FileNotFoundError as e:
            print(f"Error: Excel file not found: {e}", file=sys.stderr)
            print(f"Expected location: {Path('data/united-routes.xlsx').absolute()}", file=sys.stderr)
            return 1
        
        # Create search instance
        search = ItinerarySearch(flight_feed)
        
        # Run search
        logger.info(f"Searching for {parsed_args.legs}-leg itinerary from {parsed_args.origin}...")
        result = search.search(
            origin=parsed_args.origin,
            start_time=start_time,
            target_legs=parsed_args.legs,
            constraints=constraints,
            min_layover=timedelta(minutes=parsed_args.min_layover),
            max_elapsed=timedelta(hours=effective_max_elapsed),
            beam_width=config.search.beam_width,
            max_results=parsed_args.max_results,
        )
        
        # Format and display results
        output = format_results(result, max_results=parsed_args.max_results)
        print(output)
        
        return 0 if result.found_solutions else 1
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"Error: {e}", file=sys.stderr)
        if parsed_args.verbose if 'parsed_args' in locals() else False:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

