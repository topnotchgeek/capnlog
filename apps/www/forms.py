from django import forms
from django.forms import TextInput, Textarea, HiddenInput

from .models import BlogEntry


class BlogEntryForm(forms.ModelForm):
    # author_id = forms.IntegerField()

    class Meta:
        model = BlogEntry
        fields = ['author', 'title', 'entry_text']
        widgets = {
            'title': TextInput(attrs={'class': 'form-control'}),
            'entry_text': Textarea(attrs={'rows': '10', 'cols': '80', 'class': 'form-control'}),
            'author': HiddenInput()
        }
