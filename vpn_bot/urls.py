from django.urls import path

from .views import TlgUserView, VpnBotAdminsView

app_name = 'vpn_bot'
urlpatterns = [
    path('tlg_user/', TlgUserView.as_view(), name='tlg_user'),
    path('vpn_bot_settings/', VpnBotAdminsView.as_view(), name='vpn_bot_settings'),
]
