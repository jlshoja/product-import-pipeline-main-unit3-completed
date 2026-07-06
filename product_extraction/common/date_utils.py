"""
Shared date helpers.

Unit 7 - Shared Utility Consolidation
"""

from datetime import datetime


def gregorian_to_jalali(g_y, g_m, g_d):
    """Convert a Gregorian date to a Jalali date tuple."""
    g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]

    gy = g_y - 1600
    gm = g_m - 1
    gd = g_d - 1

    g_day_no = 365 * gy + ((gy + 3) // 4) - ((gy + 99) // 100) + ((gy + 399) // 400)

    for i in range(gm):
        g_day_no += g_days_in_month[i]

    if gm > 1 and ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)):
        g_day_no += 1

    g_day_no += gd
    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    j_month = 0
    for i in range(12):
        days_this_month = j_days_in_month[i]
        if i == 11 and j_day_no >= 365:
            days_this_month = 30
        if j_day_no < days_this_month:
            break
        j_day_no -= days_this_month
        j_month += 1

    return jy, j_month + 1, j_day_no + 1


def get_persian_date(date=None):
    """Return a Jalali date string in YYYY/MM/DD format."""
    if date is None:
        date = datetime.now()

    j_y, j_m, j_d = gregorian_to_jalali(date.year, date.month, date.day)
    return f"{j_y:04d}/{j_m:02d}/{j_d:02d}"
