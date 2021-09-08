from datetime import datetime, timedelta, time
from shifts.models import Shift, SIMPLE_DATE, SIMPLE_TIME, DATE_FORMAT

codes = {'OB1': (time(hour=18, minute=00, second=00),
                 time(hour=23, minute=59, second=59)),  # evenings
         'OB2': (time(hour=0, minute=00, second=00),
                 time(hour=7, minute=00, second=00)),  # nights

         # 'OB3': (time(hour=7, minute=00, second=00),
         #         time(hour=23, minute=59, second=59)),  # WEs
         # 'OB4': (time(hour=7, minute=00, second=00),
         #         time(hour=23, minute=59, second=59)),   # special holidays

         'NWH': (time(hour=7, minute=00, second=00),
                 time(hour=17, minute=59, second=59)),  # nights
         }


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


def get_code_counts(shift: Shift) -> dict:
    counts = {'OB1': 0, 'OB2': 0, 'OB3': 0, 'OB4': 0, 'NWH': 0}
    duration = shift.end - shift.start
    notAWEOrHoliday = True
    # TODO if shift in special OB4 return + adjacent WE

    weekno = shift.start.weekday()
    if weekno >= 5:
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
