from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=25)
    username.widget.attrs = {'size': 8}
    password = forms.CharField(max_length=30, widget=forms.PasswordInput)
    password.widget.attrs = {'size': 8}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)