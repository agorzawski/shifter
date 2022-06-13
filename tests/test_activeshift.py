from django.test import TestCase

from shifts.activeshift import prepare_active_crew, prepare_for_JSON

from .common import *


class ActiveShift(TestCase):
    testCases = {
        # the sample schedule is setup at each test.
        # normal working hours
        "caseInNWH": {"date": "2022-05-01", "slots": ("NWH",), "hour": "11:11:11", "SID": "20220501A"},
        # regular 24h op
        "caseInAM": {"date": "2022-05-01", "slots": ("AM", "PM", "NG"), "hour": "11:11:11", "SID": "20220501A"},
        "caseInPM": {"date": "2022-05-01", "slots": ("PM", "AM", "NG"), "hour": "18:11:11", "SID": "20220501B"},
        "caseInNG1": {"date": "2022-05-01", "slots": ("AM", "PM", "NG"), "hour": "23:11:11", "SID": "20220501C"},
        "caseInNG2": {"date": "2022-05-02", "slots": ("AM", "PM", "NG"), "hour": "3:11:11", "SID": "20220501C"},
        "caseInAMPM": {"date": "2022-05-01", "slots": ("AM", "PM", "NG"), "hour": "13:41:11", "SID": "20220501A"},
        "caseInAMOverlapPM": {"date": "2022-05-01", "slots": ("AM", "PM", "NG"), "hour": "14:11:11",
                              "SID": "20220501B"},
        ######
        # some longer schedules:
        "casePreA": {"date": "2022-05-10", "slots": ("AM", "PM", "NG", "NWH"), "hour": "15:11:11", "SID": "20220510B"},
        "caseA": {"date": "2022-05-10", "slots": ("AM", "PM", "NG"), "hour": "22:11:11", "SID": "20220510C"},
        "caseA2": {"date": "2022-05-11", "slots": ("AM", "PM", "NG"), "hour": "01:11:11", "SID": "20220510C"},
        "caseB": {"date": "2022-05-11", "slots": ("AM", "PM", "NG"), "hour": "22:11:11", "SID": "20220511C"},
        "caseB2": {"date": "2022-05-12", "slots": ("AM", "PM", "NG"), "hour": "01:11:11", "SID": "20220511C"},
        "caseC": {"date": "2022-05-12", "slots": ("AM", "PM", "NG"), "hour": "23:11:11", "SID": "20220512C"},
        "caseC2": {"date": "2022-05-13", "slots": ("AM", "PM", "NG"), "hour": "02:11:11", "SID": "20220512C"},

        ######
        # Funny & weird outside slots
        # last occurred shift same day
        "case6": {"date": "2022-04-30", "slots": ("NWH",), "hour": "18:11:11", "SID": "20220430A"},
        # <2h to the upcoming
        "case7": {"date": "2022-05-04", "slots": ("NWH",), "hour": "7:11:11", "SID": "20220504A"},
        # Last logged/occurred shift, even day before
        "case7b": {"date": "2022-05-01", "slots": ("AM",), "hour": "4:11:11", "SID": "20220430A"},
        # multiple op slots selected
        "case1": {"date": "2022-05-03", "slots": ("NWH", "AM", "PM"), "hour": "9:11:11", "SID": "20220503A"},
        "case2": {"date": "2022-05-03", "slots": ("NWH", "AM", "PM"), "hour": "15:11:11", "SID": "20220503B"},
        "case3": {"date": "2022-05-03", "slots": ("NWH", "AM", "PM"), "hour": "14:11:11", "SID": "20220503B"},
        "noOP": {"date": "2022-05-12", "slots": (), "hour": "18:11:11", "SID": "20220512A"},

    }

    def setUp(self):
        testShifts, campaign, revision = setup_schedule()
        create_test_shifts(slotsMembersDates=testShifts, campaign=campaign, revision=revision)

    def test_NWH_with_code_A_with_NWH_OP_TRUE_rest_FALSE(self):
        self.check(self.testCases["caseInNWH"])

    def test_AM_with_code_A(self):
        self.check(self.testCases["caseInAM"])

    def test_AM_with_code_A_just_before_handover(self):
        self.check(self.testCases["caseInAMPM"])

    def test_AM_with_code_A_during_overlapping_handover(self):
        self.check(self.testCases["caseInAMOverlapPM"])

    def test_PM_with_code_B_with_PM(self):
        self.check(self.testCases["caseInPM"])

    def test_EV_before_midnight_with_code_C(self):
        self.check(self.testCases["caseInNG1"])

    def test_EV_after_midnight_with_code_C(self):
        self.check(self.testCases["caseInNG2"])

    def test_after_NWH(self):
        self.check(self.testCases["case6"])

    def test_short_before_NWH_with_earlier_recognition(self):
        self.check(self.testCases["case7"])

    def test_short_before_Morning_with_last_previous_shift_from_day_before(self):
        self.check(self.testCases["case7b"])

    def test_mixed_NWH_and_AM_PM_with_OP_TRUE_case1(self):
        self.check(self.testCases["case1"])

    def test_mixed_NWH_and_AM_PM_with_OP_TRUE_case2(self):
        self.check(self.testCases["case2"])

    def test_mixed_NWH_and_AM_PM_with_OP_TRUE_case3(self):
        self.check(self.testCases["case3"])

    def test_mixed_NWH_and_AM_PM_with_OP_FALSE(self):
        self.check(self.testCases["noOP"])

    def test_longer_schedules_casePreA(self):
        self.check(self.testCases["casePreA"])

    def test_longer_schedules_caseA(self):
        self.check(self.testCases["caseA"])

    def test_longer_schedules_caseA2(self):
        self.check(self.testCases["caseA2"])

    def test_longer_schedules_caseB(self):
        self.check(self.testCases["caseB"])

    def test_longer_schedules_caseB2(self):
        self.check(self.testCases["caseB2"])

    def test_longer_schedules_caseC(self):
        self.check(self.testCases["caseC"])

    def test_longer_schedules_caseC2(self):
        self.check(self.testCases["caseC2"])

    def check(self, target, updateOPSlots=True, verbose=False):
        if updateOPSlots:
            update_test_slots(target["slots"])
        result = prepare_active_crew(dayToGo=target["date"], hourToGo=target["hour"], useLDAP=False, verbose=verbose)
        if verbose:
            print("============== TEST CASE ================")
            print(target)
            print("------------- RETURN ----------------")
            print(result)
            print(prepare_for_JSON(result))
            print("------------- END ----------------\n\n")
        self.assertEqual(target["SID"], result['shiftID'])


class FilterChecks(TestCase):

    def setUp(self):
        AM, PM, NG, NWH = create_four_test_slots()

    def test_filter_for_hour(self):
        update_test_slots(["NWH"])
        now = datetime.time(16, 29, 0)
        consider = Slot.objects.filter(op=True)
        slots = []
        for slot in consider:
            if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                    or slot.hour_start <= now < slot.hour_end:
                slots.append(slot)
        filteredSlots = slots
        self.assertEqual(1, len(filteredSlots))

    def test_filter_for_hour_overlap(self):
        update_test_slots(["AM", "NWH"])
        now = datetime.time(11, 29, 0)
        consider = Slot.objects.filter(op=True)
        slots = []
        for slot in consider:
            if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                    or slot.hour_start <= now < slot.hour_end:
                slots.append(slot)
        filteredSlots = slots
        self.assertEqual(2, len(filteredSlots))


def update_test_slots(slots):
    for opSlot in slots:
        slot = Slot.objects.get(abbreviation=opSlot)
        slot.op = True
        slot.save()
