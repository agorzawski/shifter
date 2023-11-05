from django.db.models.signals import post_save
from shifts.models import Revision
from django.dispatch import receiver
from shifts.views.main import notificationService

"""
This is needed to handle all 'internal' operations (eg. via admin panel) that should be notifiable
"""


@receiver(post_save, sender=Revision)
def notify_at_save(sender, instance, **kwargs):
    # notify only on particular state change
    if instance.ready_for_preview:
        notificationService.notify(instance)
