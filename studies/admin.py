from django.contrib import admin

# Register your models here.
from .models import StudyRequest

@admin.action(description='Mark selected studies as priority')
def make_priority(modeladmin, request, queryset):
    queryset.update(priority=True)

class StudyRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'member', 'booking_created', 'priority','state')
    list_filter = ['booking_created','state','priority']
    ordering = ['booking_created']
    actions = [make_priority]

admin.site.register(StudyRequest,StudyRequestAdmin)