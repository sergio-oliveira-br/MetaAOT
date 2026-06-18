# webapp/forms.py

from django import forms

class UrlForm(forms.Form):
    url = forms.URLField(label='URL', required=True, widget=forms.URLInput(attrs={'size': 60}))
