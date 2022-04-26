from django.test import TestCase

from members.models import Role
from shifts.models import *
from shifts.activeshift import prepare_active_crew, prepare_for_JSON

import pytz


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
                              "SID": "20220501A"},
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
        "case3": {"date": "2022-05-03", "slots": ("NWH", "AM", "PM"), "hour": "14:11:11", "SID": "20220503A"},
        "noOP": {"date": "2022-05-12", "slots": (), "hour": "18:11:11", "SID": "20220512A"},

    }

    def setUp(self):
        # Minimum object setup needed for the test
        # example of a full 24h cycle
        # AM 7-15, PM 14-22, NG 22-06(day after)

        roleSL, roleOP = create_two_test_roles()
        member1 = create_test_member('Morning member', 'FunnyShiftLeader', roleSL)
        member2 = create_test_member('Afternoon member', 'GrumpyShiftLeader', roleSL)
        member3 = create_test_member('Night member', 'PoorShiftLeaderGuy', roleSL)
        member1op = create_test_member('Morning OP', 'SomePoorOperator', roleOP)
        member2op = create_test_member('Afternoon OP', 'AnotherPoorOperator', roleOP)
        member3op = create_test_member('Night OP', 'UnknownPoorOperator', roleOP)
        memberOffice = create_test_member('Office Hours member', 'OfficeHoursEmployee', roleSL)
        # prepare some simple schedule
        shiftID0, shiftID1, shiftID2 = create_test_shiftIDs()
        AM, PM, NG, NWH = create_four_test_slots()
        campaign, revision = create_test_campaign_revision()
        a10, b10, c10, a11, b11, c11, a12 = create_test_shiftIDs_multiple()
        testShifts = (  # The TEST schedule
            # standalone correct NWH shift
            (member1, NWH, datetime.date(2022, 4, 30), shiftID0),
            # 24h coverage with NWH overlapping
            (member1, AM, datetime.date(2022, 5, 1), shiftID1),
            (member1op, AM, datetime.date(2022, 5, 1), shiftID1),
            (member2, PM, datetime.date(2022, 5, 1), shiftID2),
            (member2op, PM, datetime.date(2022, 5, 1), shiftID2),
            (member3, NG, datetime.date(2022, 5, 1), None),
            (member3op, NG, datetime.date(2022, 5, 1), None),
            (memberOffice, NWH, datetime.date(2022, 5, 1), None),
            # AM/PM with NWH overlapping
            (member1, AM, datetime.date(2022, 5, 3), None),
            (member2, PM, datetime.date(2022, 5, 3), None),
            (memberOffice, NWH, datetime.date(2022, 5, 3), None),
            # just NWH
            (memberOffice, NWH, datetime.date(2022, 5, 4), None),
            # more than one 24h round with some ppl scheduled NWH
            (member1, AM, datetime.date(2022, 5, 10), a10),
            (member2, PM, datetime.date(2022, 5, 10), b10),
            (member3, NG, datetime.date(2022, 5, 10), c10),
            (memberOffice, NWH, datetime.date(2022, 5, 10), None),
            (member1, AM, datetime.date(2022, 5, 11), a11),
            (member2, PM, datetime.date(2022, 5, 11), b11),
            (member3, NG, datetime.date(2022, 5, 11), c11),
            (memberOffice, NWH, datetime.date(2022, 5, 11), None),
            (member1, AM, datetime.date(2022, 5, 12), a12),
            (member2, PM, datetime.date(2022, 5, 12), None),
            (member3, NG, datetime.date(2022, 5, 12), None),
            (memberOffice, NWH, datetime.date(2022, 5, 12), None),
        )
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


def create_test_shifts(slotsMembersDates=None, campaign=None, revision=None):
    for one in slotsMembersDates:
        shift = Shift()
        shift.member = one[0]  # member1
        shift.slot = one[1]  # AM
        shift.campaign = campaign
        shift.revision = revision
        shift.date = one[2]  # datetime.date(2022, 5, 1)
        if one[3] is not None:
            shift.shiftID = one[3]
        shift.save()


def create_test_member(username, firstname, role):
    member1 = Member(username=username)
    member1.first_name = firstname
    member1.role = role
    member1.save()
    return member1


def create_test_campaign_revision():
    revision = Revision(date_start=datetime.datetime(2020, 12, 30, 12, 00, 00, tzinfo=pytz.UTC), valid=True)
    revision.save()
    campaign = Campaign(name='test', date_start=datetime.datetime(2020, 12, 31, 12, 00, 00, tzinfo=pytz.UTC),
                        date_end=datetime.datetime(2020, 12, 31, 23, 00, 00, tzinfo=pytz.UTC))
    campaign.save()
    return campaign, revision


def create_four_test_slots():
    AM = Slot(name='Morning',
              hour_start=datetime.time(7, 0, 0), hour_end=datetime.time(15, 00, 0),
              abbreviation='AM')
    AM.save()
    PM = Slot(name='Evening',
              hour_start=datetime.time(14, 0, 0), hour_end=datetime.time(22, 00, 00),
              abbreviation='PM', id_code='B')
    PM.save()
    NG = Slot(name='Night',
              hour_start=datetime.time(22, 0, 0), hour_end=datetime.time(6, 0, 0),
              abbreviation='NG', id_code='C')
    NG.save()
    NWH = Slot(name='NormalWH',
               hour_start=datetime.time(8, 0, 0), hour_end=datetime.time(16, 30, 0),
               abbreviation='NWH')
    NWH.save()
    return AM, PM, NG, NWH


def create_test_shiftIDs():
    shiftID0 = ShiftID(label='20220430A', date_created=datetime.datetime(2022, 4, 30, 7, 00, 00, tzinfo=pytz.UTC))
    shiftID0.save()
    shiftID1 = ShiftID(label='20220501A', date_created=datetime.datetime(2022, 5, 1, 7, 00, 00, tzinfo=pytz.UTC))
    shiftID1.save()
    shiftID2 = ShiftID(label='20220501B', date_created=datetime.datetime(2022, 5, 1, 14, 14, 00, tzinfo=pytz.UTC))
    shiftID2.save()
    return shiftID0, shiftID1, shiftID2


def create_test_shiftIDs_multiple():
    a10 = ShiftID(label='20220510A', date_created=datetime.datetime(2022, 5, 10, 7, 00, 00, tzinfo=pytz.UTC))
    a10.save()
    b10 = ShiftID(label='20220510B', date_created=datetime.datetime(2022, 5, 10, 14, 30, 00, tzinfo=pytz.UTC))
    b10.save()
    c10 = ShiftID(label='20220510C', date_created=datetime.datetime(2022, 5, 10, 22, 14, 00, tzinfo=pytz.UTC))
    c10.save()
    a11 = ShiftID(label='20220511A', date_created=datetime.datetime(2022, 5, 11, 7, 00, 00, tzinfo=pytz.UTC))
    a11.save()
    b11 = ShiftID(label='20220511B', date_created=datetime.datetime(2022, 5, 11, 14, 30, 00, tzinfo=pytz.UTC))
    b11.save()
    c11 = ShiftID(label='20220511C', date_created=datetime.datetime(2022, 5, 11, 22, 14, 00, tzinfo=pytz.UTC))
    c11.save()
    a12 = ShiftID(label='20220512A', date_created=datetime.datetime(2022, 5, 12, 7, 00, 00, tzinfo=pytz.UTC))
    a12.save()
    return a10, b10, c10, a11, b11, c11, a12,


def create_two_test_roles():
    roleSL = Role(name="ShiftLeader", abbreviation="SL")
    roleSL.save()
    roleOP = Role(name="Operator", abbreviation="OP")
    roleOP.save()
    return roleSL, roleOP
