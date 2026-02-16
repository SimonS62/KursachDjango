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
        # Для рассылки мы хотим выбрать клиентов и сообщения.
        # Предполагается, что у вас есть соответствующие поля в модели Mailing.
        fields = ['name', 'clients', 'message', 'schedule_time', 'is_active']
