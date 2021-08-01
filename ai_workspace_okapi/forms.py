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

class SegmentListForm(forms.ModelForm):
    segment = forms.ModelChoiceField(
        queryset=Segment.objects.all()
    )


    class Meta:
        model = Segment
        fields = (
            "segment",
        )

class SegmentForm(forms.ModelForm):
    mt_raw = forms.CharField(widget=forms.Textarea(attrs={"readonly": True}))
    class Meta:
        model = Segment
        fields = (
            "coded_source", "target", "id"
        )
        widgets = {
            "coded_source": forms.Textarea(attrs={"readonly": True})
        }