from django.test import TestCase
from shifts.models import *
from shifts.exchanges import perform_exchange_and_save_backup, \
    is_valid_for_hours_constraints, get_exchange_exchange_preview, perform_simplified_exchange_and_save_backup
from .common import make_test_schedule, FUNNY_SHIFT_LEADER, GRUMPY_SHIFT_LEADER
import pytz


class ExchangeShifts(TestCase):

    def setUp(self):
        make_test_schedule(printPlan=False)
        self.revisionBase = Revision.objects.filter(valid=True)[0]
        # local variables needed for each test
        self.m1 = Member.objects.get(first_name=FUNNY_SHIFT_LEADER)
        self.m2 = Member.objects.get(first_name=GRUMPY_SHIFT_LEADER)

        self.shift_m1_am = Shift.objects.get(member=self.m1, date=datetime.date(2022, 5, 3))
        self.shift_m2_pm = Shift.objects.get(member=self.m2, date=datetime.date(2022, 5, 3))
        self.shift2_m1_am = Shift.objects.get(member=self.m1, date=datetime.date(2022, 5, 11))
        self.shift2_m2_pm = Shift.objects.get(member=self.m2, date=datetime.date(2022, 5, 11))

        self.revisionBackup = Revision.objects.create(
            date_start=datetime.datetime(2022, 12, 30, 12, 00, 00, tzinfo=pytz.UTC),
            name='Backup Revision TEST', valid=True)

    def test_basic_exchange_object_creation(self):
        sPair = ShiftExchangePair.objects.create(shift=self.shift_m1_am,
                                                 shift_for_exchange=self.shift_m2_pm)
        sEx = _create_exchange(self.m1, self.revisionBackup, [sPair])
        self.assertEqual(1, sEx.shifts.all().count())

    def test_valid_simple_swap_no_objects_created(self):
        sPair = ShiftExchangePair.objects.create(shift=self.shift_m1_am,
                                                 shift_for_exchange=self.shift_m2_pm)
        sEx = _create_exchange(self.m1, self.revisionBackup, [sPair])
        self.assertTrue(is_valid_for_hours_constraints(sEx, sEx.requestor, self.revisionBase)[0])
        self.assertTrue(is_valid_for_hours_constraints(sEx, self.m2, self.revisionBase)[0])

    def test_invalid_simple_swap_no_objects_created(self):
        sPair = ShiftExchangePair.objects.create(shift=self.shift2_m1_am,
                                                 shift_for_exchange=self.shift2_m2_pm)
        sEx = _create_exchange(self.m1, self.revisionBackup, [sPair])
        self.assertFalse(is_valid_for_hours_constraints(sEx, sEx.requestor, self.revisionBase)[0])
        self.assertFalse(is_valid_for_hours_constraints(sEx, self.m2, self.revisionBase)[0])

    def test_invalid_swap_few_in_request_no_objects_created(self):
        # correct pair
        sPairCorr = ShiftExchangePair.objects.create(shift=self.shift_m1_am,
                                                     shift_for_exchange=self.shift_m2_pm)
        # incorrect pair
        sPair = ShiftExchangePair.objects.create(shift=self.shift2_m1_am,
                                                 shift_for_exchange=self.shift2_m2_pm)

        sEx = _create_exchange(self.m1, self.revisionBackup, [sPairCorr, sPair])
        self.assertFalse(is_valid_for_hours_constraints(sEx, sEx.requestor, self.revisionBase)[0])
        self.assertFalse(is_valid_for_hours_constraints(sEx, self.m2, self.revisionBase)[0])

    def test_valid_complex_no_objects(self):
        sPairCorr = ShiftExchangePair.objects.create(shift=self.shift_m1_am,
                                                     shift_for_exchange=self.shift_m2_pm)
        sPair = ShiftExchangePair.objects.create(shift=self.shift2_m1_am,
                                                 shift_for_exchange=self.shift2_m2_pm)

        sEx = _create_exchange(self.m1, self.revisionBackup, [sPairCorr, sPair])
        self.assertFalse(is_valid_for_hours_constraints(sEx, sEx.requestor, self.revisionBase)[0])
        self.assertFalse(is_valid_for_hours_constraints(sEx, self.m2, self.revisionBase)[0])

    def test_change_shifts_with_saved_objects(self):
        sPair = ShiftExchangePair.objects.create(shift=self.shift_m1_am,
                                                 shift_for_exchange=self.shift_m2_pm)
        sEx = _create_exchange(self.m1, self.revisionBackup, [sPair])

        nbOfShiftsInCurrent = Shift.objects.filter(revision=self.revisionBase).count()

        newShifts = perform_exchange_and_save_backup(sEx,
                                                     self.m2,
                                                     revisionBackup=self.revisionBackup)

        self.assertEqual(nbOfShiftsInCurrent, Shift.objects.filter(revision=self.revisionBase).count())
        self.assertEqual(2, Shift.objects.filter(revision=self.revisionBackup).count())
        self.assertEqual(2, len(newShifts))

    def test_simple_exchange_just_member(self):
        self.assertEqual(self.m1, self.shift_m1_am.member)
        perform_simplified_exchange_and_save_backup(self.shift_m1_am, self.m2, self.m2, revisionBackup=self.revisionBackup)
        aa = Shift.objects.filter(member=self.m2, date=self.shift_m1_am.date, slot=self.shift_m1_am.slot, revision=self.shift_m1_am.revision)
        self.assertEqual(1, len(aa))


def _print_shift_details(shift):
    print(shift.__dict__)


def _create_exchange(member, revision, shifts):
    sEx = ShiftExchange()
    sEx.requestor = member
    sEx.backupRevision = revision
    sEx.requested = datetime.datetime.now(tz=pytz.UTC)
    sEx.save()
    for sPair in shifts:
        sEx.shifts.add(sPair)
    return sEx
