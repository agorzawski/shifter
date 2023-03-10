from shifts.models import *

def get_shift(slot=None, fancy_date=None):
    shift = Shift()
    shift.role = None
    shift.revision = Revision.objects.all()[0]
    shift.date = fancy_date
    shift.slot = slot
    shift.member = Member.objects.get(username='test')
    shift.csv_upload_tag = 'TEST'
    shift.campaign = Campaign.objects.get(name='test')
    return shift


def setUpSlots():
    try:
        AM = Slot.objects.get(abbreviation='AM')
    except Slot.DoesNotExist:
        AM = Slot(name='Morning',
                  hour_start=datetime.time(7, 0, 0), hour_end=datetime.time(15, 00, 0),
                  abbreviation='AM', id_code='A')
        AM.save()
    try:
        PM = Slot.objects.get(abbreviation='PM')
    except Slot.DoesNotExist:
        PM = Slot(name='Evening',
                  hour_start=datetime.time(14, 0, 0), hour_end=datetime.time(22, 00, 00),
                  abbreviation='PM', id_code='B')
        PM.save()
    try:
        NG = Slot.objects.get(abbreviation='NG')
    except Slot.DoesNotExist:
        NG = Slot(name='Night',
                  hour_start=datetime.time(22, 0, 0), hour_end=datetime.time(6, 0, 0),
                  abbreviation='NG', id_code='C')
        NG.save()


def setUpRevisionsCampaignsMembers():
    revision = Revision(date_start=datetime.datetime(2020, 12, 30, 12, 00, 00), valid=True)
    revision.save()
    campaign = Campaign(name='test')
    campaign.date_start = datetime.datetime(2020, 12, 31, 12, 00, 00)
    campaign.date_end = datetime.datetime(2020, 12, 31, 23, 00, 00)
    campaign.save()
    member = Member(username='test', first_name='Some Fancy First Name')
    member.save()