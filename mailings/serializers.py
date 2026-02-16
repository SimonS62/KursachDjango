from rest_framework import serializers
from .models import Client, Message, Mailing, MessageAttempt


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__' # Или укажите нужные поля: ['id', 'email', 'full_name', 'comment', 'is_active']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class MailingSerializer(serializers.ModelSerializer):
    # Поле message и recipients будут отображаться как ID по умолчанию.
    # Можно сделать их вложенными, если нужно, но для простоты оставим ID.
    # message = MessageSerializer()
    # recipients = ClientSerializer(many=True)

    # Для отображения ID при GET и записи ID при POST/PUT
    message_id = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all(), source='message', write_only=True)
    message_subject = serializers.CharField(source='message.subject', read_only=True) # Для отображения темы

    recipient_ids = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        many=True,
        write_only=True,
        source='recipients'
    )
    # recipients = ClientSerializer(many=True, read_only=True) # Если нужно отображать полные данные получателей

    class Meta:
        model = Mailing
        fields = [
            'id',
            'start_time',
            'end_time',
            'status',
            'message', # Показываем ID сообщения
            'message_id', # Для записи ID
            'message_subject', # Отображает тему сообщения
            'recipients', # Показываем ID получателей
            'recipient_ids', # Для записи ID получателей
        ]
        read_only_fields = ['status'] # Статус вычисляется динамически

    # Переопределяем create, чтобы корректно обрабатывать ManyToManyField
    def create(self, validated_data):
        recipients_ids = validated_data.pop('recipients') # Получаем IDs получателей
        message_obj = validated_data.pop('message')       # Получаем объект сообщения

        mailing = Mailing.objects.create(message=message_obj, **validated_data)
        mailing.recipients.set(recipients_ids) # Устанавливаем получателей
        return mailing

    # Переопределяем update для ManyToManyField
    def update(self, instance, validated_data):
        recipients_ids = validated_data.pop('recipients', None) # Получаем IDs, если они есть
        if recipients_ids is not None:
            instance.recipients.set(recipients_ids)

        # Обновляем остальные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class MessageAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttempt
        fields = '__all__'
        read_only_fields = ('attempt_time', 'mailing', 'client') # Время, рассылка и клиент устанавливаются автоматически
