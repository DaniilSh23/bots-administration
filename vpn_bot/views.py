from loguru import logger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from vpn_bot.models import TlgUser, VpnBotSettings
from vpn_bot.serializers import TlgUserSerializer, VpnBotSettingsSerializer


class TlgUserView(APIView):
    """
    Вьюшка для обработки запросов, связанных с моделью TlgUser.
    """
    def post(self, request, format=None):
        """
        Обработка POST запроса.
        """
        logger.info(f'Получен запрос от VPN_BOT на запись пользователя.')
        serializer = TlgUserSerializer(data=request.data)
        if serializer.is_valid():
            tlg_user_obj = TlgUser.objects.update_or_create(
                tlg_id=serializer.data.get('tlg_id'),
                defaults=serializer.data
            )
            logger.success(f'Пользователь VPN_BOT c TG_ID == {serializer.data.get("tlg_id")} '
                           f'был {"создан" if tlg_user_obj[1] else "обновлён"}.')
            result_object = TlgUserSerializer(tlg_user_obj[0], many=False).data
            return Response(result_object, status.HTTP_200_OK)
        else:
            logger.warning(f'Данные от VPN_BOT на запись пользователя не прошли валидацию.')
            return Response({'result': 'Переданные данные не прошли валидацию'}, status.HTTP_400_BAD_REQUEST)


class VpnBotAdminsView(APIView):
    """
    Вьюшка для обработки запросов, связанных с таким ключом настройки VPN_BOT как vpn_bot_admin.
    """
    def get(self, request, format=None):
        """
        Обработка GET запроса для получения списка ID админов VPN_BOT
        """
        vpn_bot_settings_obj = VpnBotSettings.objects.filter(key='vpn_bot_admin')
        vpn_bot_settings_serializer = VpnBotSettingsSerializer(vpn_bot_settings_obj, many=True).data
        return Response(vpn_bot_settings_serializer, status.HTTP_200_OK)
