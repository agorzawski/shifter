from shifts.models import Slot, Revision, Shift, ShiftID
from shifts.models import DATE_FORMAT_SLIM, DATE_FORMAT, SIMPLE_TIME
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

import phonenumbers
import datetime
from shifter.settings import NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES, DEFAULT_SHIFT_SLOT, DEFAULT_SHIFTER_TO_JSON, \
    DEFAULT_SPECIAL_SHIFT_ROLES


def prepare_ShiftID(today, now, activeSlot, error=False):
    if error or activeSlot is None:
        return today.strftime(DATE_FORMAT_SLIM) + "Err"
    return today.strftime(DATE_FORMAT_SLIM) + activeSlot.id_code


def filter_active_slots(now, scheduled_shifts):
    scheduled_shifts_slots_ids = [i['slot'] for i in scheduled_shifts.values('slot').distinct()]
    default_slot = Slot.objects.get(abbreviation=DEFAULT_SHIFT_SLOT)
    if default_slot.id in scheduled_shifts_slots_ids and len(scheduled_shifts_slots_ids) > 1:
        scheduled_shifts_slots_ids.remove(default_slot.id)
    consider = [shifter.slot for shifter in scheduled_shifts if shifter.slot.id in scheduled_shifts_slots_ids]
    slots = []
    for slot in consider:
        if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                or slot.hour_start <= now < slot.hour_end:
            slots.append(slot)
    slots.sort(key=lambda s: s.hour_start, reverse=True)
    return slots


def prepare_active_crew(dayToGo=None,
                        slotToGo=None,
                        hourToGo=None,
                        fullUpdate=False,
                        useLDAP=True,
                        verbose=False):
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
    if verbose:
        print("\n =======\n Searching for ", nowFull)
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(revision=revision) \
        .filter(Q(date=today) & Q(slot__op=True))

    if Slot.objects.all().order_by("hour_start").first().hour_start > now:
        todayX = today + datetime.timedelta(days=-1)
        scheduled_shifts = Shift.objects.filter(revision=revision) \
            .filter(Q(date=todayX) & Q(slot__op=True))

    # first find on EXACT time for OP slots
    slotsOPWithinScheduled = filter_active_slots(now, scheduled_shifts)
    if verbose:
        print('\n-> 1st OP SLOTS -> ', slotsOPWithinScheduled)

    # second find on EXACT time - NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES
    if len(slotsOPWithinScheduled) == 0:
        nowLater = (nowFull + datetime.timedelta(hours=NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES)).time()
        slotsOPWithinScheduled = filter_active_slots(nowLater, scheduled_shifts)
        if len(slotsOPWithinScheduled):
            now = nowLater
        # print('-> 2nd try (2h later) OP SLOTS -> ', slotsOPWithinScheduled)

    # retrigger for the search (in case 'now' got updated)
    slots = filter_active_slots(now, scheduled_shifts)
    if verbose:
        print("-> SLOTS ALL ->", slots)
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
                'shiftID': lastCompletedShiftBeforeTodayNow.shiftID.label \
                    if lastCompletedShiftBeforeTodayNow is not None \
                    else prepare_ShiftID(today, now, None, error=True),
                'activeSlots': [lastShiftTeam[0].slot if len(lastShiftTeam) else None],
                'activeSlot': None,
                'currentTeam': lastShiftTeam
                }

    # for a final slot find the details
    slotToBeUsed = slotsOPWithinScheduled[0]
    if verbose:
        print('-> FOUND SLOT TO BE USED -> ', slotToBeUsed)

    # final correction for the date if 0:00 - end of night shift
    if slotToBeUsed.hour_start > slotToBeUsed.hour_end > now:
        today = today + datetime.timedelta(days=-1)
        nowFull = nowFull + datetime.timedelta(days=-1)

    # actual shift details finding based on the SLOT and date (today)
    sortedSlots = list(set(slots))
    sortedSlots.sort(key=lambda slotToSort: slotToSort.hour_end)
    activeSlots = []
    currentTeam = []
    for slot in sortedSlots:
        if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                or slot.hour_start <= now < slot.hour_end:
            for shifter in scheduled_shifts:
                if shifter.slot == slot and shifter.is_active and not shifter.is_cancelled:
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
            shiftID.date_created = datetime.datetime.combine(today.date(), now)  # FIXME tzinfo=pytz.UTC?
            shiftID.save()
        if shifter.shiftID is None:
            shifter.shiftID = shiftID
        shifter.save()


def update_details_from_LDAP(shifterDuty, ldap, useLDAP=True):
    if shifterDuty.member.email is not None and shifterDuty.member.mobile is not None:
        return None
    personal_data = []
    if useLDAP and ldap is not None:
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


def _get_mapped_role(oneRole, shiftRole):
    for role in DEFAULT_SHIFTER_TO_JSON:
        if role in shiftRole:  # special roles should encapsulate the mapped role abbreviation
            return role
    else:
        return oneRole


def _append_details_for(dataToReturn, oneRole, shifter):
    dataToReturn[oneRole] = shifter.member.name
    dataToReturn[oneRole + "Phone"] = shifter.member.mobile if shifter.member.mobile is not None else ''
    dataToReturn[oneRole + "Email"] = shifter.member.email if shifter.member.email is not None else ''


def prepare_for_JSON(activeShift, studies=None):
    dataToReturn = {'_datetime': activeShift['today'].strftime(DATE_FORMAT),
                    '_slot': 'outside active slots' if activeShift['activeSlot'] is None else activeShift[
                        'activeSlot'].abbreviation,
                    '_timeNow': datetime.datetime.now().strftime(SIMPLE_TIME),
                    '_timeRequested': activeShift['now'],
                    '_PVPrefix': 'NSO:Ops:',
                    'SID': activeShift['shiftID'],
                    'dayStudiesPlanned': [s.get_study_as_json() for s in studies] if studies is not None else []
                    }
    for oneRole in DEFAULT_SHIFTER_TO_JSON:
        dataToReturn[oneRole] = "N/A"
    for oneRole in DEFAULT_SHIFTER_TO_JSON:  # main roles and their alter ego
        for shifter in activeShift['currentTeam']:
            if oneRole in shifter.member.role.abbreviation:
                if shifter.role is None:  # no extra role in the same shift
                    _append_details_for(dataToReturn, oneRole, shifter)
                elif shifter.role is not None:  # extra assignment
                    if shifter.role.abbreviation in DEFAULT_SPECIAL_SHIFT_ROLES:
                        _append_details_for(dataToReturn, _get_mapped_role(oneRole, shifter.role.abbreviation), shifter)
    for oneRole in DEFAULT_SPECIAL_SHIFT_ROLES:  # acting roles
        for shifter in activeShift['currentTeam']:
            if shifter.role is not None and shifter.role.abbreviation in oneRole:
                _append_details_for(dataToReturn, _get_mapped_role(oneRole, shifter.role.abbreviation), shifter)

    return dataToReturn
