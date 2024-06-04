from django.db.models.signals import post_save
from studies.models import StudyRequest
from django.dispatch import receiver
from studies.views.main import notificationService

"""
This is needed to handle all 'internal' operations (eg. via admin panel) that should be notifiable
"""


@receiver(post_save, sender=StudyRequest)
def notify_at_save(sender, instance, **kwargs):
    # notify only on particular state change
    if instance.state in ["B", "D"] :
        notificationService.notify(instance)
