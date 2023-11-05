from django.test import TestCase
from .common_light import *
from shifter.notifications import DummyNotifier, NOTIFICATION_CODE_REVISIONS, NOTIFICATIONS_CODE_SHIFT, NOTIFICATION_CODE_STUDIES
from shifts.models import *


class NotificationService(TestCase):
    def setUp(self):
        setUpSlots()
        setUpRevisionsCampaignsMembers()
        self.shift1 = get_shift(slot=Slot.objects.get(abbreviation='PM'),
                                fancy_date=datetime.date(2021, 8, 23))
        self.shift2 = get_shift(slot=Slot.objects.get(abbreviation='AM'),
                                fancy_date=datetime.date(2021, 8, 24))
        self.notificationService = DummyNotifier('[DUMMY NOTIF FOR TEST]')

    def test_notification_on_shift(self):
        code = self.notificationService.notify((self.shift1, self.shift2))
        self.assertEqual(NOTIFICATIONS_CODE_SHIFT, code)

    def test_notification_on_revision_ready_for_review(self):
        revision = Revision(date_start=datetime.datetime(2023, 2, 28, 12, 00, 00), valid=False)
        revision.name = "Weeks 29-53 attempt 666"
        revision.ready_for_preview = True
        revision.save()
        code = self.notificationService.notify(revision)
        self.assertEqual(NOTIFICATION_CODE_REVISIONS, code)

    def test_notification_on_studies(self):
        #  TODO finish that
        code = NOTIFICATION_CODE_STUDIES
        self.assertEqual(NOTIFICATION_CODE_STUDIES, code)

    def test_notification_on_shift_exchange(self):
        #  TODO finish that
        code = NOTIFICATIONS_CODE_SHIFT
        self.assertEqual(NOTIFICATIONS_CODE_SHIFT, code)
