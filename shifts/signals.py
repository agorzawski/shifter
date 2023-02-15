from django.db.models.signals import post_save
from shifts.models import Revision
from django.dispatch import receiver
from shifts.views.main import notificationService


@receiver(post_save, sender=Revision)
def notify_at_save(sender, instance, **kwargs):
    notificationService.notify(instance)