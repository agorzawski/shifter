from django.contrib import admin
from django.utils.translation import ngettext
from django.contrib import messages
from .models import StudyRequest
from django.utils import timezone


class StudyRequestAdmin(admin.ModelAdmin):

    def make_priority(self, request, queryset):
        updated = queryset.update(priority=True)
        self.message_user(request, ngettext(
            '%d Priority updated.',
            '%d Priority updated',
            updated,
        ) % updated, messages.SUCCESS)
        self.description = 'Priority updated'

    def close_studies_DONE(self, request, queryset):
        self._update_state(request, queryset, 'D')

    def close_studies_CANCEL(self, request, queryset):
        self._update_state(request, queryset, 'C')

    def _update_state(self, request, queryset, state):
        updated = queryset.update(state=state,
                                  booking_finished=timezone.now(),
                                  finished_by=request.user)
        self.message_user(request, ngettext(
            '%d Priority updated.',
            '%d Priority updated',
            updated,
        ) % updated, messages.SUCCESS)
        self.description = 'Priority updated'

    def push_24h_forward(self, request, queryset):
        forward = timezone.timedelta(days=1)
        for one in queryset:
            currentSlotStart = one.slot_start
            currentSlotEnd = one.slot_end
            one.slot_start = currentSlotStart + forward
            one.slot_end = currentSlotEnd + forward
            one.save()
        self.description = 'Pushed forward by 24h'

    list_display = ('title', 'member', 'booking_created', 'slot_start', 'priority', 'state',)
    list_filter = ['booking_created', 'state', 'priority', 'member__team']

    ordering = ['booking_created']
    actions = [make_priority,
               push_24h_forward,
               close_studies_DONE,
               close_studies_CANCEL,
               ]


admin.site.register(StudyRequest, StudyRequestAdmin)
