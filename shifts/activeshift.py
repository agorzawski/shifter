from shifts.models import Slot, Revision, Shift, ShiftID
from shifts.models import DATE_FORMAT_SLIM, DATE_FORMAT, SIMPLE_TIME
from django.core.exceptions import ObjectDoesNotExist
import phonenumbers
import datetime
from shifter.settings import NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES


def prepareShiftId(today, activeSlot):
    shiftMap = {0: 'A', 1: 'B', 2: 'C', -1: 'X'}
    opSlots = Slot.objects.filter(op=True).order_by('hour_start')
    number = -1
    for idx, item in enumerate(opSlots):
        if item == activeSlot:
            number = idx
    print("\n ==> ", today, "|", today.hour, "|", activeSlot, "\n")
    # if today.hour < 6:
    #     today = today + datetime.timedelta(days=-1)
    return today.strftime(DATE_FORMAT_SLIM) + shiftMap[number]


def filter_active_slots(now, scheduled_shifts, slotsToConsider):
    slots = []
    for slot in slotsToConsider:
        if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                or slot.hour_start <= now < slot.hour_end:
            for shifter in scheduled_shifts:
                if shifter.slot == slot:
                    slots.append(slot)
    return slots


def prepare_active_crew(dayToGo=None, slotToGo=None, hourToGo=None, onlyOP=False, fullUpdate=False, useLDAP=True):
    ldap = None
    if fullUpdate and useLDAP:
        import members.directory as directory
        ldap = directory.LDAP()
    today = datetime.datetime.now()
    now = today.time()
    if dayToGo is not None and (slotToGo is not None or hourToGo is not None):
        today = datetime.datetime.strptime(dayToGo, DATE_FORMAT)
        if hourToGo is None and slotToGo is not None:
            now = Slot.objects.filter(abbreviation=slotToGo).first().hour_start
        if hourToGo is not None and slotToGo is None:
            now = datetime.datetime.strptime(hourToGo, SIMPLE_TIME).time()

    print("## ->", today)
    print("## ->", now)

    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(date=today).filter(revision=revision)
    slotsToConsider = Slot.objects.all() if not onlyOP else Slot.objects.filter(op=True)
    slotsOPWithinScheduled = filter_active_slots(now, scheduled_shifts, Slot.objects.filter(op=True))
    lastCompletedShiftBeforeTodayNow = Shift.objects.filter(revision=revision).filter(date__lte=today)\
        .filter(shiftID__isnull=False).order_by('shiftID').first()

    print("---->", lastCompletedShiftBeforeTodayNow)
    if len(slotsOPWithinScheduled) == 0:
        nowFull = datetime.datetime.combine(today, now)
        nowLater = (nowFull + datetime.timedelta(hours=NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES)).time()
        slotsOPWithinScheduled = filter_active_slots(nowLater, scheduled_shifts, Slot.objects.filter(op=True))
        if len(slotsOPWithinScheduled):
            now = nowLater
    slots = filter_active_slots(now, scheduled_shifts, slotsToConsider)

    print("---->", slots)

    if len(slotsOPWithinScheduled) == 0:
        slotsOPWithinScheduled = slots
    if len(slotsOPWithinScheduled) == 0:
        return {'today': today,
                'now': now,
                'shiftID': prepareShiftId(today, []),
                'activeSlots': [],
                'activeSlot': None,
                'currentTeam': []}
    slotToBeUsed = slotsOPWithinScheduled[0]

    def takeHourEnd(slotToSort):
        return slotToSort.hour_end

    def updateDetailsFromLDAP(shifterDuty, useLDAP=True):
        if shifterDuty.member.email is not None and shifterDuty.member.mobile is not None:
            # print(shifterDuty.member, " has all data locally")
            return None
        personal_data = []
        if useLDAP:
            personal_data = ldap.search(field='name', text=shifterDuty.member.last_name)
        if len(personal_data) == 0:
            return None
        one = list(personal_data.keys())[0]
        if len(personal_data) > 1:
            for oneK in personal_data.keys():
                if shifterDuty.member.last_name.lower() in oneK.lower() \
                        and shifterDuty.member.first_name.lower() in oneK.lower():
                    one = oneK
        shifterDuty.member.email = personal_data[one]['email']
        shifterDuty.member.mobile = 'N/A'
        try:
            pn = phonenumbers.parse(personal_data[one]['mobile'])
            fixed = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL).replace(" ", "")
            shifterDuty.member.mobile = fixed
            # for some reason SqLite allowed to save 16characters in 12 characters field
            # while postgres threw an exception, however this was used to format here not in the website... to be fixed
            shifterDuty.member.save()
        except Exception:
            pass
        if type(personal_data[one]['photo']) is not str:
            import base64
            shifterDuty.member.photo = base64.b64encode(personal_data[one]['photo']).decode("utf-8")
            shifterDuty.member.save()

    sortedSlots = list(set(slots))
    sortedSlots.sort(key=takeHourEnd)
    activeSlot = Slot.objects.first()
    activeSlots = []
    currentTeam = []
    for slot in sortedSlots:
        if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                or slot.hour_start <= now < slot.hour_end:
            for shifter in scheduled_shifts:
                if shifter.slot == slot:
                    activeSlot = slot
                    activeSlots.append(slot)
                    currentTeam.append(shifter)
                    if fullUpdate or (shifter.member.email is None and shifter.member.mobile is None):
                        if useLDAP:
                            print('Fetching LDAP update for {}'.format(shifter.member))
                        updateDetailsFromLDAP(shifter, useLDAP=useLDAP)
                    if today < datetime.datetime.now():
                        try:
                            shiftID = ShiftID.objects.get(label=prepareShiftId(today, slotToBeUsed))
                        except ObjectDoesNotExist:
                            shiftID = ShiftID()
                            shiftID.label = prepareShiftId(today, slotToBeUsed)
                            shiftID.date_created = datetime.datetime.combine(today.date(), now)
                            shiftID.save()
                        shifter.shiftID = shiftID
                        shifter.save()

    return {'today': today,
            'now': now,
            'shiftID': prepareShiftId(today, slotToBeUsed),
            'activeSlots': set(activeSlots),
            'activeSlot': slotToBeUsed,
            'currentTeam': currentTeam}


# def prepare_last_active_shift():
#     today = datetime.datetime.now()
#     now = today.time()
#     return {'today': today,
#             'now': now,
#             'shiftID': prepareShiftId(today, slotToBeUsed),
#             'activeSlots': set(activeSlots),
#             'activeSlot': slotToBeUsed,
#             'currentTeam': currentTeam}


def prepare_for_JSON(activeShift):
    # TODO WIP send a slack webhook announcement to remind that this was called
    # fieldsToUpdate = ['SL', 'OP', 'OCC', 'OC', 'OCE', 'OCPSS']
    fieldsToUpdate = ['SL', 'OP']
    dataToReturn = {'_datetime': activeShift['today'].strftime(DATE_FORMAT),
                    '_slot': 'outside active slots' if activeShift['activeSlot'] is None else activeShift[
                        'activeSlot'].abbreviation,
                    '_timeNow': datetime.datetime.now().strftime(SIMPLE_TIME),
                    '_timeRequested': activeShift['now'],
                    '_PVPrefix': 'NSO:Ops:',
                    'SID': activeShift['shiftID'],
                    }
    for one in fieldsToUpdate:
        dataToReturn[one] = "N/A"
    for one in fieldsToUpdate:
        for shifter in activeShift['currentTeam']:
            if one in shifter.member.role.abbreviation and shifter.role is None:  # no extra role in the same shift
                dataToReturn[one] = shifter.member.name
                dataToReturn[one + "Phone"] = shifter.member.mobile
                dataToReturn[one + "Email"] = shifter.member.email

    return dataToReturn
