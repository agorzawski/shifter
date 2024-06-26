from django import forms
from studies.models import StudyRequest
from members.models import Member


class StudyRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(StudyRequestForm, self).__init__(*args, **kwargs)
        if self.user.is_staff:
            self.fields['member'].choices = [(x.id, x.name) for x in Member.objects.all()]
        else:
            self.fields['member'].choices = [(x.id, x.name) for x in [self.user]]

    class Meta:
        model = StudyRequest
        fields = ('member', 'collaborators', 'title', 'description', 'duration', 'booking_comment', 'beam_current',
                  'beam_pulse_length', 'beam_destination', 'beam_reprate', 'jira', )
        widgets = {
            'collaborators': forms.SelectMultiple(attrs={'style': "width: 100%", 'id': 'collaborators_field'}),
            'booking_comment': forms.Textarea(attrs={'placeholder': "Tell us more about potential constraints regarding your slot."}),
        }
        labels = {'member': 'Study Leader'}



class StudyRequestFormClosing(forms.Form):
    status = forms.ChoiceField(choices=(('C', 'Canceled'), ('D', 'Done'), ('R', 'Requested')))
    booking_id = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'closed_booking_id_to_set',}))
    after_comment = forms.CharField(widget=forms.Textarea, required=False)
    logbook_link = forms.URLField(widget=forms.URLInput,required=False)
