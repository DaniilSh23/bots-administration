from django.contrib import admin

from service_desk_bot.models import ServDeskBotSettings


@admin.register(ServDeskBotSettings)
class ServDeskSettingsAdmin(admin.ModelAdmin):
    """
    Регистрация в админке модели для настроек Service Desk Bot
    """
    list_display = ('key', 'value')
    list_display_links = ('key', 'value')
