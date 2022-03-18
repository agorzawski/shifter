from django.test import TestCase

from members.models import Role
from shifts.models import *
from shifts.activeshift import prepare_active_crew, prepare_for_JSON

testCases = {
    # the sample schedule is setup at each test.
    # normal working hours
    "caseInNWH": {"date": "2022-05-01", "slots": ("NWH",), "hour": "11:11:11", "SID": "20220501A"},
    # regular 24h op
    "caseInAM": {"date": "2022-05-01", "slots": ("AM", "PM", "NG"), "hour": "11:11:11", "SID": "20220501A"},
    "caseInPM": {"date": "2022-05-01", "slots": ("PM", "AM", "NG"), "hour": "18:11:11", "SID": "20220501B"},
    "caseInNG1": {"date": "2022-05-01", "slots": ("AM", "PM", "NG"), "hour": "23:11:11", "SID": "20220501C"},
    "caseInNG2": {"date": "2022-05-02", "slots": ("AM", "PM", "NG"), "hour": "03:11:11", "SID": "20220501C"},
    "caseInAMPM": {"date": "2022-05-01", "slots": ("AM", "PM", "NG"), "hour": "13:41:11", "SID": "20220501A"},
    "caseInAMOverlapPM": {"date": "2022-05-01", "slots": ("AM", "PM", "NG"), "hour": "14:11:11", "SID": "20220501A"},
    ######
    # Funny & weird outside slots
    # last occurred shift same day
    "case6": {"date": "2022-05-04", "slots": ("NWH",), "hour": "18:11:11", "SID": "20220504A"},
    # <2h to the upcoming
    "case7": {"date": "2022-05-04", "slots": ("NWH",), "hour": "7:11:11", "SID": "20220504A"},
    # Last logged/occurred shift
    "case7b": {"date": "2022-05-04", "slots": ("NWH",), "hour": "5:11:11", "SID": "20220503B"},
    # multiple op slots selected
    "case8": {"date": "2022-05-04", "slots": ("NWH", "AM", "PM"), "hour": "9:11:11", "SID": "20220504A"},
    "case9": {"date": "2022-05-04", "slots": ("NWH", "AM", "PM"), "hour": "15:11:11", "SID": "20220504B"},
}


class ActiveShift(TestCase):

    def setUp(self):
        # Minimum object setup needed for the test
        # example of a full 24h cycle
        # AM 7-15, PM 14-22, NG 22-06(day after)

        AM = Slot(name='Morning',
                  hour_start=datetime.time(7, 0, 0), hour_end=datetime.time(15, 00, 0),
                  abbreviation='AM')
        AM.save()
        PM = Slot(name='Evening',
                  hour_start=datetime.time(14, 0, 0), hour_end=datetime.time(22, 00, 00),
                  abbreviation='PM')
        PM.save()
        NG = Slot(name='Night',
                  hour_start=datetime.time(22, 0, 0), hour_end=datetime.time(6, 0, 0),
                  abbreviation='NG')
        NG.save()
        NWH = Slot(name='NormalWH',
                   hour_start=datetime.time(8, 0, 0), hour_end=datetime.time(16, 30, 0),
                   abbreviation='NWH')
        NWH.save()
        revision = Revision(date_start=datetime.datetime(2020, 12, 30, 12, 00, 00), valid=True)
        revision.save()
        roleSL = Role(name="ShiftLeader", abbreviation="SL")
        roleSL.save()
        roleOP = Role(name="Operator", abbreviation="OP")
        roleOP.save()
        campaign = Campaign(name='test')
        campaign.date_start = datetime.datetime(2020, 12, 31, 12, 00, 00)
        campaign.date_end = datetime.datetime(2020, 12, 31, 23, 00, 00)
        campaign.save()
        member1 = Member(username='Morning member')
        member1.role=roleSL
        member1.save()
        member2 = Member(username='Afternoon member')
        member2.role = roleSL
        member2.save()
        member3 = Member(username='Night member')
        member3.role = roleSL
        member3.save()
        member1op = Member(username='Morning OP')
        member1op.role=roleSL
        member1op.save()
        member2op = Member(username='Afternoon OP')
        member2op.role = roleSL
        member2op.save()
        member3op = Member(username='Night OP')
        member3op.role = roleSL
        member3op.save()
        memberOffice = Member(username='Office Hours member')
        memberOffice.role = roleSL
        memberOffice.save()
        # prepare some simple schedule
        # adhoc matching the dates from the testCasesDefined above
        shiftID1 = ShiftID()
        shiftID1.label = '20220501A'
        shiftID1.date_created = datetime.datetime(2022, 5, 1, 7, 00, 00)
        shiftID1.save()
        shiftID2 = ShiftID()
        shiftID2.label = '20220501B'
        shiftID2.date_created = datetime.datetime(2022, 5, 1, 14, 14, 00)
        shiftID2.save()
        allShifts = (
            # 24h coverage with NWH ovelaping
            (member1, AM, datetime.date(2022, 5, 1), shiftID1),
            (member1op, AM, datetime.date(2022, 5, 1), shiftID1),
            (member2, PM, datetime.date(2022, 5, 1), shiftID2),
            (member2op, PM, datetime.date(2022, 5, 1), shiftID2),
            (member3, NG, datetime.date(2022, 5, 1), None),
            (member3op, NG, datetime.date(2022, 5, 1), None),
            (memberOffice, NWH, datetime.date(2022, 5, 1), None),
            # AM/PM with NWH overlaping
            (member1, AM, datetime.date(2022, 5, 3), None),
            (member2, PM, datetime.date(2022, 5, 3), None),
            (memberOffice, NWH, datetime.date(2022, 5, 3), None),
            # just NWH
            (memberOffice, NWH, datetime.date(2022, 5, 4), None),
        )
        create_shifts(slotsMembersDates=allShifts, campaign=campaign, revision=revision)

    def test_NWH_with_code_A_with_NWH_OP_TRUE_rest_FALSE(self):
        self.check(testCases["caseInNWH"])

    def test_AM_with_code_A(self):
        self.check(testCases["caseInAM"])

    def test_AM_with_code_A_just_before_handover(self):
        self.check(testCases["caseInAMPM"])

    def test_AM_with_code_A_during_overlapping_handover(self):
        self.check(testCases["caseInAMOverlapPM"])

    def test_PM_with_code_B_with_PM(self):
        self.check(testCases["caseInPM"])

    def test_EV_before_midnight_with_code_C(self):
        self.check(testCases["caseInNG1"])

    def test_EV_after_midnight_with_code_C(self):
        self.check(testCases["caseInNG2"])

    def test_after_NWH(self):
        self.check(testCases["case6"])

    def test_short_before_NWH_with_earlier_recognition(self):
        self.check(testCases["case7"])

    def test_short_before_NWH_without_earlier_recognition_last_previous_shift(self):
        self.check(testCases["case7b"])

    def test_mixed_NWH_and_AM_PM_with_OP_TRUE_case1(self):
        self.check(testCases["case8"])

    def test_mixed_NWH_and_AM_PM_with_OP_TRUE_case2(self):
        self.check(testCases["case9"])

    def check(self, X, verbose=True):
        for opSlot in X["slots"]:
            slot = Slot.objects.get(abbreviation=opSlot)
            slot.op = True
            slot.save()
        r = prepare_active_crew(dayToGo=X["date"], hourToGo=X["hour"], useLDAP=False)
        if verbose:
            print("====================================")
            print(X)
            print("------------------------------------")
            print(r)
            print(prepare_for_JSON(r))
            print("------------------------------------")
        self.assertEqual(X["SID"], r['shiftID'])


def create_shifts(slotsMembersDates=None, campaign=None, revision=None):
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
