from django.db import models


class ServDeskBotSettings(models.Model):
    """
    Настройки для Service Desk Bot.
    """
    key = models.CharField(verbose_name='Ключ', max_length=230)
    value = models.TextField(verbose_name='Значение', max_length=500)

    class Meta:
        ordering = ['-id']
        verbose_name = 'настройка Service Desk Bot'
        verbose_name_plural = 'настройки Service Desk Bot'

