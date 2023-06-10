from shifter.settings import DEFAULT_SHIFT_SLOT
from shifts.models import DATE_FORMAT_FULL, Shift
from datetime import timedelta
import datetime


def get_hours_break(laterShift: Shift, earlierShift: Shift):
    breakTotal = laterShift.start - earlierShift.end
    return breakTotal.seconds // 3600 + breakTotal.days * 24


def find_daily_rest_time_violation(scheduled_shifts, minimum_rest_time_in_hours=11) -> list:
    """
    Returns the tuple of pairs of shift that violate the rule for the minimum break
    """
    toReturn = []
    ss = list(scheduled_shifts)
    ss.sort(key=lambda s: s.start)
    for earlier, later in zip(ss[:-1], ss[1:]):
        if DEFAULT_SHIFT_SLOT in later.slot.abbreviation:
            continue
        if later.start - earlier.end < timedelta(hours=minimum_rest_time_in_hours):
            toReturn.append((earlier, later))
    return toReturn


def find_weekly_rest_time_violation(scheduled_shifts, minimum_rest_time=36) -> list:
    """
    Returns the tuple of pairs of shift that violate the rule for the minimum break
    """
    streak = []
    toReturn = []
    ss = list(scheduled_shifts)
    ss.sort(key=lambda s: s.start)
    for i, one in enumerate(ss[:-1]):
        nextShift = ss[i+1]
        if nextShift.start - one.end < timedelta(hours=minimum_rest_time):
            streak.append(one)
        else:
            streak = []
        if len(streak) >= 6:
            if nextShift.start - one.end < timedelta(hours=minimum_rest_time):
                streak.append(ss[i+1])
                toReturn.append(streak)
                streak = []
            else:
                streak = []

    # IDEA nb1 find any consecutive days, count <7 and see what is the break to the next one

    return toReturn


def find_working_hours(scheduled_shifts, startDate=None, endDate=None) -> dict:

    tempDates = {}
    for one in scheduled_shifts:
        # print(one)
        if tempDates.get(one.date, None) is None:
            tempDates[one.date] = {'start': None, 'end': None}
        dateIn = tempDates[one.date]
        if dateIn.get('start', None) is None:
            dateIn['start'] = one.slot.hour_start
            dateIn['end'] = one.slot.hour_end
        if dateIn.get('start') > one.slot.hour_start:
            dateIn['start'] = one.slot.hour_start
        if one.slot.hour_end > dateIn.get('end'):
            dateIn['end'] = one.slot.hour_end
        if one.slot.hour_end >= dateIn.get('end') and dateIn.get('start') > one.slot.hour_end:
            dateIn['start'] = datetime.time(0, 0, 0)
            # TODO fix the nights
        if dateIn.get('start') > one.slot.hour_end:
            dateIn['end'] = datetime.time(23, 59, 59)
    slots = []
    totalWorkingTimeInH = timedelta(hours=0)
    for k, v in tempDates.items():
        hourInADayStart = datetime.datetime.combine(k, v['start'])
        hourInADayEnd = datetime.datetime.combine(k, v['end'])
        slots.append((hourInADayStart.strftime(DATE_FORMAT_FULL), hourInADayEnd.strftime(DATE_FORMAT_FULL)))
        totalWorkingTimeInH += (hourInADayEnd - hourInADayStart)

    return {'startDate':  startDate.strftime(DATE_FORMAT_FULL) if startDate is not None else None,
            'endDate': endDate.strftime(DATE_FORMAT_FULL) if endDate is not None else None,
            'totalWorkingH': totalWorkingTimeInH.days * 24 + totalWorkingTimeInH.seconds // 3600,
            'workingSlots': slots,
            }
