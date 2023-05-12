import datetime
import json

import pytz
from loguru import logger

from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

from administration_of_bots.settings import TIME_ZONE
from registration_bot.MyBitrix23 import Bitrix23
from registration_bot.models import BotSettings
from service_desk_bot.forms import SendApplicationForm
from django.views.decorators.csrf import csrf_exempt

from service_desk_bot.models import ServDeskBotSettings


def get_filling_an_app(request):
    """
    Обработка GET запроса для формы подачи новой заявки.
    """
    if request.method == 'GET':

        application_type_objects = ServDeskBotSettings.objects.filter(key='application_type')
        applications_types = []
        placeholders = []
        for i_elem in application_type_objects:
            applications_types.append(i_elem.value.split('|')[0])
            placeholders.append(i_elem.value.split('|')[1])

        service_type_objects = ServDeskBotSettings.objects.filter(key='service_type')

        context = {
            'form': SendApplicationForm(),
            'application_types': applications_types,
            'placeholders': placeholders,
            'service_types': [i_elem.value for i_elem in service_type_objects],
        }

        # return render(request=request, template_name='service_desk_bot/filling_an_application.html')
        return render(request=request, template_name='service_desk_bot/send_application.html', context=context)


@csrf_exempt
def post_filling_an_app(request):
    """
    Обработка POST запроса для формы подачи новой заявки.
    """

    if request.method == 'POST':
        form = SendApplicationForm(request.POST, request.FILES)
        if form.is_valid():

            # Создаём инстанс битры
            bitra = Bitrix23(
                hostname=BotSettings.objects.get(key="subdomain").value,
                client_id=BotSettings.objects.get(key="client_id").value,
                client_secret=BotSettings.objects.get(key="client_secret").value,
                access_token=BotSettings.objects.get(key="access_token").value,
                refresh_token=BotSettings.objects.get(key="refresh_token").value,
                expires=BotSettings.objects.get(key="tokens_expires").value,
            )
            rslt = bitra.refresh_tokens()

            # Если метод отдал результат, то обновляем данные для Битры в БД
            if rslt:
                for i_key, i_value in rslt:
                    BotSettings.objects.update_or_create(key=i_key, defaults={
                        "key": i_key,
                        "value": i_value,
                    })

            # Получаем данные о юзере по tlg_id
            tlg_id = form.cleaned_data.get('tlg_id')
            method = 'user.get'
            params = {
                'UF_USR_1683828234089': tlg_id,
            }
            btrx_usr = bitra.call(method=method, params=params)

            if btrx_usr.get('result') and btrx_usr.get('result')[0].get('ACTIVE'):

                # Создаём задачу
                now_datetime = datetime.datetime.now(tz=pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M:%S')
                method = 'tasks.task.add'
                params = {
                    'fields': {
                        'TITLE': form.cleaned_data.get('title'),
                        'DESCRIPTION': form.cleaned_data.get('description'),
                        'GROUP_ID': 54,  # ID проекта "Тех.под"
                        'CREATED_BY': btrx_usr.get('result')[0].get('ID'),
                        'RESPONSIBLE_ID': 3,  # исполнитель всегда юзер с ID == 3
                        'UF_AUTO_712896860480': 0,  # ID сделки, всегда == 0
                        'UF_AUTO_234524460475': form.cleaned_data.get('application_type'),   # тип заявки
                        'UF_AUTO_208101803568': form.cleaned_data.get('service_type'),  # тип сервиса
                        'UF_AUTO_505612246987': now_datetime,
                    }
                }
                create_task_rslt = bitra.call(method=method, params=params)
                new_task_id = create_task_rslt.get('result').get('task').get('id')

                # Новая заявка упешно создана
                if new_task_id:
                    logger.success(f'Успешное создание новой заявки в Битрикс Тех.под. '
                                   f'ID задачи Битры(заявки) == {new_task_id}')
                    return render(request=request, template_name='service_desk_bot/success.html',
                                  context={'new_task_id': new_task_id})

                # Новая заявка не была создана
                else:
                    logger.warning(f'Не удалось создать задачу(новую заявку) в группе тех.под.\n'
                                   f'Ответ Битры: {create_task_rslt}')
                    return HttpResponse(f'Не удалось создать заявку. Проблема с Битриксом.', status=502)

            # Если юзера нет в Битриксе или он не активен
            else:
                logger.warning(f'Юзер с tlg_id == {tlg_id} не активен или не найден в Битриксе')
                return HttpResponse(content=f'Юзер с tlg_id == {tlg_id} не активен или не найден в Битриксе',
                                    status=403)

        # если данные запроса невалидны
        context = {'form': form}
        return render(request=request, template_name='service_desk_bot/send_application.html', context=context)


class CheckUserInBitrix(APIView):
    """
    Проверка, что юзер, стартовавший бота, есть в системе Битрикса и он активен.
    Также запись ему TG ID в профиль.
    """

    def post(self, request):
        """
        Обработка POST запроса.
        Принимает параметры tlg_username и tlg_id.
        Проверяем наличие и активность юзера в Битриксе по tlg_username и,
        при успешной проверке, записываем ему в профиль tlg_id.
        Статус коды ответов: 400 - неверный запрос, стоит также проверить параметры запроса,
        403 - юзер не прошёл проверку и не может получить доступ к боту, 502 - неудачный запрос к API Битрикса,
        200 - юзер успешно прошёл проверку.
        """

        if request.data.get('tlg_username') and request.data.get('tlg_id'):

            tlg_username, tlg_id = request.data.get('tlg_username'), request.data.get('tlg_id')

            # Создаём инстанс битры
            bitra = Bitrix23(
                hostname=BotSettings.objects.get(key="subdomain").value,
                client_id=BotSettings.objects.get(key="client_id").value,
                client_secret=BotSettings.objects.get(key="client_secret").value,
                access_token=BotSettings.objects.get(key="access_token").value,
                refresh_token=BotSettings.objects.get(key="refresh_token").value,
                expires=BotSettings.objects.get(key="tokens_expires").value,
            )
            rslt = bitra.refresh_tokens()

            # Если метод отдал результат, то обновляем данные для Битры в БД
            if rslt:
                for i_key, i_value in rslt:
                    BotSettings.objects.update_or_create(key=i_key, defaults={
                        "key": i_key,
                        "value": i_value,
                    })

            # Получаем данные о юзере
            method = 'user.get'
            params = {
                'UF_USR_1679923976413': tlg_username,
            }
            method_rslt = bitra.call(method=method, params=params)

            if method_rslt.get('result') and method_rslt.get('result')[0].get('ACTIVE'):
                logger.success(f'Успешная проверка юзера tlg_username == {tlg_username} в Битриксе (ServiceDeskBot)')

                # Записываем в профиль юзера TG ID
                method = 'user.update'
                params = {
                    'ID': method_rslt.get('result')[0].get('ID'),
                    'UF_USR_1683828234089': tlg_id,
                }
                method_rslt = bitra.call(method=method, params=params)

                # Обработка успешного обновления профиля
                if method_rslt.get('result'):
                    logger.success(f'Успешная запись tlg_id == {tlg_id} в профиль юзера Битрикс с '
                                   f'tlg_username == {tlg_username} (ServiceDeskBot)')
                    return Response(
                        data=f'Успешная проверка юзера с tlg_username == {tlg_username}',
                        status=status.HTTP_200_OK
                    )
                # Неудачное обновление профиля
                else:
                    logger.warning(f'Не удалось обновить в Битриксе профиль юзера с tlg_username == {tlg_username} '
                                   f'(ServiceDeskBot)')
                    return Response(
                        data=f'Не удалось обновить в Битриксе профиль юзера с tlg_username == {tlg_username}',
                        status=status.HTTP_502_BAD_GATEWAY
                    )

            # Юзер не найден в Битриксе
            logger.warning(f'Юзер с tlg_username == {request.data.get("tlg_username")} не найден в Битриксе.'
                           f'Ответ Битрикса: {method_rslt}(Service Desk Bot)')
            return Response({'result': 'Юзер не найден в Битриксе'}, status=status.HTTP_403_FORBIDDEN)

        # Неверные параметры запроса
        logger.warning(f'Отсутствует параметр tlg_username или tlg_id в запросе на проверку активности и '
                       f'наличия юзера в Битриксе.(Service Desk Bot)')
        return Response({'result': 'Неверные параметры запроса'},
                        status.HTTP_400_BAD_REQUEST)


class NewFormSettings(APIView):
    def post(self, request):
        """
        Установка новых значений для типа заявки, типа сервиса и placeholder'а
        """


def test_page(request):
    new_task_id = '1234567'
    return render(request=request, template_name='service_desk_bot/success.html',
                  context={'new_task_id': new_task_id})


class TestBitrixMethod(APIView):
    """Какой-либо метод битрикса"""

    def get(self, request, format=None):
        """Вьюшка для выполнения какого-либо метода АПИ Битрикса"""

        # Создаём инстанс битры
        bitra = Bitrix23(
            hostname=BotSettings.objects.get(key="subdomain").value,
            client_id=BotSettings.objects.get(key="client_id").value,
            client_secret=BotSettings.objects.get(key="client_secret").value,
            access_token=BotSettings.objects.get(key="access_token").value,
            refresh_token=BotSettings.objects.get(key="refresh_token").value,
            expires=BotSettings.objects.get(key="tokens_expires").value,
        )
        rslt = bitra.refresh_tokens()

        # Если метод отдал результат, то обновляем данные для Битры в БД
        if rslt:
            for i_key, i_value in rslt:
                BotSettings.objects.update_or_create(key=i_key, defaults={
                    "key": i_key,
                    "value": i_value,
                })

        # Получаем юзера
        method = 'user.get'
        params = {
            'UF_USR_1679923976413': "DanyaSevas",
        }

        # Получаем данные о юзере по tlg_id
        method = 'user.get'
        params = {
            'UF_USR_1683828234089': 1978222333,
        }
        method_rslt = bitra.call(method=method, params=params)

        # # Обновляем профиль юзера
        # method = 'user.update'
        # params = {
        #     'ID': 105,
        #     'UF_USR_1683828234089': 1978111111,
        # }

        # Создаём задачу
        method = 'tasks.task.add'
        params = {
            'fields': {
                'TITLE': 'название заявки',
                'DESCRIPTION': 'описание заявки',
                'GROUP_ID': 54,  # ID проекта "Тех.под"
                'CREATED_BY': 105,
                'RESPONSIBLE_ID': 3,  # исполнитель всегда юзер с ID == 3
                'UF_AUTO_712896860480': 0,  # ID сделки, всегда == 0
                'UF_AUTO_234524460475': 'тип заявки',
                'UF_AUTO_208101803568': 'тип сервиса',
                'UF_AUTO_505612246987': datetime.datetime.now(tz=pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M:%S')
            }
        }

        method_rslt = bitra.call(method=method, params=params)
        print(method_rslt)
        return HttpResponse(f'{json.dumps(method_rslt, indent=4, ensure_ascii=False)}')
