from abc import ABC, abstractmethod

from shifts.models import Shift, Revision
from studies.models import StudyRequest
from django.core.mail import send_mail


class NotificationService(ABC):
    """
    General notification system that takes an arbitrary event and broadcast by the means provided by the implementation.
    Supported events:
    - tuple of Shift - sent in case a modification is applied, i.e. two exchanged shifts,
    - StudyRequest - sent to Study Leader and Collaborators of the SR,
    - Revision - sent when new version is available with 'ready_for_preview==True',
    """

    def __init__(self, name):
        self._name = name
        print('==>> Initialising ', name)

    @abstractmethod
    def _triggerShiftNotification(self, event):
        """
        triggers the notification on tupple of shifts
        """
        pass

    @abstractmethod
    def _triggerRevisionNotification(self, event):
        """
        triggers the notification on Revision
        """
        pass

    @abstractmethod
    def _triggerStudyRequestNotification(self, event):
        """
        triggers the notification on StudyRequest
        """
        pass

    def notify(self, event):
        if isinstance(event, tuple):
            if len(event) == 2 and isinstance(event[0], Shift) and isinstance(event[1], Shift):
                self._triggerShiftNotification(event)
        elif isinstance(event, Revision):
            if event.ready_for_preview:
                self._triggerRevisionNotification(event)
        elif isinstance(event, StudyRequest):
            self._triggerStudyRequestNotification(event)
        else:
            print('Do not know how to notify for ', event)


class DummyNotifier(NotificationService):
    """ Mainly for test class """

    def __init__(self, name):
        super().__init__(name=name)

    def _triggerShiftNotification(self, event):
        print('Notification for shifts that have changed {} {}'.
              format(event[0], event[1]))

    def _triggerRevisionNotification(self, revision):
        print("New planning is available in your 'My shifts' space. \n\n Search for {}".
              format(revision))

    def _triggerStudyRequestNotification(self, shifts):
        pass


class EmailNotifier(NotificationService):
    """ Simple Email sender, using native Django send_mail"""

    def _triggerShiftNotification(self, shifts):
        send_mail(
            '[shifter] Shift change',
            'Notification for shifts that have updated \n {} \n {}'.
                format(shifts[0], shifts[1]),
            'noreply@ess.eu',
            [shifts[0].member.email, shifts[1].member.email],
            fail_silently=False,
        )

    def _triggerRevisionNotification(self, revision):
        pass  # TODO

    def _triggerStudyRequestNotification(self, study):
        send_mail(
            '[shifter upcoming study] {}'.format(study.title),
            'This is a notification for the upcoming study \n {} booked at {} \n\n {}'.
                format(study.title, study.slot_start, study.description),
            'noreply@ess.eu',
                [study.member.email] + [c.email for c in study.collaborator],
            fail_silently=False,
        )


class ESSNotifyService(NotificationService):
    """
    Simple service interface to the api of the notification service
    """
    def __init__(self, tokenId=None):
        super().__init__(name="ESS Notify Link")
        if tokenId is None:
            from shifter.settings import SHIFTER_ESS_NOTIFY_KEY
            if SHIFTER_ESS_NOTIFY_KEY is None:
                raise ValueError('Cannot start ESSNotifyLink without provided service id!')
            self._notifyKey = SHIFTER_ESS_NOTIFY_KEY
        else:
            self._notifyKey = tokenId

    def _sendNotify(self, payload):
        import requests
        requests.post(f'https://notify.esss.lu.se/api/v2/services/{self._notifyKey}/notifications',
                      json=payload,
                      headers={"accept": "application/json", "Content-Type": "application/json"})

    def _triggerRevisionNotification(self, revision):
        self._sendNotify({"title": "New planning revision",
                          "subtitle": "New planning is available in your 'My shifts' space. \n\n Search for {}".
                         format(revision),
                          "url": "https://shifter.esss.lu.se"})

    def _triggerShiftNotification(self, shifts):
        self._sendNotify({"title": "Shift update",
                          "subtitle": "Notification for shifts that have updated \n {} \n {}".
                         format(shifts[0], shifts[1]),
                          "url": "https://shifter.esss.lu.se"})

    def _triggerStudyRequestNotification(self, shifts):
        pass  # TODO
