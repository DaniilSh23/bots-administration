from django.contrib import admin

from vpn_bot.admin_mixins import ExportTlgUsersAsCSVMixin
from vpn_bot.models import TlgUser, VpnBotSettings


@admin.register(TlgUser)
class TlgUserAdmin(admin.ModelAdmin, ExportTlgUsersAsCSVMixin):
    """
    Регистрация модели TlgUser в админке.
    """
    actions = [
        'export_csv_for_dyatel_project',
    ]
    list_display = (
        "tlg_id",
        "first_name",
        "username",
        "is_verified",
        "is_scam",
        "is_fake",
    )
    list_display_links = (
        "tlg_id",
        "first_name",
        "username",
    )
    search_fields = "tlg_id", "first_name", "username"
    search_help_text = "Поиск по TG ID, TG имени, TG username"
    ordering = ['-id']
    fieldsets = [
        ('Основная информация', {
            "fields": ("tlg_id", "username", "first_name", "last_name"),
            "classes": ("wide", "extrapretty"),
            "description": "Основные данные о пользвателе Telegram.",
        }),
        ('Дополнительная информация', {
            'fields': ('is_verified', 'is_scam', 'is_fake', 'is_premium', 'language_code'),
            'classes': ('wide', 'collapse'),
            'description': 'Дополнительная информация о пользователе Telegram, '
                           'такая как: верификация, мошенничество и т.д.',
        })
    ]


@admin.register(VpnBotSettings)
class VpnBotSettingsAdmin(admin.ModelAdmin):
    """
    Регистрация в админке модели для настроек VPN_BOT
    """
    list_display = ('key', 'value')
    list_display_links = ('key', 'value')
