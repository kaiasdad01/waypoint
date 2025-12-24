"""Output formatting for CLI results."""

from collections import defaultdict
from datetime import date, datetime, timedelta

from status_optimizer.domain.itinerary import Itinerary
from status_optimizer.domain.segment import Segment
from status_optimizer.search.search import ItinerarySearchResult


def format_time_delta(td: timedelta) -> str:
    """Format timedelta as human-readable string.
    
    Args:
        td: Timedelta to format
        
    Returns:
        Formatted string like "2h 30m" or "45m" if < 1 hour
    """
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"
    return f"{minutes}m"


def format_datetime(dt: datetime) -> str:
    """Format datetime as readable string.
    
    Args:
        dt: Datetime to format (assumed UTC)
        
    Returns:
        Formatted string like "2025-01-15 08:00 UTC"
    """
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def format_segment(segment: Segment) -> str:
    """Format a single segment.
    
    Args:
        segment: Segment to format
        
    Returns:
        Formatted string for the segment
    """
    flight = segment.flight
    dep_time = flight.departure_time.strftime("%H:%M")
    arr_time = flight.arrival_time.strftime("%H:%M")
    duration = format_time_delta(flight.duration)
    
    return (
        f"  Leg {segment.sequence_number}: {flight.flight_number}  "
        f"{flight.origin} → {flight.destination}  "
        f"({dep_time} → {arr_time}, {duration})"
    )


def format_itinerary(itinerary: Itinerary, rank: int, show_date: bool = False) -> str:
    """Format a single itinerary as readable text.
    
    Args:
        itinerary: Itinerary to format
        rank: Rank number (1-indexed)
        show_date: Whether to show the departure date in the header
        
    Returns:
        Formatted string for the itinerary
    """
    lines = []
    
    # Header
    elapsed_str = format_time_delta(itinerary.total_elapsed_time)
    lines.append(f"\n{'='*80}")
    if show_date:
        departure_date = itinerary.departure_time.date()
        lines.append(f"Itinerary {rank} - {departure_date} - Total Time: {elapsed_str}")
    else:
        lines.append(f"Itinerary {rank} - Total Time: {elapsed_str}")
    lines.append(f"{'='*80}")
    
    # Segments with layovers
    layover_times = itinerary.get_layover_times()
    for i, segment in enumerate(itinerary.segments):
        segment_str = format_segment(segment)
        lines.append(segment_str)
        
        # Add layover info if not last segment
        if i < len(itinerary.segments) - 1:
            layover_time_str = format_time_delta(layover_times[i])
            connecting_airport = segment.flight.destination
            lines.append(f"    → Layover: {layover_time_str} at {connecting_airport}")
    
    # Summary
    lines.append("")
    lines.append(f"Summary: {format_time_delta(itinerary.total_elapsed_time)} total | "
                 f"{format_time_delta(itinerary.total_airtime)} airtime | "
                 f"{format_time_delta(itinerary.total_layover_time)} layovers")
    
    return "\n".join(lines)


def format_no_solutions(reason: str) -> str:
    """Format "no solutions" message.
    
    Args:
        reason: Reason why no solutions were found
        
    Returns:
        Formatted error message
    """
    lines = [
        "No feasible itineraries found.",
        "",
        f"Reason: {reason}",
        "",
        "Suggestions:",
        "  • Try relaxing constraints (e.g., increase --max-elapsed)",
        "  • Try a different date or date range",
        "  • Try a different origin airport",
        "  • Try adjusting --min-layover to allow tighter connections",
    ]
    return "\n".join(lines)


def format_results(result: ItinerarySearchResult, max_results: int) -> str:
    """Format search results as readable text, grouped by departure date.
    
    Results are grouped by the date of the first flight departure, ensuring
    that comparisons are made within the same day. This prevents showing
    nearly identical itineraries that differ only by the day they occur.
    
    Args:
        result: ItinerarySearchResult from search
        max_results: Maximum number of results to display per day
        
    Returns:
        Formatted string with all results grouped by date
    """
    if not result.found_solutions:
        reason = result.no_solution_reason or "Unknown reason"
        return format_no_solutions(reason)
    
    # Group itineraries by departure date (date of first flight)
    itineraries_by_date: dict[date, list[Itinerary]] = defaultdict(list)
    for itinerary in result.itineraries:
        departure_date = itinerary.departure_time.date()
        itineraries_by_date[departure_date].append(itinerary)
    
    # Sort each day's itineraries by elapsed time (best first)
    for date_key in itineraries_by_date:
        itineraries_by_date[date_key].sort(key=lambda it: it.total_elapsed_time)
    
    # Sort dates chronologically
    sorted_dates = sorted(itineraries_by_date.keys())
    
    lines = []
    
    # Header
    total_found = len(result.itineraries)
    lines.append("")
    if total_found > max_results * len(sorted_dates):
        lines.append(f"Found {total_found} itineraries (showing top {max_results} per day):")
    else:
        lines.append(f"Found {total_found} itinerary{'ies' if total_found != 1 else ''}:")
    lines.append("")
    
    # Format each day's results
    all_display_itineraries = []
    for day_date in sorted_dates:
        day_itineraries = itineraries_by_date[day_date]
        # Limit to max_results per day
        display_count = min(len(day_itineraries), max_results)
        display_itineraries = day_itineraries[:display_count]
        all_display_itineraries.extend(display_itineraries)
    
    # Format each itinerary
    for i, itinerary in enumerate(all_display_itineraries):
        # Add day header if we have multiple days and this is the first itinerary of a day
        if len(sorted_dates) > 1:
            itinerary_date = itinerary.departure_time.date()
            # Check if this is the first itinerary for this date
            prev_itineraries_same_date = sum(
                1 for it in all_display_itineraries[:i]
                if it.departure_time.date() == itinerary_date
            )
            if prev_itineraries_same_date == 0:
                # First itinerary for this date - add day header
                day_itineraries = itineraries_by_date[itinerary_date]
                display_count = min(len(day_itineraries), max_results)
                lines.append(f"\n{'#'*80}")
                lines.append(f"# Departure Date: {itinerary_date} ({len(day_itineraries)} itineraries found, showing top {display_count})")
                lines.append(f"{'#'*80}")
        
        itinerary_str = format_itinerary(itinerary, i + 1, show_date=len(sorted_dates) > 1)
        lines.append(itinerary_str)
        if i < len(all_display_itineraries) - 1:
            lines.append("")  # Blank line between itineraries
    
    return "\n".join(lines)

