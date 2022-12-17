from django import forms
from studies.models import StudyRequest


class StudyRequestForm(forms.ModelForm):
    class Meta:
        model = StudyRequest
        fields = ('member', 'title', 'description', 'duration', 'beam_current', 'beam_pulse_length', 'beam_destination', 'beam_reprate', 'jira')
        widgets = {
            'collaborators': forms.SelectMultiple(),
        }

class StudyRequestFormClosing(forms.ModelForm):
    class Meta:
        model = StudyRequest
        fields = ('after_comment',)