from django import forms


class SendApplicationForm(forms.Form):
    """
    Форма для подачи заявки в Service Desk.
    """
    tlg_id = forms.CharField(max_length=30)
    title = forms.CharField(max_length=250)
    application_type = forms.CharField(max_length=100)
    service_type = forms.CharField(max_length=100)
    description = forms.CharField(max_length=250)
    file = forms.FileField(required=False)
