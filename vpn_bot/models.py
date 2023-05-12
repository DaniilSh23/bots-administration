from django.db import models


class TlgUser(models.Model):
    """
    Модель пользователя телеграм.
    """
    tlg_id = models.CharField(verbose_name='TG ID', max_length=30)
    is_verified = models.BooleanField(verbose_name='Telegram его проверил', default=False)
    is_scam = models.BooleanField(verbose_name='Мошенник', default=False)
    is_fake = models.BooleanField(verbose_name='Выдаёт себя за другого', default=False)
    is_premium = models.BooleanField(verbose_name='Премиум', default=False)
    first_name = models.CharField(verbose_name='Имя(TG)', max_length=100, blank=True, null=False)
    last_name = models.CharField(verbose_name='Фамилия(TG)', max_length=100, blank=True, null=False)
    username = models.CharField(verbose_name='username(TG)', max_length=100, blank=True, null=False)
    language_code = models.CharField(verbose_name='языковой код(TG)', max_length=20, blank=True, null=False)

    def __str__(self):
        return f'Пользователь с TG ID: {self.tlg_id}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'пользователь TG'
        verbose_name_plural = 'пользователи TG'


class VpnBotSettings(models.Model):
    """
    Настройки для Vpn Bot.
    """
    key = models.CharField(verbose_name='Ключ', max_length=230)
    value = models.TextField(verbose_name='Значение', max_length=500)

    class Meta:
        ordering = ['-id']
        verbose_name = 'настройка VPN_BOT'
        verbose_name_plural = 'настройки VPN_BOT'
