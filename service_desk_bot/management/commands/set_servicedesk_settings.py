from django.core.management import BaseCommand, CommandError
from loguru import logger
from service_desk_bot.models import ServDeskBotSettings


class Command(BaseCommand):
    """
    Команда для записи стандартных значений настроек в таблицу БД, за которую отвечает модель ServDeskBotSettings
    """

    def handle(self, *args, **options):
        logger.info('Старт команды по наполнению таблицы БД настройками для бота Service Desk')

        application_types = (
                ('У меня вопрос', 'Опишите более детально Ваш вопрос'),
                ('Создать нового пользователя', ''),
                ('Критическая проблема', 'Что привело к этой ошибке: опишите детально последовательность действий, '
                                         'укажите ссылку, например для 1С укажите базу, приложите скрин-шот. чем более '
                                         'подробно вы опишите свою проблему, тем быстрее она решится. '
                                         'DoD - как проверить, что проблема решена'),
                ('Другое', 'Что привело к этой ошибке: опишите детально последовательность действий, '
                           'укажите ссылку, например для 1С укажите базу, приложите скрин-шот. чем более '
                           'подробно вы опишите свою проблему, тем быстрее она решится. '
                           'DoD - как проверить, что проблема решена'),
            )

        for i_type, i_text in application_types:
            obj, created = ServDeskBotSettings.objects.get_or_create(
                key='application_type', value=f"{i_type}|{i_text}",
                defaults={
                    "key": "application_type",
                    "value": f"{i_type}|{i_text}",
                }
            )
            if created:
                logger.success(f'Добавлен application_type {i_type!r}')
            else:
                logger.info(f'Не был добавлен service_type {i_type!r} он уже есть в БД')

        service_types = (
                '1С',
                'Другое',
                'Битрикс 24',
                'Контур',
                'WhatsApp',
                'Google',
                'Телефония',
                'Сайт',
                'Ловец лидов',
            )

        for i_elem in service_types:
            obj, created = ServDeskBotSettings.objects.get_or_create(
                key='service_type', value=i_elem,
                defaults={
                    "key": "service_type",
                    "value": i_elem,
                }
            )
            if created:
                logger.success(f'Добавлен service_type {i_elem!r}')
            else:
                logger.info(f'Не был добавлен service_type {i_elem!r} он уже есть в БД')

        logger.info('Окончание команды по наполнению таблицы БД настройками для бота Service Desk')