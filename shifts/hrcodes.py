from datetime import date, timedelta, time
from shifts.models import Shift, SIMPLE_DATE, SIMPLE_TIME, DATE_FORMAT

codes = {'OB1': (time(hour=18, minute=00, second=00),
                 time(hour=23, minute=59, second=59)),  # evenings

         'OB2': (time(hour=0, minute=00, second=00),
                 time(hour=7, minute=00, second=00)),  # nights

         'NWH': (time(hour=7, minute=00, second=00),
                 time(hour=17, minute=59, second=59)),  # nights
         }

# TODO think of importing it as external table (not need to re-release it)
# TODO consider https://pypi.org/project/holidays/ when Sweden is included (not in Nov 2021)
public_holidays = [
    date(2021, 11, 6),

    # https://confluence.esss.lu.se/pages/viewpage.action?spaceKey=HR&title=Public+Holidays+and+additional+days+off+%282022%29+Sweden
    date(2022, 1, 6),
    date(2022, 1, 7),

    date(2022, 5, 26),
    date(2022, 5, 27),

    date(2022, 6, 6),
]

# The ones that are counted as OB4
# From 18:00 on Maundy Thursday and from 07:00 on Whitsun Eve, Midsummer Eve,
# Christmas Eve and New Year's Eve until midnight before the first weekday after the holiday.
public_holidays_special = [
    date(2021, 6, 25),
    date(2021, 12, 24),
    date(2021, 12, 25),
    date(2021, 12, 26),
    date(2021, 12, 31),

    date(2022, 1, 1),
    date(2022, 4, 15),
    date(2022, 4, 16),
    date(2022, 4, 17),
    date(2022, 4, 18),
    date(2022, 6, 24),
    date(2022, 6, 25),
    date(2022, 12, 24),
    date(2022, 12, 25),
    date(2022, 12, 26),
    date(2022, 12, 31),

    date(2022, 10, 30),
    date(2022, 10, 31),
    date(2022, 11, 1),
    date(2022, 11, 2),
    date(2022, 12, 9),
    date(2022, 12, 10),
    date(2022, 12, 11),
    date(2022, 12, 12),
]


def get_public_holidays(fmt=None):
    ph = public_holidays_special + public_holidays
    ph.sort()
    if fmt is None:
        return [d for d in ph]
    return [d.strftime(format=fmt) for d in ph]


def count_total(counts):
    countsReturn = {'OB1': 0, 'OB2': 0, 'OB3': 0, 'OB4': 0, 'NWH': 0}
    for oneDay in counts.keys():
        for oneCode in countsReturn.keys():
            countsReturn[oneCode] += counts.get(oneDay)[oneCode]
    return countsReturn


def get_date_code_counts(shifts):
    result = {}
    for shift in shifts:
        dayString = shift.start.date().strftime(SIMPLE_DATE)
        count = get_code_counts(shift)
        # TODO fix the 'double date' result (e.g. nights)
        result[dayString] = count
    return result


def _check_adjacent_WE(shiftDate, public_holiday):
    """
    To cover the holidays but also the adjacent WE (or long WE) around holidays
    """
    sDayNb = shiftDate.weekday()
    if shiftDate == public_holiday:
        return True
    if sDayNb >= 5 and abs(shiftDate - public_holiday) < timedelta(days=5):
        return True
    return False


def get_code_counts(shift: Shift) -> dict:
    counts = {'OB1': 0, 'OB2': 0, 'OB3': 0, 'OB4': 0, 'NWH': 0}
    duration = shift.end - shift.start
    notAWEOrHoliday = True
    for public_holiday in public_holidays_special:
        if _check_adjacent_WE(shift.date, public_holiday):
            counts['OB4'] = duration.seconds // 3600
            notAWEOrHoliday = False
    weekno = shift.start.weekday()
    if weekno >= 5 and notAWEOrHoliday:
        counts['OB3'] = duration.seconds // 3600
        notAWEOrHoliday = False

    if notAWEOrHoliday:
        _check(shift, 'NWH', counts)
        _check(shift, 'OB1', counts)
        _check(shift, 'OB2', counts)  # TODO consider returning date -> codes dict in case shift spanning over two days
    return counts


def _check(shift, code, counts):
    dateToCheck = shift.start
    while dateToCheck < shift.end:
        if codes[code][0] < (dateToCheck + timedelta(seconds=30)).time() < codes[code][1]:
            if counts[code] < 8:
                counts[code] += 1
        dateToCheck += timedelta(hours=1)
