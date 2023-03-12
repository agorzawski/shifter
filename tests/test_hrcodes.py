from .common_light import *
from django.test import TestCase
from shifts.models import *
import shifts.hrcodes as hrc

HOURS_AM = {'OB1': 0, 'OB2': 1, 'OB3': 0, 'OB4': 0, 'NWH': 7}  #
HOURS_PM = {'OB1': 4, 'OB2': 0, 'OB3': 0, 'OB4': 0, 'NWH': 4}  #
HOURS_NG = {'OB1': 2, 'OB2': 6, 'OB3': 0, 'OB4': 0, 'NWH': 0}  #
HOURS_WE = {'OB1': 0, 'OB2': 0, 'OB3': 8, 'OB4': 0, 'NWH': 0}  # + normal holidays, like WE
HOURS_BH = {'OB1': 0, 'OB2': 0, 'OB3': 0, 'OB4': 8, 'NWH': 0}  # special holidays


class HRCodes(TestCase):

    def setUp(self):
        setUpSlots()
        setUpRevisionsCampaignsMembers()

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

    def test_codes_BankHoliday(self):  # on bank holiday
        shift = get_shift(slot=Slot.objects.get(abbreviation='PM'),
                          fancy_date=datetime.date(2021, 6, 25))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_BH)

    def test_codes_BankHoliday_AdjWE(self):  # a WE after bank holiday
        shift = get_shift(slot=Slot.objects.get(abbreviation='PM'),
                          fancy_date=datetime.date(2021, 6, 27))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_BH)

    def test_codes_Not_BankHoliday(self):  # a shift a day AFTER  bank holiday
        shift = get_shift(slot=Slot.objects.get(abbreviation='AM'),
                          fancy_date=datetime.date(2022, 4, 19))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_AM)

    def test_codes_Not_BankHoliday2(self):  # a two shift two day AFTER bank holiday
        shift = get_shift(slot=Slot.objects.get(abbreviation='AM'),
                          fancy_date=datetime.date(2022, 4, 20))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_AM)

    def test_codes_BankHolidayXmasEve(self):
        shift = get_shift(slot=Slot.objects.get(abbreviation='AM'),
                          fancy_date=datetime.date(2022, 12, 24))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_BH)

    def test_codes_red_day_2023(self):  # a shift on a red day -> OB3
        shift = get_shift(slot=Slot.objects.get(abbreviation='AM'),
                          fancy_date=datetime.date(2023, 5, 1))
        self.compare(hrc.get_code_counts(shift), HOURS_WE)
        shift = get_shift(slot=Slot.objects.get(abbreviation='NG'),
                          fancy_date=datetime.date(2023, 5, 1))
        self.compare(hrc.get_code_counts(shift), HOURS_WE)

    def test_codes_red_day_2022(self):  # a shift on a red day -> OB3
        shift = get_shift(slot=Slot.objects.get(abbreviation='AM'),
                          fancy_date=datetime.date(2022, 6, 6))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_WE)

    def test_reduced_day_morning(self):  # a shift on a reduced day - no weird OB
        shift = get_shift(slot=Slot.objects.get(abbreviation='AM'),
                          fancy_date=datetime.date(2023, 4, 6))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_AM)

    def test_reduced_day_afternoon(self):  # a pm shift on a reduced day -> all OB3
        shift = get_shift(slot=Slot.objects.get(abbreviation='PM'),
                          fancy_date=datetime.date(2023, 4, 6))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_WE)

    def test_reduced_day_with_night_shift(self):  # a shift on a red day -> OB3
        shift = get_shift(slot=Slot.objects.get(abbreviation='NG'),
                          fancy_date=datetime.date(2023, 4, 6))
        h = hrc.get_code_counts(shift)
        self.compare(h, HOURS_WE)

    def compare(self, codes1, codes2):
        for oneCode in codes1.keys():
            self.assertEqual(codes1.get(oneCode), codes2.get(oneCode))
