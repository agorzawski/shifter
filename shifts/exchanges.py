from django.db.models import Q
from shifts.models import ShiftExchange, Member, Shift, ShiftExchangePair, Revision
from shifts.workinghours import find_daily_rest_time_violation, find_weekly_rest_time_violation
from datetime import timedelta
from django.utils import timezone


def get_exchange_exchange_preview(shiftExchange: ShiftExchange, baseRevision, previewRangeDays=7, verbose=False):
    """
    Returns all new shift plan wrt shifts requested for change (each change component
    queries previewRangeDays forward and backward)

    All lists wiht new 'after change shifts' is returned.

    WARNING: at this stage, no changes to any shift if provided, the 'new'
    theoretical shifts exists ONLY as objects and are not represented in the db

    """
    if verbose:
        print("\t============================")
        print('\t----- TESTING validity -----')
        print("\t============================")
        print("\t", shiftExchange)

    allShiftsForNewPlanning = []
    usedSlots = []
    for shiftSwap in shiftExchange.shifts.all():
        usedSlots += [shiftSwap.shift.id, shiftSwap.shift_for_exchange.id]

    for shiftSwap in shiftExchange.shifts.all():
        if verbose: print("\t", shiftSwap)
        # create new swapped shifts
        newS = _prepare_after_swap_shifts(shiftSwap)
        if verbose: print("\t", newS)
        allShiftsForNewPlanning += newS
        # member 1 future setup:
        sM1TmpBefore = Shift.objects.filter(member=shiftSwap.shift.member, revision=baseRevision). \
            filter(Q(date__lt=shiftSwap.shift_for_exchange.date) &
                   Q(date__gt=(shiftSwap.shift_for_exchange.date + timedelta(days=-previewRangeDays))))
        sM1TmpAfter = Shift.objects.filter(member=shiftSwap.shift.member, revision=baseRevision). \
            filter(Q(date__gt=shiftSwap.shift_for_exchange.date) &
                   Q(date__lt=(shiftSwap.shift_for_exchange.date + timedelta(days=previewRangeDays))))
        if verbose: print("\t", sM1TmpBefore, sM1TmpAfter)

        for s in list(sM1TmpAfter)+list(sM1TmpBefore):
            if s.id in usedSlots:
                continue
            usedSlots.append(s.id)
            allShiftsForNewPlanning.append(s)

        sM2TmpBefore = Shift.objects.filter(member=shiftSwap.shift_for_exchange.member,
                                            revision=baseRevision). \
            filter(Q(date__lt=shiftSwap.shift.date) &
                   Q(date__gt=(shiftSwap.shift.date + timedelta(days=-previewRangeDays))))
        sM2TmpAfter = Shift.objects.filter(member=shiftSwap.shift_for_exchange.member,
                                           revision=baseRevision). \
            filter(Q(date__gt=shiftSwap.shift.date) &
                   Q(date__lt=(shiftSwap.shift.date + timedelta(days=previewRangeDays))))
        if verbose: print("\t", sM2TmpBefore, sM2TmpAfter)

        for s in list(sM2TmpAfter)+list(sM2TmpBefore):
            if s.id in usedSlots:
                continue
            usedSlots.append(s.id)
            allShiftsForNewPlanning.append(s)

    if verbose:
        print(allShiftsForNewPlanning)
        print("\t============================")
    return allShiftsForNewPlanning


def _create_shift(shift, member, revision=None, permanent=False, pre_comment=None):
    """
    Creates a shift from a shift but with changed member and revision
    """
    s = Shift()
    s.member = member
    s.slot = shift.slot
    s.campaign = shift.campaign
    s.date = shift.date
    s.shiftID = shift.shiftID
    s.is_active = True
    s.is_cancelled = False
    s.revision = shift.revision if revision is None else revision
    s.csv_upload_tag = shift.csv_upload_tag
    if pre_comment is not None:
        s.pre_comment = pre_comment
    if permanent:
        s.save()
    return s


def _prepare_after_swap_shifts(shiftExchangePair: ShiftExchangePair,
                               permanent=False) -> list:
    s1 = _create_shift(shiftExchangePair.shift,
                       shiftExchangePair.shift_for_exchange.member,
                       permanent=permanent)
    s2 = _create_shift(shiftExchangePair.shift_for_exchange,
                       shiftExchangePair.shift.member,
                       permanent=permanent)
    return [s1, s2]


def _update_exchange_pair(oneSwap, revisionBackup):
    oneSwap.shift.revision = revisionBackup
    oneSwap.shift.save()
    oneSwap.shift_for_exchange.revision = revisionBackup
    oneSwap.shift_for_exchange.save()


def is_valid_for_hours_constraints(shiftExchange: ShiftExchange, member: Member, baseRevision: Revision,) -> tuple:
    """
    returns tuple of boolean, and list of violated shifts
    """
    closeScheduleAfterUpdate = get_exchange_exchange_preview(shiftExchange, baseRevision)
    # FIXME consider ShiftExchange per only TWO members, then one can save calls to check validity for each member
    s1 = find_daily_rest_time_violation([x for x in closeScheduleAfterUpdate if x.member == member])
    s2 = find_weekly_rest_time_violation([x for x in closeScheduleAfterUpdate if x.member == member])

    return len(s1) == 0 & len(s2) == 0, (s1, s2)


def perform_exchange_and_save_backup(shiftExchange: ShiftExchange,
                                     approver: Member,
                                     revisionBackup: Revision,
                                     verbose=False) -> list:
    """
    creates new shifts for the proposed slots, keeps the old ones in the revisionBackup,
    makes the shiftExchange as Done==True

    Warning: this call, changes the shifts!
    """
    if revisionBackup is None:
        raise ValueError('The backup revision needs to be provided to store the shift exchange!')
    if verbose:
        print("\t============================")
        print('\t----- SAVING EXCHANGE ------')
        print("\t============================")
        print(shiftExchange)
        print('Approved by ', approver)
        print('Backup rev to use ', revisionBackup)
    shiftsAfterSwap = []
    for oneSwap in shiftExchange.shifts.all():
        shifts = _prepare_after_swap_shifts(oneSwap, permanent=True)
        shiftsAfterSwap += shifts
        _update_exchange_pair(oneSwap, revisionBackup)

    shiftExchange.implemented = True
    shiftExchange.approver = approver
    shiftExchange.approved = timezone.localtime(timezone.now())
    shiftExchange.save()
    if verbose: print("\t============================")
    return shiftsAfterSwap


def perform_simplified_exchange_and_save_backup(shift: Shift,
                                                newMember: Member,
                                                approver: Member,
                                                revisionBackup: Revision) -> ShiftExchange:
    """Performs a simplified shift exchange when in the existing shift new member is created"""
    fakeShift = _create_shift(shift, newMember,
                              revision= revisionBackup,
                              pre_comment="FakeAndTemporary shift created when updating the change of Member",
                              permanent=True)
    sPair = ShiftExchangePair.objects.create(shift=shift, shift_for_exchange=fakeShift)
    sEx = ShiftExchange()
    sEx.requestor = approver
    sEx.approver = approver
    sEx.backupRevision = revisionBackup
    sEx.requested = timezone.now()
    # FIXME consider actually performing the check. TO be seen how to 'avoid' constraints for the fake swap partner
    sEx.applicable = True
    sEx.tentative = False
    sEx.save()
    sEx.shifts.add(sPair)
    sEx.save()
    perform_exchange_and_save_backup(sEx, approver, revisionBackup=sEx.backupRevision, verbose=True)
    return sEx