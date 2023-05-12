from rest_framework import serializers
from registration_bot.models import BotUsers, CompanyData, BankData, BotSettings


class BotUsersSerializer(serializers.ModelSerializer):
    """Сериалайзер для модели BotUsers"""

    class Meta:
        model = BotUsers
        fields = (
            'tlg_id',
            'tlg_username',
            'telephone',
            'email',
            'deal_id',
            'is_staff',
        )


class CompanyDataSerializer(serializers.ModelSerializer):
    """Сериалайзер для модели CompanyData"""

    class Meta:
        model = CompanyData
        fields = (
            'comp_name',
            'address',
            'ogrn',
            'inn',
            'top_management_post',
            'top_management_name',
        )


class BankDataSerializer(serializers.ModelSerializer):
    """Сериалайзер для модели BankData"""

    class Meta:
        model = BankData
        fields = (
            'bik',
            'rs',
            'cor_a',
            'bank_name',
        )


class BotSettingsSerializer(serializers.ModelSerializer):
    """Сериалайзер для модели BankData"""

    class Meta:
        model = BotSettings
        fields = '__all__'


class SendMsgToOLSerializer(serializers.Serializer):
    """
    Сериалайзер для POST запроса, цель которого - это отправка сообщения в ОЛ Битрикса.
        tlg_id - TG ID пользователя
        username - TG username пользователя
        last_name - TG last_name пользователя (опционально)
        name - TG first_name пользователя (опционально)
        msg_text - текст сообщения пользователя в чате с ботом
    """

    tlg_id = serializers.IntegerField(max_value=9999999999)
    username = serializers.CharField(max_length=400, required=False)
    name = serializers.CharField(max_length=400, required=False)
    last_name = serializers.CharField(max_length=400, required=False)
    msg_text = serializers.CharField(max_length=5000)


class FormLinkSerializer(serializers.Serializer):
    """
    Сериалайзер для ссылки на на форму сбора персональных данных.
    """
    form_link = serializers.CharField(max_length=99999999)
