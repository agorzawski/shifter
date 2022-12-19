from django.test import TestCase
from .common import *
from shifts.workinghours import find_weekly_rest_time_violation, find_daily_rest_time_violation
from shifts.workinghours import find_working_hours


class ActiveShift(TestCase):

    def setUp(self):
        testShifts, self.campaign, self.revision = setup_schedule()
        create_test_shifts(slotsMembersDates=testShifts, campaign=self.campaign, revision=self.revision)

    def test_CheckMinimumTimeDaily_CORRECT(self):
        scheduled_shits = Shift.objects.filter(member__first_name=FUNNY_SHIFT_LEADER)
        found = find_daily_rest_time_violation(scheduled_shits)
        self.assertEqual(0, len(found))

    def test_CheckMinimumTimeDaily_WRONG(self):
        scheduled_shits = Shift.objects.filter(member__first_name=GRUMPY_SHIFT_LEADER)
        found = find_daily_rest_time_violation(scheduled_shits)
        self.assertEqual(1, len(found))

    def test_CheckMinimumTimeDaily_CORRECT_with_NWH(self):
        scheduled_shits = Shift.objects.filter(member__first_name=POOR_SHIFT_LEADER)
        found = find_daily_rest_time_violation(scheduled_shits)
        self.assertEqual(0, len(found))

    def test_CheckMinimumTimeWeekly_CORRECT(self):
        scheduled_shits = Shift.objects.filter(member__first_name=FUNNY_SHIFT_LEADER)
        found = find_weekly_rest_time_violation(scheduled_shits)
        self.assertEqual(0, len(found))

    def test_CheckMinimumTimeWeekly_WRONG(self):
        scheduled_shits = Shift.objects.filter(member__first_name=GRUMPY_SHIFT_LEADER)
        found = find_weekly_rest_time_violation(scheduled_shits)
        self.assertEqual(1, len(found))


class WorkingTime(TestCase):

    def setUp(self):
        testShifts, self.campaign, self.revision = setup_schedule()
        create_test_shifts(slotsMembersDates=testShifts, campaign=self.campaign, revision=self.revision)

    def test_get_shiftSlots(self):
        scheduled_shits = Shift.objects.filter(member__role__abbreviation='SL')
        a = find_working_hours(scheduled_shits)
        #print(a)


