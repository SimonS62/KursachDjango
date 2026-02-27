from django import forms
from .models import Client, Message, Mailing


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        # Указываем поля, которые хотим видеть в форме.
        # Можно также использовать '__all__' для всех полей модели.
        fields = ['name', 'email', 'phone_number', 'timezone']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']

class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['subject', 'text', 'scheduled_at', 'clients'] # Укажите актуальные поля вашей модели Mailing
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'clients': forms.CheckboxSelectMultiple(), # Пример для ManyToManyField
        }
