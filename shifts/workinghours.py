from shifter.settings import DEFAULT_SHIFT_SLOT
from datetime import timedelta


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
        if ss[i+1].start - one.end < timedelta(hours=24):
            streak.append(one)
        else:
            streak = []
        if len(streak) >= 6:
            if ss[i+1].start - one.end < timedelta(hours=minimum_rest_time):
                toReturn.append(streak)
            else:
                streak = []

    # IDEA nb1 find any consecutive days, count <7 and see what is the break to the next one

    return toReturn
