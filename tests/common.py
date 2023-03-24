"""
A common part for many test, a standard test
"""
from django.db import IntegrityError

from members.models import Role
from shifts.models import *
import pytz


FUNNY_SHIFT_LEADER = "FunnyShiftLeader"
GRUMPY_SHIFT_LEADER = 'GrumpyShiftLeader'
POOR_SHIFT_LEADER= 'PoorShiftLeaderGuy'


def setup_schedule():
    # Minimum object setup needed for the tests
    # example of a full 24h cycle
    # AM 7-15, PM 14-22, NG 22-06(day after)

    roleSL, roleOP = create_two_test_roles()
    member1 = create_test_member('Morning member', FUNNY_SHIFT_LEADER, roleSL)
    member2 = create_test_member('Afternoon member', GRUMPY_SHIFT_LEADER, roleSL)
    member3 = create_test_member('Night member', POOR_SHIFT_LEADER, roleSL)
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
        (member2, AM, datetime.date(2022, 5, 13), None),
        (member3, NWH, datetime.date(2022, 5, 13), None),

        (member2, AM, datetime.date(2022, 5, 14), None),
        (member2, AM, datetime.date(2022, 5, 15), None),
        (member2, AM, datetime.date(2022, 5, 16), None),
    )
    return testShifts, campaign, revision


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


def create_four_test_slots():
    try:
        AM = Slot.objects.get(abbreviation='AM')
    except Slot.DoesNotExist:
        AM = Slot(name='Morning',
                  hour_start=datetime.time(7, 0, 0), hour_end=datetime.time(15, 00, 0),
                  abbreviation='AM')
        AM.id_code = "A"
        AM.save()
        print(AM, AM.id_code)
    try:
        PM = Slot.objects.get(abbreviation='PM')
    except Slot.DoesNotExist:
        print('create pm')
        PM = Slot(name='Evening',
                  hour_start=datetime.time(14, 0, 0), hour_end=datetime.time(22, 00, 00),
                  abbreviation='PM')
        PM.id_code = "B"
        PM.save()
        print(PM, PM.id_code)
    try:
        NG = Slot.objects.get(abbreviation='NG')
    except Slot.DoesNotExist:
        print('create night')
        NG = Slot(name='Night',
                  hour_start=datetime.time(22, 0, 0), hour_end=datetime.time(6, 0, 0),
                  abbreviation='NG',)
        NG.id_code = "C"
        NG.save()
        print(NG, NG.id_code)
    try:
        NWH = Slot.objects.get(abbreviation='NWH')
    except Slot.DoesNotExist:
        NWH = Slot(name='NormalWH',
                   hour_start=datetime.time(8, 0, 0), hour_end=datetime.time(16, 30, 0),
                   abbreviation='NWH')
        NWH.save()
    return AM, PM, NG, NWH
