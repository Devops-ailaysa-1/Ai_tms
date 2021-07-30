from django import forms
from .models import Document, Segment

class DocumentListForm(forms.Form):
    documents = forms.ModelChoiceField(
        queryset=Document.objects.all()
    )

    class Meta:
        fields = (
            "documents",
        )

class SegmentListForm(forms.Form):
    segment = forms.ModelChoiceField(
        queryset=Segment.objects.all()
    )


    class Meta:
        fields = (
            "segment"
        )