from django.test import TestCase
from shifts.models import *
import shifts.hrcodes as hrc

HOURS_AM = {'OB1': 0, 'OB2': 0, 'OB3': 0, 'OB4': 0}  #
HOURS_PM = {'OB1': 4, 'OB2': 0, 'OB3': 0, 'OB4': 0}  #
HOURS_NG = {'OB1': 2, 'OB2': 6, 'OB3': 0, 'OB4': 0}  #
HOURS_WE = {'OB1': 0, 'OB2': 0, 'OB3': 8, 'OB4': 0}  #


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


class HRCodes(TestCase):

    def setUp(self):
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

        revision = Revision(date_start=datetime.datetime(2020, 12, 30, 12, 00, 00), valid=True)
        revision.save()
        campaign = Campaign(name='test')
        campaign.date_start = datetime.datetime(2020, 12, 31, 12, 00, 00)
        campaign.date_end = datetime.datetime(2020, 12, 31, 23, 00, 00)
        campaign.save()
        member = Member(username='test')
        member.save()

    def test_codes_simple(self):
        shift = get_shift(slot=Slot.objects.get(abbreviation='AM'),
                       fancy_date=datetime.date(2021, 8, 26))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_AM)

    def test_codes_incl_late_evening(self):
        shift = get_shift(slot=Slot.objects.get(abbreviation='PM'),
                       fancy_date=datetime.date(2021, 8, 23))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_PM)

    def test_codes_overnight(self):
        shift = get_shift(slot=Slot.objects.get(abbreviation='NG'),
                       fancy_date=datetime.date(2021, 8, 26))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_NG)

    def test_codes_WE(self):
        shift = get_shift(slot=Slot.objects.get(abbreviation='PM'),
                       fancy_date=datetime.date(2021, 8, 28))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_WE)

    def compare(self, codes1, codes2):
        for oneCode in codes1.keys():
            self.assertEqual(codes1.get(oneCode), codes2.get(oneCode))