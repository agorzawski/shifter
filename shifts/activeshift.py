from shifts.models import Slot, Revision, Shift, ShiftID
from shifts.models import DATE_FORMAT_SLIM, DATE_FORMAT, SIMPLE_TIME
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

import phonenumbers
import datetime
from shifter.settings import NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES, DEFAULT_SHIFT_SLOT


def prepare_ShiftID(today, now, activeSlot, error=False):
    if error or activeSlot is None:
        return today.strftime(DATE_FORMAT_SLIM)+"Err"
    return today.strftime(DATE_FORMAT_SLIM) + activeSlot.id_code


def filter_active_slots(now, scheduled_shifts):
    return filter_for_hour(now, [shifter.slot for shifter in scheduled_shifts])


def filter_for_hour(now, slotsToConsider):
    slots = []
    for slot in slotsToConsider:
        if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                or slot.hour_start <= now < slot.hour_end:
            slots.append(slot)
    return slots


def prepare_active_crew(dayToGo=None,
                        slotToGo=None,
                        hourToGo=None,
                        fullUpdate=False,
                        useLDAP=True,):
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

    nowFull = datetime.datetime.combine(today, now)

    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(revision=revision) \
                                    .filter(Q(date=today) & Q(slot__op=True))
    # first find on EXACT time for OP slots
    slotsOPWithinScheduled = filter_active_slots(now, scheduled_shifts)
    # print('-> 1st OP SLOTS -> ', slotsOPWithinScheduled)

    # second find on EXACT time - NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES
    if len(slotsOPWithinScheduled) == 0:
        nowLater = (nowFull + datetime.timedelta(hours=NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES)).time()
        slotsOPWithinScheduled = filter_active_slots(nowLater, scheduled_shifts)
        if len(slotsOPWithinScheduled):
            now = nowLater
        # print('-> 2nd try (2h later) OP SLOTS -> ', slotsOPWithinScheduled)

    # retrigger for the search (in case now got updated)
    slots = filter_active_slots(now, scheduled_shifts)
    # print("-> SLOTS ALL ->", slots)

    # return if still no result found
    if len(slotsOPWithinScheduled) == 0:
        lastCompletedShiftBeforeTodayNow = Shift.objects \
            .filter(revision=revision) \
            .filter(Q(shiftID__isnull=False) & Q(shiftID__date_created__lte=nowFull)) \
            .order_by('-shiftID__date_created').first()
        # print("-> LAST SID found ->", lastCompletedShiftBeforeTodayNow.shiftID)
        lastShiftTeam = [s for s in Shift.objects.filter(shiftID=lastCompletedShiftBeforeTodayNow.shiftID)]
        return {'today': today,
                'now': now,
                'shiftID': lastCompletedShiftBeforeTodayNow.shiftID.label\
                if lastCompletedShiftBeforeTodayNow is not None\
                else prepare_ShiftID(today, now, None, error=True),
                'activeSlots': [lastShiftTeam[0].slot if len(lastShiftTeam) else None],
                'activeSlot': None,
                'currentTeam': lastShiftTeam
                }

    # for a final slot find the details
    slotToBeUsed = slotsOPWithinScheduled[0]
    # print('-> FOUND SLOT TO BE USED -> ', slotToBeUsed)
    # actual shift details finding based on the SLOT and date (today)
    sortedSlots = list(set(slots))
    sortedSlots.sort(key=lambda slotToSort: slotToSort.hour_end)
    activeSlots = []
    currentTeam = []
    for slot in sortedSlots:
        if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                or slot.hour_start <= now < slot.hour_end:
            for shifter in scheduled_shifts:
                if shifter.slot == slot:
                    activeSlots.append(slot)
                    currentTeam.append(shifter)
                    update_shifter_details(shifter, today, now, slotToBeUsed, ldap,
                                           fullUpdate=fullUpdate, useLDAP=useLDAP)

    return {'today': today,
            'now': now,
            'shiftID': prepare_ShiftID(today, now, slotToBeUsed),
            'activeSlots': set(activeSlots),
            'activeSlot': slotToBeUsed,
            'currentTeam': currentTeam}


def update_shifter_details(shifter, today, now, slotToBeUsed, ldap, fullUpdate=False, useLDAP=True):
    if fullUpdate or (shifter.member.email is None and shifter.member.mobile is None):
        if useLDAP:
            print('Fetching LDAP update for {}'.format(shifter.member))
        update_details_from_LDAP(shifter, ldap, useLDAP=useLDAP)
    if today < datetime.datetime.now():
        try:
            shiftID = ShiftID.objects.get(label=prepare_ShiftID(today, now, slotToBeUsed))
        except ObjectDoesNotExist:
            shiftID = ShiftID()
            shiftID.label = prepare_ShiftID(today, now, slotToBeUsed)
            shiftID.date_created = datetime.datetime.combine(today.date(), now)
            shiftID.save()
        if shifter.shiftID is None:
            shifter.shiftID = shiftID
        shifter.save()


def update_details_from_LDAP(shifterDuty, ldap, useLDAP=True):
    if shifterDuty.member.email is not None and shifterDuty.member.mobile is not None:
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


def prepare_for_JSON(activeShift):
    # TODO WIP send a slack webhook announcement to remind that this was called
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
