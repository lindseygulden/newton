""" Functions for manipulating time data and variables"""

# pylint: disable=broad-exception-caught
import datetime as dt
from calendar import isleap
from typing import List

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta


def days_in_month(month: int, year: int):
    """Returns number of days in a given month and year"""
    if not isinstance(month, int):
        raise ValueError(" Input arguments for month and year must be integers.")
    if month == 2:
        if isleap(year):
            return 29
        return 28
    if month in [4, 6, 9, 11]:
        return 30
    return 31


def convert_to_datetime(x, fmt: str = "%Y-%m-%d"):
    """Takes common date/time representations and returns them as a datetime object"""
    if isinstance(x, str):
        return dt.datetime.strptime(x, fmt)
    if isinstance(x, pd.Timestamp):
        return x.to_pydatetime()
    if isinstance(x, np.datetime64):
        return pd.Timestamp(x).to_pydatetime()
    if isinstance(x, dt.date):
        return dt.datetime.combine(x, dt.time(0, 0))
    if isinstance(x, dt.datetime):
        return x
    return None  # TODO raise error


def convert_multiple_formats_to_datetime(x, formats: List[str]):
    """Trys from a list of multiple string formats to convert a string to datetime"""
    for f in formats:
        try:
            return convert_to_datetime(x, fmt=f)
        except Exception:
            continue
    return x


def first_day_of_next_month(some_date: dt.datetime) -> dt.datetime:
    """Returns a datetime specifying the first day of the next month relative to some_date
    Args:
        some_date: a datetime object for any date in a month
    Returns:
        start_of_next_month: a datetime object for the first day of the month immediately following that of some_date
    """
    if not isinstance(some_date, dt.datetime):
        raise TypeError("Input argument some_date must be a python datetime object.")

    one_month_later = some_date + relativedelta(months=1)
    start_of_next_month = one_month_later - relativedelta(days=one_month_later.day - 1)
    return start_of_next_month


def convert_to_decimal_year(d: dt.datetime):
    """Converts a python datetime to a decimal year. Handles leap years. Does not treat sub-daily values.
    Args:
        d: the datetime (or date) object to be converted to decimal year
    Returns:
        float representing the decimal year for a given day.
    """
    if not isinstance(d, dt.datetime) and not isinstance(d, dt.date):
        raise ValueError(
            "convert_to_decimal_year requires input of a python datetime.datetime or datetime.date object."
        )
    days_in_this_year = 365 + int(isleap(d.year))
    day_of_year = d.timetuple().tm_yday - 1  # January 1 is day 0
    return d.year + (day_of_year / days_in_this_year)
