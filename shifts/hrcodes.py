from datetime import datetime, timedelta, time
from shifts.models import Shift, SIMPLE_DATE, SIMPLE_TIME, DATE_FORMAT


codes = {'OB1': (time(hour=18, minute=00, second=00),
                 time(hour=23, minute=59, second=59)), # evenigns
         'OB2': (time(hour=0, minute=00, second=00),
                 time(hour=7, minute=00, second=00)), # nights

         # 'OB3': (time(hour=7, minute=00, second=00),
         #         time(hour=23, minute=59, second=59)),  # WEs
         # 'OB4': (time(hour=7, minute=00, second=00),
         #         time(hour=23, minute=59, second=59))   # special holidays

         }


def get_code_counts(shift: Shift) -> dict:
    counts = {'OB1': 0, 'OB2': 0, 'OB3': 0, 'OB4': 0, }

    print('==========================')
    print(shift)
    # print(shift.start)
    # print(shift.end)
    duration = shift.end - shift.start

    notAWEOrHoliday = True
    # TODO if shift in special OB4 return + adjacent WE

    weekno = shift.start.weekday()
    if weekno >= 5:
        counts['OB3'] = duration.seconds//3600
        notAWEOrHoliday = False

    if notAWEOrHoliday:
        _check(shift, 'OB1', counts)
        _check(shift, 'OB2', counts) # TODO consider returning date -> codes dict in case shift spanning over two days

    print(counts)
    return counts


def _check(shift, code, counts):
    dateToCheck = shift.start
    while dateToCheck < shift.end:
        if codes[code][0] < (dateToCheck + timedelta(seconds=30)).time() < codes[code][1]:
            counts[code] += 1
        dateToCheck += timedelta(hours=1)