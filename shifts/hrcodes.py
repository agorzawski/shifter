from datetime import date, timedelta, time, datetime
from shifts.models import Shift, SIMPLE_DATE, SIMPLE_TIME, DATE_FORMAT

codes = {'OB1': (time(hour=18, minute=00, second=00),
                 time(hour=23, minute=59, second=59)),  # evenings

         'OB2': (time(hour=0, minute=00, second=00),
                 time(hour=7, minute=00, second=00)),  # nights

         'NWH': (time(hour=7, minute=00, second=00),
                 time(hour=17, minute=59, second=59)),  # nights
         }

# The ones that are counted as OB3 (as weekends)
# TODO think of importing it as external table (not need to re-release it)
# TODO consider https://pypi.org/project/holidays/ when Sweden is included (not in Nov 2021)
red_days = [
    date(2021, 11, 6),

    # https://confluence.esss.lu.se/pages/viewpage.action?spaceKey=HR&title=Public+Holidays+and+additional+days+off+%282022%29+Sweden
    date(2022, 1, 6),
    date(2022, 1, 7),
    date(2022, 5, 26),
    date(2022, 5, 27),
    date(2022, 6, 6),

    # https://confluence.esss.lu.se/pages/viewpage.action?spaceKey=HR&title=Public+holidays+and+additional+days+off+%282023%29+Sweden
    date(2023, 5, 1),
    date(2023, 5, 18),
    date(2023, 5, 19),
    date(2023, 6, 5),
    date(2023, 6, 6),

    # https://confluence.esss.lu.se/display/HR/Public+holidays+and+additional+days+off+%282024%29+Sweden
    date(2024, 5, 1),
    date(2024, 5, 9),
    date(2024, 5, 10),
    date(2024, 12, 31),
]

reduced_days = [
    date(2021, 1, 5),
    date(2021, 4, 1),
    date(2021, 4, 30),
    date(2021, 11, 5),

    date(2022, 1, 5),
    date(2022, 4, 14),
    date(2022, 11, 4),

    # these days are reduced by 3h, and start the 'WE' OB code as of 14:00
    # https://confluence.esss.lu.se/pages/viewpage.action?spaceKey=HR&title=Public+holidays+and+additional+days+off+%282023%29+Sweden
    date(2023, 1, 5),
    date(2023, 4, 6),
    date(2023, 11, 3),

    # https://confluence.esss.lu.se/display/HR/Public+holidays+and+additional+days+off+%282024%29+Sweden
    date(2024, 1, 5),
    date(2024, 3, 28),
    date(2024, 4, 30),
    date(2024, 11, 1),
]

# The ones that are counted as OB4
# From 18:00 on Maundy Thursday and from 07:00 on Whitsun Eve, Midsummer Eve,
# Christmas Eve and New Year's Eve until midnight before the first weekday after the holiday.
# the first group is to cover the 'special' earlier 18:00 in Maundy Thu
public_holidays_special_exception = [
    (date(2022, 4, 14), time(18, 0, 0)),
    (date(2023, 4, 6), time(18, 0, 0))
]
public_holidays_special = [
    date(2021, 6, 25),
    date(2021, 12, 24),
    date(2021, 12, 25),
    date(2021, 12, 26),
    date(2021, 12, 31),

# https://confluence.esss.lu.se/pages/viewpage.action?spaceKey=HR&title=Public+Holidays+and+additional+days+off+%282022%29+Sweden
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

    # https://confluence.esss.lu.se/pages/viewpage.action?spaceKey=HR&title=Public+holidays+and+additional+days+off+%282023%29+Sweden
    date(2023, 1, 1),
    # date(2023, 4, 9), reduced 3
    date(2023, 4, 7),
    date(2023, 4, 8),
    date(2023, 4, 9),
    date(2023, 4, 10),
    date(2023, 6, 23),
    date(2023, 12, 25),
    date(2023, 12, 26),

    # https://confluence.esss.lu.se/display/HR/Public+holidays+and+additional+days+off+%282024%29+Sweden
    date(2024, 1, 1),
    date(2024, 3, 29),
    date(2024, 4, 1),
    date(2024, 6, 6),
    date(2024, 6, 7),
    date(2024, 6, 21),
    date(2024, 12, 24),
    date(2024, 12, 25),
    date(2024, 12, 26),
]


def get_public_holidays(fmt=None):
    ph = public_holidays_special + red_days
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


def _check_if_date_or_adjacent_WE(shiftDate: date, public_holiday: date):
    """
    To cover the holidays but also the adjacent WE (or long WE) around holidays
    """
    sDayNb = shiftDate.weekday()
    if shiftDate == public_holiday:
        return True
    if sDayNb >= 5 and abs(shiftDate - public_holiday) < timedelta(days=3):
        return True
    return False


def get_code_counts(shift: Shift, verbose=False) -> dict:
    counts = {'OB1': 0, 'OB2': 0, 'OB3': 0, 'OB4': 0, 'NWH': 0}
    duration = shift.end - shift.start
    if verbose:
        print("duration: ", duration)
    notAWEOrHoliday = True
    for ph in public_holidays_special:  # OB4 special holidays: Easter, Xmas, New Years and Midsommar
        if _check_if_date_or_adjacent_WE(shift.date, ph):
            counts['OB4'] = duration.seconds // 3600
            notAWEOrHoliday = False
    if verbose:
        print("public holiday spec: ", counts)
    for ph in public_holidays_special_exception:  # OB4 for few hours in special case (refer to the link above)
        breakDown = datetime.combine(ph[0], ph[1])
        if abs(shift.end - breakDown) > timedelta(hours=13) or shift.end < breakDown:
            continue
        if verbose:
            print("public special OB4 ", shift, breakDown, (shift.end - breakDown))
        if shift.start > breakDown:
            counts['OB4'] = duration.seconds // 3600
        else:
            beforeBD = breakDown - shift.start
            overBD = shift.end - breakDown
            counts['OB4'] = beforeBD.seconds // 3600
            counts['NWH'] = overBD.seconds // 3600
            if verbose:
                print(beforeBD.seconds // 3600, overBD.seconds//3600)
        notAWEOrHoliday = False
    if verbose:
        print("public_holidays_special_exception OB4: ", counts)
    for rd in red_days:  # OB3 - regular red days
        if _check_if_date_or_adjacent_WE(shift.date, rd):
            counts['OB3'] = duration.seconds // 3600
            notAWEOrHoliday = False
    if verbose:
        print("red_days OB3: ", counts)
    for rd in reduced_days:  # OB3 as of 14:00, but not for exception days (that also happen to be reduced hours)
        if rd in [d[0] for d in public_holidays_special_exception]:
            continue
        if _check_if_date_or_adjacent_WE(shift.date, rd) and \
                shift.slot.abbreviation == 'NWH':
            # print(rd)
            # print(shift.date)
            counts['NWH'] = 5
            notAWEOrHoliday = False
            continue
        # Temporary removed the OB3 for the reduced day adjacent to the WE. Issue#50
        # if _check_if_date_or_adjacent_WE(shift.date, rd) and \
        #         shift.start >= datetime.combine(rd, time(14, 0)) and \
        #         notAWEOrHoliday:
        #     counts['OB3'] = duration.seconds // 3600
        #     notAWEOrHoliday = False
    if verbose:
        print("reduced days NWH: ", counts)
    weekno = shift.start.weekday()
    if weekno >= 5 and notAWEOrHoliday:
        counts['OB3'] = duration.seconds // 3600
        notAWEOrHoliday = False
    if verbose:
        print("Weekends OB3: ", counts)
    if notAWEOrHoliday:
        _check(shift, 'NWH', counts)
        _check(shift, 'OB1', counts)
        _check(shift, 'OB2', counts)  # TODO consider returning date -> codes dict in case shift spanning over two days
    if verbose:
        print(counts)
    return counts


def _check(shift, code, counts):
    dateToCheck = shift.start
    while dateToCheck < shift.end:
        if codes[code][0] < (dateToCheck + timedelta(seconds=30)).time() < codes[code][1]:
            if counts[code] < 8:
                counts[code] += 1
        dateToCheck += timedelta(hours=1)
