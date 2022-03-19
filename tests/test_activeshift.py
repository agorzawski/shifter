from django.test import TestCase

from members.models import Role
from shifts.models import *
from shifts.activeshift import prepare_active_crew, prepare_for_JSON, filter_active_slots, filter_for_hour


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
        # Funny & weird outside slots
        # last occurred shift same day
        "case6": {"date": "2022-04-30", "slots": ("NWH",), "hour": "18:11:11", "SID": "20220430A"},
        # <2h to the upcoming
        "case7": {"date": "2022-05-04", "slots": ("NWH",), "hour": "7:11:11", "SID": "20220504A"},
        # Last logged/occurred shift, even day before
        "case7b": {"date": "2022-05-01", "slots": ("AM",), "hour": "4:11:11", "SID": "20220430A"},
        # multiple op slots selected
        "case1": {"date": "2022-05-04", "slots": ("NWH", "AM", "PM"), "hour": "9:11:11", "SID": "20220504A"},
        "case2": {"date": "2022-05-04", "slots": ("NWH", "AM", "PM"), "hour": "15:11:11", "SID": "20220504B"},
        "noOP": {"date": "2022-05-04", "slots": (), "hour": "13:11:11", "SID": "20220504A"},

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
        testShifts = (
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

    # FIXME This case is implicitly solved by the 'last created' shift' of the day before
    # with the caveat that EV shift will be initiated before midnight
    # def test_EV_after_midnight_with_code_C(self):
    #     self.check(self.testCases["caseInNG2"])

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

    def test_mixed_NWH_and_AM_PM_with_OP_FALSE(self):
        self.check(self.testCases["noOP"])


    def check(self, target, updateOPSlots=True, verbose=True):
        print("\n\n\n\n")
        if updateOPSlots:
            update_test_slots(target["slots"])
        result = prepare_active_crew(dayToGo=target["date"], hourToGo=target["hour"], useLDAP=False)
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
        filteredSlots = filter_for_hour(datetime.time(16, 29, 0), Slot.objects.filter(op=True))
        self.assertEqual(1, len(filteredSlots))

    def test_filter_for_hour_overlap(self):
        update_test_slots(["AM", "NWH"])
        filteredSlots = filter_for_hour(datetime.time(11, 29, 0), Slot.objects.filter(op=True))
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
    revision = Revision(date_start=datetime.datetime(2020, 12, 30, 12, 00, 00), valid=True)
    revision.save()
    campaign = Campaign(name='test', date_start=datetime.datetime(2020, 12, 31, 12, 00, 00),
                        date_end=datetime.datetime(2020, 12, 31, 23, 00, 00))
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
    shiftID0 = ShiftID(label='20220430A', date_created=datetime.datetime(2022, 4, 30, 7, 00, 00))
    shiftID0.save()
    shiftID1 = ShiftID(label='20220501A', date_created=datetime.datetime(2022, 5, 1, 7, 00, 00))
    shiftID1.save()
    shiftID2 = ShiftID(label='20220501B', date_created=datetime.datetime(2022, 5, 1, 14, 14, 00))
    shiftID2.save()
    return shiftID0, shiftID1, shiftID2


def create_two_test_roles():
    roleSL = Role(name="ShiftLeader", abbreviation="SL")
    roleSL.save()
    roleOP = Role(name="Operator", abbreviation="OP")
    roleOP.save()
    return roleSL, roleOP
