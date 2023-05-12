from django.contrib import admin

from registration_bot.models import BotUsers, CompanyData, BankData, BotSettings, BotRatings, Reminders


class BotUsersAdmin(admin.ModelAdmin):
    """Регистрация модели BotUsers в админке"""

    list_display = (
        'tlg_id',
        'consent_to_pers_data',
        'consent_datetime',
        'tlg_username',
        'telephone',
        'email',
        'deal_id',
        'chat_for_deal_id',
        'start_at',
        'is_staff',
    )
    list_display_links = (
        'tlg_id',
        'consent_to_pers_data',
        'consent_datetime',
        'tlg_username',
        'telephone',
        'email',
        'deal_id',
        'chat_for_deal_id',
        'start_at',
        'is_staff',
    )
    search_fields = ('deal_id', 'consent_to_pers_data', 'consent_datetime', 'telephone', 'email', 'tlg_username',
                     'chat_for_deal_id')
    search_help_text = 'Поиск по: согласию обраб. перс. данных, ID сделки, ID откр.линии, телефону, ' \
                       'email, username телеграм'
    list_filter = ('is_staff', 'consent_to_pers_data')


class CompanyDataAdmin(admin.ModelAdmin):
    """Регистрация модели CompanyData в админке"""

    list_display = (
        'comp_name',
        'address',
        'ogrn',
        'inn',
        'top_management_post',
        'top_management_name',
        'requisite_id',
        'user',
    )
    list_display_links = (
        'comp_name',
        'address',
        'ogrn',
        'inn',
        'top_management_post',
        'top_management_name',
        'requisite_id',
        'user',
    )
    search_fields = ('comp_name', 'ogrn', 'inn', 'top_management_name')
    search_help_text = 'Поиск по: названию компании, ОГРН, ИНН, ФИО управляющего лица'


class BankDataAdmin(admin.ModelAdmin):
    """Регистрация модели BankData в админке"""

    list_display = (
        'bik',
        'rs',
        'cor_a',
        'bank_name',
        'company',
    )
    list_display_links = (
        'bik',
        'rs',
        'cor_a',
        'bank_name',
        'company',
    )
    search_fields = ('bik', 'rs', 'cor_a', 'bank_name')
    search_help_text = 'Поиск по: БИК, РС, Кор.счёт, название банка'
    list_filter = ('company',)


class BotSettingsAdmin(admin.ModelAdmin):
    """Регистрация модели BotSettings в админке."""

    list_display = ('key', 'value')
    list_display_links = ('key', 'value')
    search_fields = ('key', 'value')
    search_help_text = 'Поиск по обоим полям'


class BotRatingAdmin(admin.ModelAdmin):
    """Регистрация модели BotRatings в админке."""

    list_display = ('user', 'rating', 'created_at', 'comment')
    list_display_links = ('user', 'rating', 'created_at', 'comment')
    search_fields = ('user', 'rating', 'created_at', 'comment')
    search_help_text = 'Поиск по всем полям'


class RemindersAdmin(admin.ModelAdmin):
    """Регистрация модели Reminders в админке."""

    list_display = ('user', 'reminder_type', 'proc_id')
    list_display_links = ('user', 'reminder_type', 'proc_id')
    search_fields = ('user', 'reminder_type', 'proc_id')
    search_help_text = 'Поиск по всем полям'


admin.site.register(BotUsers, BotUsersAdmin)
admin.site.register(CompanyData, CompanyDataAdmin)
admin.site.register(BankData, BankDataAdmin)
admin.site.register(BotSettings, BotSettingsAdmin)
admin.site.register(BotRatings, BotRatingAdmin)
admin.site.register(Reminders, RemindersAdmin)
