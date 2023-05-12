from rest_framework import serializers
from vpn_bot.models import TlgUser, VpnBotSettings


class TlgUserSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для модели TlgUser
    """
    class Meta:
        model = TlgUser
        fields = '__all__'


class VpnBotSettingsSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для модели VpnBotSettings.
    """
    class Meta:
        model = VpnBotSettings
        fields = '__all__'

