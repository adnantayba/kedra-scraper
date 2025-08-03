# utils/daterange.py
import datetime
from dateutil.relativedelta import relativedelta


def daterange_monthly(start_date, end_date):
    """Yield (start, end) tuples for each month between two dates"""
    current = start_date.replace(day=1)
    while current < end_date:
        next_month = current + relativedelta(months=1)
        yield (current, min(next_month - datetime.timedelta(days=1), end_date))
        current = next_month
