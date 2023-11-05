"""
Prototype of the shifter-centralised notification implementation and classes.
"""

from abc import ABC, abstractmethod

from django.template.loader import render_to_string
from shifts.models import Shift, Revision, Member
from studies.models import StudyRequest
from django.core.mail import send_mail

from notifications.signals import notify

NOTIFICATIONS_CODE_SHIFT = 10
NOTIFICATION_CODE_REVISIONS = 20
NOTIFICATION_CODE_STUDIES = 30
NOTIFICATION_CODE_ERROR = -1


class NotificationService(ABC):
    """
    General notification system that takes an arbitrary event and broadcast by the means provided by the implementation.
    Supported events:
    - tuple of Shift - sent in case a modification is applied, i.e. two exchanged shifts,
    - StudyRequest - sent to Study Leader and Collaborators of the SR,
    - Revision - sent when new version is available with 'ready_for_preview==True',
    """
    #  TODO fix the url to be dynamic. There is no request context at this moment (or any other)
    def __init__(self, name, domain="https://shifter.esss.lu.se"):
        self._name = name
        self.default_domain = domain
        print('==>> Initialising ', name)

    @abstractmethod
    def _triggerShiftNotification(self, event):
        """
        triggers the notification on Shift/Collections of Shift/ShiftExchanges
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

    def notify(self, event) -> int:
        if isinstance(event, Shift) or isinstance(event, NewShiftsUpload):
            return self._triggerShiftNotification(event)
        elif isinstance(event, Revision):
            if event.ready_for_preview:
                return self._triggerRevisionNotification(event)
        elif isinstance(event, StudyRequest):
            return self._triggerStudyRequestNotification(event)
        else:
            print('Do not know how to notify for ', event)
            return NOTIFICATION_CODE_ERROR


class NewShiftsUpload:
    def __init__(self, revision, campaign, affectedMembers, rotaMaker, startEnd):
        self.revision = revision
        self.members = affectedMembers
        self.campaign = campaign
        self.rotaMaker = rotaMaker
        self.start = startEnd[0]
        self.end = startEnd[1]


class DummyNotifier(NotificationService):
    """ Mainly for test class """

    def __init__(self, name):
        super().__init__(name=name)

    def _triggerShiftNotification(self, event):
        print("Something new with the following: ", event)
        return NOTIFICATIONS_CODE_SHIFT

    def _triggerRevisionNotification(self, revision):
        print("New planning is available in your 'My shifts' space. \n\n Search for {}".format(revision))
        return NOTIFICATION_CODE_REVISIONS

    def _triggerStudyRequestNotification(self, study):
        notify.send(study.member, recipient=study.member, verb='You have created the study {}'.format(study.title))
        for one in study.collaborators.all():
            notify.send(one, recipient=one, verb='You have been added to the study {}'.format(study.title))
        print("{}: NEW study requested {}".format(self._name, study))
        return NOTIFICATION_CODE_STUDIES


class EmailNotifier(NotificationService):
    """ Simple Email creator, notifier and sender, using native Django send_mail and django-notification-hq"""
    DEFAULT_NO_REPLY = 'noreply@ess.eu'

    def _notify_internal_and_external(self, actor,  emailSubject, emailBody, affectedMembers, target=None):
        # sends the Django notifications
        notify.send(actor, recipient=affectedMembers, target=target, verb=emailSubject,
                    description=emailBody, emailed=True)
        # sends the email
        # FIXME maybe replace with the cron/job to sent 'unread' notifications (once a day)
        send_mail(emailSubject, emailBody, self.DEFAULT_NO_REPLY, [one.email for one in affectedMembers],
                  fail_silently=False,)

    def _triggerShiftNotification(self, event):
        if isinstance(event, Shift):
            pass

        if isinstance(event, NewShiftsUpload) and event.revision.valid: # not valid revisions go with another notify
            emailSubject = '[shifter] MAIN ROTA updated'
            emailBody = render_to_string('shiftsupload_email.html', {"campaign": event.campaign,
                                                                     "revision": event.revision,
                                                                     "rotaMaker": event.rotaMaker,
                                                                     "import_start": event.start,
                                                                     "import_end": event.end})

            self._notify_internal_and_external(actor=event.rotaMaker,
                                               target=None,
                                               emailSubject=emailSubject, emailBody=emailBody,
                                               affectedMembers=event.members)

        # isinstance(event, ShiftExchange):
        #     pass

    def _triggerRevisionNotification(self, revision):
        emailSubject = "[shifter] NEW REVISION"
        emailBody = render_to_string('shiftsnewrevision_email.html', {"revision": revision,})
        #  TODO Fix AnonymousUser. Seems like there is no good option to pass the actual user
        self._notify_internal_and_external(actor=Member.objects.get(username="AnonymousUser"),
                                           target=revision,
                                           emailSubject=emailSubject, emailBody=emailBody,
                                           affectedMembers=list(set([one.member for one in Shift.objects.filter(revision=revision)])))

    def _triggerStudyRequestNotification(self, study):

        emailSubject = '[shifter STUDY][{}] {}'.format(study.state_full(), study.title)
        emailBody = render_to_string('studyrequest_email.html', {"study": study,
                                                                 "studyState": study.state_full(),
                                                                 "col": study.collaborators.all(),
                                                                 "domain": self.default_domain})
        self._notify_internal_and_external(actor=study.member,
                                           target=study,
                                           emailSubject=emailSubject, emailBody=emailBody,
                                           affectedMembers=study.all_involved())


notificationService = EmailNotifier('[SHIFTER main Notifier]')