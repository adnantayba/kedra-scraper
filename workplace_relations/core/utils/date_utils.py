"""
Date utility functions for the workplace relations scraper.
"""

from datetime import datetime, date
from typing import List, Tuple, Optional
from workplace_relations.config import settings


class DateUtils:
    """Utility class for date operations."""

    @staticmethod
    def parse_date(date_str: str, format_str: Optional[str] = None) -> Optional[date]:
        """
        Parse date string to date object.

        Args:
            date_str: Date string to parse
            format_str: Format string (uses settings default if None)

        Returns:
            Parsed date object or None if parsing fails
        """
        if not date_str:
            return None

        format_to_use = format_str or settings.DATE_FORMAT_INPUT

        try:
            return datetime.strptime(date_str, format_to_use).date()
        except ValueError:
            # Try alternative formats
            for alt_format in [settings.DATE_FORMAT_DISPLAY, "%Y-%m-%d", "%m-%d-%Y"]:
                try:
                    return datetime.strptime(date_str, alt_format).date()
                except ValueError:
                    continue
            return None

    @staticmethod
    def format_date(date_obj: date, format_str: Optional[str] = None) -> str:
        """
        Format date object to string.

        Args:
            date_obj: Date object to format
            format_str: Format string (uses settings default if None)

        Returns:
            Formatted date string
        """
        format_to_use = format_str or settings.DATE_FORMAT_DISPLAY
        return date_obj.strftime(format_to_use)

    @staticmethod
    def get_monthly_ranges(start_date: date, end_date: date) -> List[Tuple[date, date]]:
        """
        Generate monthly date ranges between start and end dates.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of (start, end) date tuples for each month
        """
        ranges = []
        current_start = start_date

        while current_start <= end_date:
            # Calculate end of current month
            if current_start.month == 12:
                current_end = date(current_start.year + 1, 1, 1) - date.resolution
            else:
                current_end = (
                    date(current_start.year, current_start.month + 1, 1)
                    - date.resolution
                )

            # Adjust to not exceed the overall end date
            if current_end > end_date:
                current_end = end_date

            ranges.append((current_start, current_end))

            # Move to next month
            if current_start.month == 12:
                current_start = date(current_start.year + 1, 1, 1)
            else:
                current_start = date(current_start.year, current_start.month + 1, 1)

        return ranges

    @staticmethod
    def get_partition_date(date_obj: date) -> str:
        """
        Get partition date string for storage organization.

        Args:
            date_obj: Date object

        Returns:
            Partition date string (YYYY-MM format)
        """
        return date_obj.strftime(settings.DATE_FORMAT_PARTITION)

    @staticmethod
    def is_valid_date_range(start_date: date, end_date: date) -> bool:
        """
        Validate date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            True if valid range, False otherwise
        """
        return start_date <= end_date

    @staticmethod
    def get_date_range_days(start_date: date, end_date: date) -> int:
        """
        Calculate number of days in date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of days
        """
        return (end_date - start_date).days + 1
