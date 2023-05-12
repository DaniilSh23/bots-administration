import datetime
import http
import json
import random
from loguru import logger
import requests
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt  # Декоратор для отключения CSRF защиты(надо для запросов AJAX)

from registration_bot.MyBitrix23 import Bitrix23
from registration_bot.models import BotUsers, CompanyData, BankData, BotSettings, BotRatings
from registration_bot.serializers import BotUsersSerializer, CompanyDataSerializer, BankDataSerializer, \
    SendMsgToOLSerializer, FormLinkSerializer
from registration_bot.tasks import get_pdf_doc_from_btrx


class BotUsersView(APIView):
    """Представление для работы с моделью BotUsers"""

    def get(self, request, format=None):
        """
        Обработка GET запроса:
            ?tlg_id=.. - получение данных об одном пользователе по tlg_id
        """
        tlg_id = request.query_params.get('tlg_id')
        if tlg_id and tlg_id.isdigit():
            try:
                bot_user_obj = BotUsers.objects.get(tlg_id=tlg_id)
            except Exception:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            bot_user_serializer = BotUsersSerializer(bot_user_obj, many=False).data
            return Response(bot_user_serializer, status.HTTP_200_OK)

    def post(self, request, format=None):
        """
        Обработчик POST запроса.
        """
        # {"tlg_id": "9999999999", "deal_id": "99999"}
        # {"tlg_id": "9999999999", "tlg_username": "DanyaSevas", "deal_id": "99999"}
        logger.info(f'Данные из POST запроса в BotUsersView: \n\t{request.data}')
        serializer = BotUsersSerializer(data=request.data)
        if serializer.is_valid():
            users_lst_for_this_deal = BotUsers.objects.filter(deal_id=request.data.get('deal_id'))
            logger.info(f'Список пользователей с deal_id == {request.data.get("deal_id")}:\n\t{users_lst_for_this_deal}')
            if len(users_lst_for_this_deal) > 0:    # Если с этой сделкой есть другие пользователи
                for i_user in users_lst_for_this_deal:
                    if str(i_user.tlg_id) != str(request.data.get('tlg_id')):     # Проверка, что tlg_id у пользователя другой
                        logger.info(f'TG ID юзера для удаления == {str(i_user.tlg_id)}, '
                                    f'TG ID юзера, который должен остаться == {str(request.data.get("tlg_id"))}')
                        logger.info(f'Удаляем пользователя с TG ID == {i_user.tlg_id}, '
                                    f'связанного со сделкой deal_id=={request.data.get("deal_id")}')
                        i_user.delete()     # Удаляем пользователя
            bot_user_object = BotUsers.objects.update_or_create(
                tlg_id=serializer.data.get("tlg_id"),
                defaults=serializer.data
            )
            result_object = BotUsersSerializer(bot_user_object[0], many=False).data
            return Response(result_object, status.HTTP_200_OK)
        else:
            return Response({'result': 'Переданные данные не прошли валидацию'}, status.HTTP_400_BAD_REQUEST)


class CompanyDataView(APIView):
    """Вьюха для работы с моделью CompanyData"""

    def get(self, request, format=None):
        """
        Обработка GET запроса.
            ?tlg_id=.. - получение компании клиента по TG ID
        """
        tlg_id = request.query_params.get('tlg_id')
        if tlg_id and str(tlg_id).isdigit():
            try:
                company_obj = CompanyData.objects.get(user__tlg_id=tlg_id)
            except Exception:
                return Response({'result': 'Данные не найдены'}, status=status.HTTP_400_BAD_REQUEST)
            company_serializer = CompanyDataSerializer(company_obj, many=False).data
            return Response(company_serializer, status.HTTP_200_OK)
        return Response({'result': 'неверные параметры запроса.'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        """
        Обработка POST запроса. В запросе параметр user - это TG ID пользователя(int).
        """
        # {"comp_name": "ООО РОГА И КОПЫТА", "address": "какой-то там адрес", "ogrn": "1111111111111",
        #  "inn": "2222222222", "top_management_post": "top manager", "top_management_name": "Ivan Vasilyevich",
        #  "user": 1978587604}
        tlg_id = request.data.get('user')
        if str(tlg_id).isdigit():
            user_obj = BotUsers.objects.get(tlg_id=tlg_id)
        else:
            return Response({'result': 'Передан неверный TG ID пользователя.'}, status.HTTP_400_BAD_REQUEST)

        serializer = CompanyDataSerializer(data=request.data)
        if serializer.is_valid():
            comp_lst = CompanyData.objects.filter(user=user_obj)
            for i_comp in comp_lst:  # Удаляем все остальные компании, которые записаны за этим пользователем
                if i_comp.user == user_obj:
                    i_comp.delete()
            company_obj = CompanyData.objects.update_or_create(
                inn=serializer.data.get('inn'),
                defaults={
                    'comp_name': serializer.data.get('comp_name'),
                    'address': serializer.data.get('address'),
                    'ogrn': serializer.data.get('ogrn'),
                    'inn': serializer.data.get('inn'),
                    'top_management_post': serializer.data.get('top_management_post'),
                    'top_management_name': serializer.data.get('top_management_name'),
                    'user': user_obj,
                }
            )
            return Response(status.HTTP_200_OK)
        else:
            return Response({'result': 'Переданные данные не прошли валидацию'}, status.HTTP_400_BAD_REQUEST)


class BankDataView(APIView):
    """Вьюха для работы с моделью BankData"""

    def get(self, request, format=None):
        """
        Обработка GET запроса.
            ?inn - получение одной записи по ИНН компании
        """
        inn = request.query_params.get('inn')
        if inn and inn.isdigit():
            try:
                bank_obj = BankData.objects.get(company__inn=inn)
            except Exception:
                return Response({'result': 'Данные не найдены'}, status=status.HTTP_400_BAD_REQUEST)
            bank_serializer = BankDataSerializer(bank_obj, many=False).data
            return Response(bank_serializer, status.HTTP_200_OK)
        return Response({'result': 'неверные параметры запроса.'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        """
        Обработка POST запроса.
        """
        inn = request.data.get('inn_comp')
        if inn.isdigit():
            company_obj = CompanyData.objects.get(inn=inn)
        else:
            return Response({'result': 'Передан неверный ИНН компании.'}, status.HTTP_400_BAD_REQUEST)

        serializer = BankDataSerializer(data=request.data)
        if serializer.is_valid():
            bank_obj = BankData.objects.update_or_create(
                company=company_obj,
                defaults={
                    'bik': serializer.data.get('bik'),
                    'rs': serializer.data.get('rs'),
                    'cor_a': serializer.data.get('cor_a'),
                    'bank_name': serializer.data.get('bank_name'),
                    'company': company_obj,
                }
            )
            return Response(status.HTTP_200_OK)
        else:
            return Response({'result': 'Переданные данные не прошли валидацию'}, status.HTTP_400_BAD_REQUEST)


'''Views для локального приложения Битрикс'''


@csrf_exempt
def start_bitrix(request: WSGIRequest):
    """Вьюшка для старта приложения Битрикс"""

    if request.method == 'POST':
        # Сохраняем access_token и refresh_token в БД
        BotSettings.objects.update_or_create(
            key='access_token',
            defaults={
                'key': 'access_token',
                'value': request.POST.get("auth[access_token]")
            }
        )
        BotSettings.objects.update_or_create(
            key='refresh_token',
            defaults={
                'key': 'refresh_token',
                'value': request.POST.get("auth[refresh_token]")
            }
        )
        BotSettings.objects.update_or_create(
            key='tokens_expires',
            defaults={
                'key': 'tokens_expires',
                'value': request.POST.get("auth[expires]")
            }
        )
        logger.info(f'НОВЫЙ АКСЕС И РЕФРЕШ ТОКЕНЫ: {request.POST.get("auth[access_token]"), request.POST.get("auth[refresh_token]")}')
        return HttpResponse(f'Success', status=http.HTTPStatus.OK)


@csrf_exempt
def common_bitrix(request: WSGIRequest):
    """Вьюшка для получения запросов от Битрикса"""

    if request.method == 'POST':
        """POST запрос поступает, когда клиент заполняет форму с персональными данными."""

        deal_id = request.GET.get('id')     # Запрос-то POST, но параметр лежит в URL адресе, поэтому поступаем хитро
        # Фиксируем согласие на обработку персональных данных в админке
        action_rslt = BotUsers.objects.update_or_create(
            deal_id=deal_id,
            defaults={"consent_to_pers_data": True, "consent_datetime": datetime.datetime.now()}
        )
        user_obj = action_rslt[0]   # [объект модели БД, True/False о создании новой записи в БД]
        # Посылаем пользователю бота ответ на заполнение ПД (бот отредактирует ответ и добавит к нему кнопки)
        bot_token = BotSettings.objects.get(key='bot_token').value
        bot_snd_trigger_rslt = requests.post(
            url=f'https://api.telegram.org/bot{bot_token}/sendMessage',
            data={
                'chat_id': user_obj.tlg_id,
                # Это сообщение - триггер для бота, должно быть именно таким
                'text': '*_successful_recording_of_personal_data_*',
            }
        )
        if bot_snd_trigger_rslt.json().get('ok'):
            logger.success('Успешная отправка боту триггера о записи перс.данных клиента')
            return HttpResponse({"Окей, спасибо, запрос принят"}, status=http.HTTPStatus.OK)
        else:
            logger.critical(f'Отправка триггера боту не удалась! Ответ телеграма\n{bot_snd_trigger_rslt.json()}')
            return HttpResponse({"Телеграм дал ошибку. Текст ответа телеграма в логах"}, status=http.HTTPStatus.BAD_REQUEST)

    elif request.method == 'POST':
        print(request.POST)
        return HttpResponse(status=http.HTTPStatus.OK)


class WorkWthOL(APIView):
    """Вьюшка для работы с чатом для сделки"""

    def get(self, request, format=None):
        """
        Обработка GET запроса.
        Создаём новый чат для сделки, в котором будем "логировать" действия пользователей с ботом.
        Это нужно бухгалтерам и продавцам.
            ?tlg_id - TG ID пользователя
        """

        tlg_id = request.query_params.get('tlg_id')
        if tlg_id and tlg_id.isdigit():
            deal_id = BotUsers.objects.get(tlg_id=tlg_id).deal_id

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

            user_obj = BotUsers.objects.get(tlg_id=tlg_id)

            # Получаем сделку и достаём из неё ответственного, а также название
            method = 'crm.deal.get'
            params = {'id': user_obj.deal_id}
            method_rslt = bitra.call(method=method, params=params)
            manager_id = method_rslt['result'].get('ASSIGNED_BY_ID')  # Ответственный за сделку (ID)
            deal_name = method_rslt['result'].get('TITLE')  # Наименование сделки

            # Создание чата
            chat_color = random.choice(['RED', 'GREEN', 'MINT', 'LIGHT_BLUE', 'DARK_BLUE', 'PURPLE', 'AQUA', 'PINK',
                                        'LIME', 'BROWN', 'AZURE', 'KHAKI', 'SAND', 'MARENGO', 'GRAY', 'GRAPHITE'])
            method = 'im.chat.add'
            params = {
                'TYPE': 'CHAT',
                'TITLE': f'(REG.BOT)"{deal_name}"',
                'DESCRIPTION': f'Действия клиента с ботом-регистратором по сделке {deal_name}',
                'COLOR': chat_color,
                'MESSAGE': 'Клиент запустил бота по специальной ссылке.',
                'USERS': [32698, manager_id],
                # 'ENTITY_TYPE': 'CHAT',
                # 'ENTITY_ID' = > 13,
                # 'OWNER_ID' = > 39,
            }
            method_rslt = bitra.call(method=method, params=params)
            # Записываем ID созданного чата в BotUsers
            if str(method_rslt.get("result")).isdigit():
                logger.info(f'Успешное создание чата для сделки с ID {deal_id}')
                bot_user_obj = BotUsers.objects.update_or_create(
                    tlg_id=tlg_id,
                    defaults={
                        "chat_for_deal_id": method_rslt.get("result")
                    }
                )
                return Response(
                    {f'CHAT ID for deal {deal_id}': bot_user_obj[0].chat_for_deal_id},
                    status.HTTP_200_OK
                )
            else:
                logger.critical(f'Не был создан чат для сделки с ID {deal_id}.\nОтвет битрикса:\n\t{method_rslt}')
                return Response({'Not create chat for deal. Bitrix answer': f'{method_rslt}'},
                                status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning(f'Данные не прошли валидацию в методе по созданию чата для сделки')
            return Response({'result': 'Переданные данные не прошли валидацию или мало параметров'},
                            status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        """
        Обработка POST запроса.
        Отправка сообщения о действиях пользователя с ботом в чат битрикса.
        Параметры запроса:
            tlg_id - (int, max_value=9999999999) TG ID пользователя
            username - (str, max_length=400) TG username пользователя (опционально)
            last_name - (str, max_length=400) TG last_name пользователя (опционально)
            name - (str, max_length=400) TG first_name пользователя (опционально)
            msg_text - (str, max_length=5000) текст сообщения пользователя в чате с ботом
        """

        # {"tlg_id": 1978587604, "last_name": "Shestakov", "name": "Daniil", "msg_text": "/Test message from reg bot/"}

        # Принимаем и проверяем параметры POST запроса
        serializer = SendMsgToOLSerializer(data=request.data)
        if serializer.is_valid():
            # Берём объект нужного пользователя из БД
            bot_user_obj = BotUsers.objects.get(tlg_id=serializer.data.get('tlg_id'))

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

            # Отправляем сообщение в чат битрикса
            tlg_username = serializer.data.get('username')
            tlg_firstname = serializer.data.get('name')
            tlg_lastname = serializer.data.get('last_name')
            msg_text = serializer.data.get('msg_text')
            bitrix_subdomain = BotSettings.objects.get(key='subdomain')

            method = 'im.message.add'
            params = {
                'DIALOG_ID': f'chat{bot_user_obj.chat_for_deal_id}',
                'MESSAGE': 'АКТИВНОСТЬ В БОТЕ-РЕГИСТРАТОРЕ\n\n'
                           'О клиенте:\n'
                           f'\tID сделки: {bot_user_obj.deal_id}\n'
                           f'\tСсылка на сделку: https://{bitrix_subdomain}/crm/deal/details/{bot_user_obj.deal_id}/\n'
                           f'\tTelegram ID клиента: {bot_user_obj.tlg_id}\n'
                           f'\tTelegram username клиента: {tlg_username}\n'
                           f'\tИмя (из профиля Telegram): {tlg_firstname}\n'
                           f'\tФамилия (из профиля Telegram): {tlg_lastname}\n\n'
                           f'----------------------------------\n\n'
                           f'Действие:\n\n\t{msg_text}'
            }
            method_rslt = bitra.call(method=method, params=params)
            logger.info(f'Отправлен запрос для отправки сообщения в чат для бота. Ответ битрикс:\n\n\t{method_rslt}')
            if str(method_rslt.get('result')).isdigit():  # Если сообщение было успешно отправлено
                logger.success('Успешная отправка сообщения в чат бота в Битриксе.')
                return Response({'Successful send message to bitrix chat.'}, status.HTTP_200_OK)
            else:  # Если сообщение не отправлено
                logger.critical(f'Не удалось отправить сообщение в чат бота для сделки с ID {bot_user_obj.deal_id}')
                return Response(
                    {'Send msg error. Bitrix answer': method_rslt},
                    status.HTTP_400_BAD_REQUEST
                )
        else:  # Если данные из запроса не прошли валидацию
            logger.warning(f'Данные не прошли валидацию при вызове метода отправки сообщения в чат бота (Битрикс)')
            return Response({'Request data is not valid! Your request data': request.data}, status.HTTP_400_BAD_REQUEST)


class WorkWthDeal(APIView):
    """Вьюшка для работы со сделкой в Битриксе"""

    def get(self, request, format=None):
        """
        Обработка GET запроса.
        Здесь создаём компанию, реквизит, банковский реквизит и привязываем всё это дело к сделке.
            ?tlg_id - TG ID пользователя
        """
        tlg_id = request.query_params.get('tlg_id')
        if str(tlg_id).isdigit():  # Проверочка, что tlg_id - это цифры
            # Достаём из БД данные о компании и реквизитах
            user_obj = BotUsers.objects.get(tlg_id=tlg_id)
            company_obj = CompanyData.objects.get(user=user_obj)
            bank_detail_obj = BankData.objects.get(company=company_obj)

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
            # Получаем сделку и достаём из неё ответственного
            method = 'crm.deal.get'
            params = {'id': user_obj.deal_id}
            method_rslt = bitra.call(method=method, params=params)
            deal_assigned_by_id = method_rslt['result'].get('ASSIGNED_BY_ID')

            # Проверяем наличие компании в системе.
            # Достаём список реквизитов и фильтруем по ИНН, вытягиваем айдишник компании
            method = 'crm.requisite.list'
            params = {
                'order': {"DATE_CREATE": "ASC"},
                'filter': {"RQ_INN": company_obj.inn, 'ENTITY_TYPE_ID': 4},
                'select': ['ID', 'ENTITY_ID']
            }
            comp_req_lst = bitra.call(method=method, params=params)

            # Создаём или обновляем компанию в Битриксе
            params = {
                    'fields': {
                        "TITLE": company_obj.comp_name,
                        "COMPANY_TYPE": "CUSTOMER",
                        "INDUSTRY": "MANUFACTURING",
                        "EMPLOYEES": "EMPLOYEES_2",
                        "CURRENCY_ID": "RUB",
                        "HAS_PHONE": 'Y',
                        "HAS_EMAIL": 'Y',
                        'EMAIL': [{"VALUE": user_obj.email, "VALUE_TYPE": "WORK"}],
                        "PHONE": [{"VALUE": user_obj.telephone, "VALUE_TYPE": "WORK"}],
                        'IM': [{'VALUE': user_obj.chat_for_deal_id, 'VALUE_TYPE': 'CHAT'}],
                        "OPENED": "Y",
                        "ASSIGNED_BY_ID": deal_assigned_by_id,  # Ответственный в сделке
                    }
                }
            if comp_req_lst.get('total') != 0:  # Если реквизиты с ИНН компании есть в системе
                logger.info('ИНН компании найден в Битриксе. Данные компании будут обновлены.')
                method = 'crm.company.update'
                comp_id = comp_req_lst['result'][0].get('ENTITY_ID')
                params['id'] = comp_id
            else:   # Если реквизитов с ИНН компании нет в системе
                logger.info('ИНН компании НЕ найден в Битриксе. Компания будет создана.')
                method = 'crm.company.add'
                comp_id = None
            comp_crt_rslt = bitra.call(     # Кидаем запрос на создание или обновление компании в Битриксе
                method=method,
                params=params
            )
            if comp_crt_rslt.get('result'):
                # Создаём или обновляем в Битре реквизит и привязываем к компании
                if company_obj.comp_name.upper().startswith('ИП '):     # Параметры реквизита для ИП
                    ip_fst_name = company_obj.comp_name.split()[1]
                    ip_lst_name = company_obj.comp_name.split()[2]
                    ip_sec_name = company_obj.comp_name.split()[3] if len(company_obj.comp_name.split()) == 4 else None
                    params = {
                        'fields': {
                            "ENTITY_TYPE_ID": 4,
                            "ENTITY_ID": comp_crt_rslt['result'] if not comp_id else comp_id,   # ID компании
                            "PRESET_ID": 3,  # 3 - айдишник шаблона реквизита для ООО
                            "NAME": f"Реквизит компании {company_obj.comp_name}",
                            "ACTIVE": "Y",
                            "RQ_FIRST_NAME": ip_fst_name,  # Имя ИП
                            "RQ_LAST_NAME": ip_lst_name,  # Фамилия ИП
                            "RQ_SECOND_NAME": ip_sec_name,  # Отчество ИП
                            "RQ_OGRNIP": company_obj.ogrn,  # ОГРН компании ИП
                            "RQ_INN": company_obj.inn,  # ИНН компании
                            "RQ_COMPANY_FULL_NAME": company_obj.comp_name,
                        }
                    }
                else:   # Параметры реквизита для ООО
                    params = {
                        'fields': {
                            "ENTITY_TYPE_ID": 4,
                            "ENTITY_ID": comp_crt_rslt['result'] if not comp_id else comp_id,  # Это ID компании
                            "PRESET_ID": 1,  # 1 - айдишник шаблона реквизита для ООО
                            "NAME": f"Реквизит компании {company_obj.comp_name}",
                            "ACTIVE": "Y",
                            "RQ_OGRN": company_obj.ogrn,  # ОГРН компании ООО
                            "RQ_INN": company_obj.inn,  # ИНН компании
                            "RQ_COMPANY_FULL_NAME": company_obj.comp_name,  # хз, полное название компании?
                            "RQ_COMPANY_NAME": company_obj.comp_name,
                            "RQ_DIRECTOR": company_obj.top_management_name,
                            "UF_CRM_1573048471": company_obj.top_management_post,  # Вроде должность управляющего
                        }
                    }
                if comp_req_lst.get('total') != 0:  # Если реквизиты с ИНН компании есть в системе
                    logger.info('ИНН компании найден в Битриксе. Реквизит компании будет удалён и создан заново.')
                    # TODO: по-хорошему, сделать бы проверку, что удаление было успешным
                    bitra.call(method='crm.requisite.delete', params={'id': comp_req_lst['result'][0].get('ID')})
                logger.info('Создаём реквизит компании')
                method = 'crm.requisite.add'
                crt_req_rslt = bitra.call(
                    method=method,
                    params=params
                )
                if crt_req_rslt['result']:
                    # Записываем ID реквизита в таблицу компаний
                    CompanyData.objects.update_or_create(
                        inn=company_obj.inn,
                        defaults={'requisite_id': crt_req_rslt['result']}
                    )
                    # Создаём адрес и привязываем к реквизиту
                    params = {
                        'fields': {
                            "TYPE_ID": 6,  # Тип адреса (1 - фактический, 6 - юридический)
                            "ENTITY_TYPE_ID": 8,  # ID род. сущности (8 - реквизит, 4 - компания)
                            "ENTITY_ID": crt_req_rslt['result'],  # ID реквизита
                            "ADDRESS_1": company_obj.address,
                        }
                    }
                    method = 'crm.address.add'
                    crt_ads_rslt = bitra.call(
                        method=method,
                        params=params
                    )
                    if crt_ads_rslt['result']:
                        # Создаём реквизит банка
                        crt_bnk_detail_rslt = bitra.call(
                            method='crm.requisite.bankdetail.add',
                            params={
                                'fields': {
                                    "ENTITY_ID": crt_req_rslt['result'],
                                    "COUNTRY_ID": 1,  # Это знач.было в возврате метода по пресетам реквизитов
                                    "NAME": f"Реквизит банка компании {company_obj.comp_name} из сделки ID {user_obj.deal_id}",
                                    "ACTIVE": "Y",
                                    "RQ_BANK_NAME": bank_detail_obj.bank_name,  # Название банка
                                    "RQ_BIK": bank_detail_obj.bik,
                                    "RQ_ACC_NUM": bank_detail_obj.rs,  # Расчётный счёт
                                    "RQ_COR_ACC_NUM": bank_detail_obj.cor_a,  # Кор.счёт
                                    "RQ_ACC_CURRENCY": "RUB",  # Валюта счёта
                                }
                            }
                        )
                        if str(crt_bnk_detail_rslt['result']).isdigit():
                            # Обновляем сделку и привязываем к ней компанию
                            update_deal_rslt = bitra.call(
                                method='crm.deal.update',
                                params={
                                    'id': user_obj.deal_id,
                                    'fields': {
                                        'COMPANY_ID': comp_crt_rslt['result'] if not comp_id else comp_id
                                    }
                                }
                            )
                            if update_deal_rslt.get('result'):
                                return Response(
                                    {
                                        'All operations result': 'Success',
                                        'Create or update company bitrix answer': comp_crt_rslt,
                                        'Create requisite bitrix answer': crt_req_rslt,
                                        'Create bank detail bitrix answer': crt_bnk_detail_rslt,
                                        'Deal update bitrix answer': update_deal_rslt,
                                        'Thanks! Use our airlines. And sorry меня за мой bad english': '..please'
                                    },
                                    status.HTTP_200_OK
                                )
                            else:  # Неудачное обновление сделки
                                logger.warning('Неудачное обновление сделки')
                                return Response(
                                    {'Bad result for deal update. Bitrix answer': update_deal_rslt},
                                    status.HTTP_400_BAD_REQUEST
                                )
                        else:  # Неудачное создание реквизитов банка
                            logger.warning('Неудачное создание реквизитов банка')
                            return Response(
                                {'Bad result for create bank details. Bitrix answer': crt_bnk_detail_rslt},
                                status.HTTP_400_BAD_REQUEST
                            )
                    else:  # Неудачное создание адреса для реквизита
                        logger.warning('Неудачное создание адреса для реквизита')
                        return Response(
                            {'Bad result for create address. Bitrix answer': crt_ads_rslt},
                            status.HTTP_400_BAD_REQUEST
                        )
                else:  # Неудачное создание реквизита
                    logger.warning('Неудачное создание реквизита')
                    return Response(
                        {'Bad result for create requisite': crt_req_rslt},
                        status.HTTP_400_BAD_REQUEST
                    )
            else:  # Неудачное создание компании
                return Response(
                    {'Bad result for create company': comp_crt_rslt},
                    status.HTTP_400_BAD_REQUEST
                )
        else:  # Параметр запроса tlg_id не прошёл проверку
            return Response(
                {'Request params is not valid'},
                status.HTTP_400_BAD_REQUEST
            )

    def post(self, request, format=None):
        """
        Обработка POST запроса.
        Принимаем ID с товарными позициями и добавляем их в сделку.
        Параметры запроса:
            products - str, <fst_prod_id:numb,sec_prod_id:numb,...> ID товаров и их количество в виде строки
            tlg_id - int, TG ID пользователя
        """

        # Для теста POST запроса
        # {"tlg_id": 1978587604, "products": "1474:1,1498:23"}

        # Делаем список из пришедшей в запросе строки с ID товаров и количеством
        products_id_lst = request.data.get('products').split(',')
        tlg_id = request.data.get('tlg_id')
        check_prod_data = [True if i_elem.split(':')[0].isdigit() and i_elem.split(':')[1].isdigit() else False
                           for i_elem in products_id_lst]
        if str(tlg_id).isdigit and all(check_prod_data):
            # Достаём из БД ID сделки
            deal_id = BotUsers.objects.get(tlg_id=tlg_id).deal_id

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

            # Добавляем товары в сделку
            products_rows = []
            for i_elem in products_id_lst:
                prod_id = int(i_elem.split(':')[0])  # Значение параметра PRODUCT_ID
                quantity = int(i_elem.split(':')[1])  # Значение параметра QUANTITY
                # Запрос к Битриксу для получения цены товара
                method = 'crm.product.get'
                params = {'id': prod_id}
                get_prod_rslt = bitra.call(method=method, params=params)
                if get_prod_rslt['result'].get('PRICE'):  # Если цена была в ответе битрикса
                    price = get_prod_rslt['result'].get('PRICE') if get_prod_rslt['result'].get('PRICE') else None
                else:  # Если запрос к АПИ Битрикса не дал результата
                    continue
                products_rows.append({'PRODUCT_ID': prod_id, 'PRICE': price, 'QUANTITY': quantity})
            add_products_rslt = bitra.call(
                method='crm.deal.productrows.set',
                params={
                    'id': deal_id,
                    'rows': products_rows
                }
            )

            if add_products_rslt['result']:
                return Response(
                    {'Success! Bitrix answer': add_products_rslt},
                    status.HTTP_200_OK
                )
            else:  # Если запрос для добавления товаров был неудачным
                return Response(
                    {'Products does not set in deal. Bitrix answer': add_products_rslt},
                    status.HTTP_400_BAD_REQUEST
                )
        else:  # Если данные из параметров запроса не прошли проверку
            return Response({'Request data is not valid! Your request data': request.data}, status.HTTP_400_BAD_REQUEST)


class WorkWthDocuments(APIView):
    """Вьюшка для работы с генератором документов в Битриксе"""

    def get(self, request, format=None):
        """
        Обработка GET запроса.
        Здесь мы должны сформировать документы (счёт и договор) в сделке.
        Затем кинуть таск в селери и по готовности ПДФ, используя токен бота и сырой метод API телеграма,
        отправить документ пользователю.
        Параметры:
            ?tlg_id - TG ID пользователя
        """

        tlg_id = request.query_params.get('tlg_id')
        if str(tlg_id).isdigit():
            # Достаём из БД объект данного пользователя
            bot_user_obj = BotUsers.objects.get(tlg_id=tlg_id)
            company_name = CompanyData.objects.get(user=bot_user_obj).comp_name

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

            is_ip = True if company_name.upper().startswith('ИП ') else False  # Определяем флаг для ИП

            # Двигаем сделку по воронке
            method = 'crm.deal.update'
            params = {
                'id': bot_user_obj.deal_id,
                'fields': {'STAGE_ID': 'PREPAYMENT_INVOICE'}
            }
            change_deal_status_rslt = bitra.call(method=method, params=params)   # TODO: реализовать проверку этого
            # Генерируем документ по ID шаблона
            method = 'crm.documentgenerator.document.add'
            params = {
                'templateId': 2,  # ID шаблона (счёта)
                'entityTypeId': 2,  # ID типа сущности CRM - сделка
                'entityId': bot_user_obj.deal_id,  # ID тестовой сделки
                'stampsEnabled': 1  # 1 - значит ставим штампы и подписи
            }
            invoice_rslt = bitra.call(method=method, params=params)  # Запрашиваем счёт
            params = {
                # ID шаблона (договора) 228 - Для ИП, 230 - ООО)
                'templateId': 228 if is_ip else 230,
                'entityTypeId': 2,  # ID типа сущности CRM - сделка
                'entityId': bot_user_obj.deal_id,  # ID тестовой сделки
                'stampsEnabled': 1  # 1 - значит ставим штампы и подписи
            }
            contract_rslt = bitra.call(method=method, params=params)  # Запрашиваем договор

            if invoice_rslt['result']['document']['id'] and contract_rslt['result']['document']['id']:
                invoice_doc_id = invoice_rslt['result']['document']['id']
                contract_doc_id = contract_rslt['result']['document']['id']
                # Создаём таск celery
                get_pdf_doc_from_btrx.delay(invoice_doc_id=invoice_doc_id, contract_doc_id=contract_doc_id,
                                            tlg_id=tlg_id)
                return Response({'OK!': 'Docs are generated, tasks are being executed.'})
        else:  # Если параметр запроса не прошёл проверку
            return Response({'Invalid request parameter. Your value': tlg_id}, status.HTTP_400_BAD_REQUEST)


class PersData(APIView):
    """
    Вьюшка для работы с персональными данными
    """

    def get(self, request, format=None):
        """
        Обработка GET запроса.
        Получаем из сделки ссылку на форму.
        Параметры:
            tlg_id - Telegram ID клиента.
        """
        tlg_id = request.query_params.get('tlg_id')
        if str(tlg_id).isdigit():
            # Достаём из БД объект данного пользователя
            bot_user_obj = BotUsers.objects.get(tlg_id=tlg_id)

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

            # Двигаем сделку по воронке
            method = 'crm.deal.update'
            params = {
                'id': bot_user_obj.deal_id,
                'fields': {
                    'STAGE_ID': 'WON',
                    'CATEGORY_ID': 22,
                    'UF_CRM_1637673196084': 2824,
                }
            }
            change_deal_status_rslt = bitra.call(method=method, params=params)  # TODO: реализовать проверку этого

            # Запрашиваем сделку и достаём от туда ссылку на форму
            method = 'crm.deal.get'
            params = {'id': bot_user_obj.deal_id}
            method_rslt = bitra.call(method=method, params=params)
            if method_rslt.get("result"):   # Если запрос успешный
                form_link = method_rslt["result"].get("UF_CRM_1674048858820")
                if form_link:    # Если ссылка есть
                    # В сериалайзер надо отдать не просто значение параметра, а словарь
                    form_link_serializer = FormLinkSerializer({'form_link': form_link}, many=False).data
                    return Response(form_link_serializer, status.HTTP_200_OK)
                else:   # Если ссылки нет
                    return Response({'Form link not exist in deal'}, status=status.HTTP_400_BAD_REQUEST)
            else:   # Запрос к АПИ битрикса не дал результата
                return Response({'Error from Bitrix': method_rslt}, status=status.HTTP_400_BAD_REQUEST)
        else:   # Неверный параметр запроса
            return Response({'Invalid request parameter'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        """
        Принимаем персональные данные из запроса. Фиксируем в модели BotUsers согласие и его дату.
        Данные отправляем дальше в Битрикс.
            pssprt - серия и номер паспорта
            snls - СНИЛС
            tlg_id - TG ID пользователя
        """
        # {"pssprt": 1111223344, "snls": 12345678909, "tlg_id": 1978587604}

        passport = request.data.get('pssprt')
        snils = request.data.get('snls')
        tlg_id = request.data.get('tlg_id')
        if str(passport).isdigit() and str(snils).isdigit() and str(tlg_id).isdigit():    # Если оба параметра запроса - цифры
            # Фиксируем в БД дату и время согласия.
            BotUsers.objects.update_or_create(
                tlg_id=tlg_id,
                defaults={"consent_to_pers_data": True, "consent_datetime": datetime.datetime.now()}
            )
            user_obj = BotUsers.objects.get(tlg_id=tlg_id)

            # Обновляем реквизит компании паспортом и снилсом
            requisite_id = CompanyData.objects.get(user=user_obj).requisite_id

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

            method = 'crm.requisite.update'
            params = {
                'id': requisite_id,
                'fields': {
                    "UF_CRM_1672134628": snils,  # Должен быть СНИЛС
                    # "UF_CRM_1672134382": passport,  # TODO: нужно взять у Артура поле, в которе писать пасп.данные
                }
            }
            method_rslt = bitra.call(method=method, params=params)
            if method_rslt.get('result'):   # Если в Битрикс всё успешно записалось
                return Response({'Success!'}, status.HTTP_200_OK)
            else:   # Если Битрикс ответил ошибкой
                return Response({'Error. Bitrix answer': method_rslt}, status.HTTP_400_BAD_REQUEST)
        else:   # Если данные не прошли валидацию
            return Response({'Request data is not valid! Your request data': request.data}, status.HTTP_400_BAD_REQUEST)


class BotRatingView(APIView):
    """Работа с оценками бота-регистратора"""

    def post(self, request, format=None):
        """
        POST запрос для записи оценки бота пользователем.
        Из бота сперва прилетает оценка, а затем следующим запросом коммент, но только если клиент его ввёл.
        Параметры запроса:
            tlg_id - TG ID пользователя
            rating - оценка пользователя (число в виде строки, длина строки 1) (опционально)
            comment - комментарий к оценке (опционально)
        """
        # {"tlg_id":1978587604,"comment":"new comment"}
        tlg_id = request.data.get('tlg_id')
        rating = request.data.get('rating')
        comment = request.data.get('comment')
        if str(tlg_id).isdigit() and comment and len(comment) <= 4096:
            BotRatings.objects.update_or_create(
                user=BotUsers.objects.get(tlg_id=tlg_id),
                defaults={'comment': comment}
            )
            return Response(status.HTTP_200_OK)
        if str(tlg_id).isdigit() and str(rating).isdigit() and len(str(rating)) == 1:
            BotRatings.objects.update_or_create(
                user=BotUsers.objects.get(tlg_id=tlg_id),
                defaults={'rating': rating}
            )
            return Response(status.HTTP_200_OK)
        else:
            return Response({'Request data is not valid! Your request data': request.data}, status.HTTP_400_BAD_REQUEST)


class AddTaskToLawyer(APIView):
    """Вьюшка для добавления задачи юристу"""

    def get(self, request, format=None):
        """
        Обработка GET запроса для добавления задачи юристу.
        Параметры:
            ?tlg_id - TG ID клиента
            ?task_type - Tип задачи (1-ЭДО, 2-МЧД)
        """
        tlg_id = request.query_params.get('tlg_id')
        task_type = request.query_params.get('task_type')
        if str(tlg_id).isdigit() and str(task_type).isdigit():
            user_obj = BotUsers.objects.get(tlg_id=tlg_id)

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

            # Ставим в Битриксе задачу юристу
            if str(task_type) == '1':   # Если тип задачи 1 - ЭДО
                task_title = 'Выгрузить из сделки клиента договор без факсимиле, ' \
                             'отправить его из контура Диадока на почту клиента'
            else:   # Если тип задачи 2 - МЧД
                task_title = 'Добавить организацию в Контур экстерн-подготовить доверенность к подписанию'
            method = 'tasks.task.add'
            params = {
                'fields': {
                    'TITLE': task_title,
                    'DESCRIPTION': task_title,
                    'AUDITORS': [92],  # ID наблюдателя
                    'RESPONSIBLE_ID': 92,  # TODO: (ID ответственного) получать из БД
                    'UF_CRM_TASK': [f'D_{user_obj.deal_id}'],  # <тип сущности CRM>_<id сущности>
                }
            }
            method_rslt = bitra.call(method=method, params=params)
            if method_rslt.get('result'):   # Если запрос выполнен успешно
                return Response({'Successful request for add task to lawyer'}, status.HTTP_200_OK)

        else:   # Если в tlg_id были переданы не цифры
            return Response({'Request data is not valid! Your request data': request.data}, status.HTTP_400_BAD_REQUEST)


class ReminderManagementView(APIView):
    """Вьюшка для управления напоминаниями"""

    def get(self, request, format=None):
        """
        GET запрос. Создаём или удаляем задачу в Celery о напоминании либо об оплате, либо о подписи.
        Параметры:
            ?tlg_id - TG ID пользователя
            ?reminder_type - Тип напоминания(p, s - оплата и подпись соответственно)
            ?act - Действие (add, del)
        """
        tlg_id = request.query_params.get('tlg_id')
        reminder_type = request.query_params.get('reminder_type')
        act = request.query_params.get('act')
        # Проверка параметров запроса
        if str(tlg_id).isdigit() and str(reminder_type).isalpha() and str(act).isalpha() \
                and len(str(reminder_type)) == 1 and len(str(act)) == 3:
            if act == 'add':    # Действие для добавления задачи
                pass
                # TODO: раскоментить, когда будут "отремонтированы" напоминалки
                # created_task = remind_user.delay(tlg_id=tlg_id, reminder_type=reminder_type)
                # user_obj = BotUsers.objects.get(tlg_id=tlg_id)
                # Reminders.objects.update_or_create(
                #     user=user_obj,
                #     defaults={
                #         'reminder_type': reminder_type,
                #         'proc_id': created_task.id
                #     }
                # )
            elif act == 'del':  # Действие для удаления задачи
                pass
                # TODO: раскоментить, когда будут "отремонтированы" напоминалки
                # remind_obj = Reminders.objects.get(user__tlg_id=tlg_id)
                # celery.app.control.revoke(task_id=remind_obj.proc_id, terminate=True)   # Отрубаем таск по его ID
                # remind_obj.delete()     # Удаляем запись из таблицы напоминалок
                # logger.info(f'Таск о напоминании удалён! TG ID == {tlg_id}')
            return Response({'Success'}, status.HTTP_200_OK)
        else:   # Если параметры запроса невалидны
            return Response({'Invalid request params'}, status.HTTP_400_BAD_REQUEST)


class MarketplaceWorkView(APIView):
    """Вьюшка для обработки запросов от бота, связанных с маркетплейсами, и работа с Битрикс"""

    def post(self, request, format=None):
        """
        Обработка POST запроса. Получаем ID маркетплейсов и передаём их в сделку Битрикс.
        """

        # В запросе от бота прилетит tlg_id - число и строка, в которой записаны цифры через пробел.
        marketplaces_lst = request.data.get('marketplaces').split()
        tlg_id = request.data.get('tlg_id')
        if str(tlg_id).isdigit():
            for i_elem in marketplaces_lst:
                if not i_elem.isdigit():
                    validation_flag = False
                    break
            else:
                validation_flag = True
        else:
            validation_flag = False

        if validation_flag:     # Данные прошли валидацию
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

            # Записываю в сделку ID маркетплейсов
            deal_id = BotUsers.objects.get(tlg_id=tlg_id).deal_id
            method = 'crm.deal.update'
            params = {
                'id': deal_id,
                'fields': {
                    'UF_CRM_1675152964610': marketplaces_lst  # ID маркетплейса(ов)
                },
            }
            method_rslt = bitra.call(method=method, params=params)
            if method_rslt.get('result'):  # Если запрос выполнен успешно
                return Response({'Successful request for add marketplaces in deal'}, status.HTTP_200_OK)
            else:   # Отрицательный ответ Битрикса
                return Response({'Error. Bitrix answer': f'{method_rslt}'}, status=status.HTTP_400_BAD_REQUEST)
        else:   # Данные не прошли валидацию
            return Response({'result': f'Your data doesnt validate. Your request here{request.data}'},
                            status=status.HTTP_400_BAD_REQUEST)


class SomeBtrxMethod(APIView):
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

        # ID тестовой сделки 86564
        # ID коннектора feed-add-post-form-link-text-telegrambot
        # ID открытой линии 164
        # Мой ID в системе 32698
        # ID компании 20220
        # ID обычного реквизита 5890
        # ID банковского реквизита 472
        # ID шаблона договора бот-помощник 78
        # ID шаблона счёта 2
        # ID сгенерированного документа - Счёта 3578

        # # Получить сделку по ID
        # method = 'crm.deal.get'
        # params = {'id': 86564}

        # Получить список полей компании
        # method = 'crm.company.fields'
        # params = ''

        # # Получаем список пресетов для реквизитов
        # method = 'crm.requisite.preset.list'
        # params = None

        # # Получаем пресет для реквизита по ID
        # method = 'crm.requisite.preset.get'
        # params = {'id': 1}  # 1 - ООО, 3 - ИП

        # # Получаем список банковских реквизитов
        # method = 'crm.requisite.bankdetail.list'
        # params = None

        # # Получаем список полей банковских реквизитов
        # method = 'crm.requisite.bankdetail.fields'
        # params = None

        # # Получаем поля банковских реквизитов
        # method = 'crm.requisite.bankdetail.fields'
        # params = None

        # # Получаем компанию
        # method = 'crm.company.get'
        # params = {'id': 20306}

        # # Получаем список полей реквизитов
        # method = 'crm.requisite.fields'
        # params = None

        # # Создаём реквизит
        # method = 'crm.requisite.add'
        # params = {
        #     'fields': {
        #         "ENTITY_TYPE_ID": 4,
        #         "ENTITY_ID": 20220,     # Это ID компании, к которой привязываемся
        #         "PRESET_ID": 1,  # ID шаблона реквизита (это ОРГАНИЗАЦИЯ, типо вроде ООО, для ИП == 3)
        #         "NAME": f"Реквизит компании Тестовая компания бота-регистратора",
        #         # "XML_ID": "5e4641fd-1dd9-11e6-b2f2-005056c00008",  # ? ХЗ
        #         "ACTIVE": "Y",
        #         # "SORT": 100  # ? ХЗ
        #     }
        # }

        # # Создаём реквизит для ИП
        # method = 'crm.requisite.add'
        # params = {
        #     'fields': {
        #         "ENTITY_TYPE_ID": 4,
        #         "ENTITY_ID": 20272,  # Это ID компании, к которой привязываемся
        #         "PRESET_ID": 3,  # 3 - айдишник шаблона реквизита для ИП
        #         "NAME": f"ТЕСТ Реквизит компании ИП Шестаков Ярослав Викторович",
        #         # "XML_ID": "5e4641fd-1dd9-11e6-b2f2-005056c00008",  # ? ХЗ
        #         "ACTIVE": "Y",
        #         # "SORT": 100,  # ? ХЗ
        #         "RQ_LAST_NAME": 'Шестаков',  # Фамилия ИП
        #         "RQ_FIRST_NAME": 'Ярослав',  # Имя ИП
        #         "RQ_SECOND_NAME": 'Викторович',  # Отчество ИП
        #         "CompanyRequisiteRegisteredAddressText": 'Город, улица, дом, индекс',  # Адрес компании
        #         "RQ_OGRNIP": '123456789009876',  # ОГРН компании
        #         "RQ_INN": '123456789009',  # ИНН компании
        #     }
        # }

        # Создаём реквизит для ООО (ID компании 20294)
        method = 'crm.requisite.add'
        params = {
            'fields': {
                "ENTITY_TYPE_ID": 4,
                "ENTITY_ID": 20358,  # Это ID компании, к которой привязываемся
                "PRESET_ID": 1,  # 1 - айдишник шаблона реквизита для ООО
                "NAME": f"ТЕСТ Реквизит компании ООО Бодрый единорог",
                # "XML_ID": "5e4641fd-1dd9-11e6-b2f2-005056c00008",  # ? ХЗ
                "ACTIVE": "Y",
                # "SORT": 100,  # ? ХЗ
                "RQ_LAST_NAME": 'Шестаков',  # Фамилия
                "RQ_FIRST_NAME": 'Ярослав',  # Имя
                "RQ_SECOND_NAME": 'Викторович',  # Отчество
                "RQ_OGRN": '1234567890098',  # ОГРН компании ООО
                "RQ_INN": '123456789009',  # ИНН компании
                "RQ_COMPANY_FULL_NAME": 'Полное название компании',  # хз, полное название компании?
                "RQ_COMPANY_NAME": 'Хз, имя компании что ли',
                "RQ_DIRECTOR": 'ФИО управляющего',
                "UF_CRM_1573048471": 'Вроде как должность управляющего',
                "UF_CRM_1672134628": '11122233345',     # Должен быть СНИЛС
                "UF_CRM_1672134382": '1111 223344',     # Серия и номер паспорта должна быть
            }
        }   # метод вернул ID реквизита 6094

        # Обновляем реквизит
        method = 'crm.requisite.update'
        params = {
            'id': 6094,
            'fields': {
                "UF_CRM_1672134628": '11111111111',  # Должен быть СНИЛС
                "UF_CRM_1672134382": '1111 009988',  # Нифига тут ИНН физика
            }
        }

        # # Создаём банковский реквизит
        # bank_obj = BankData.objects.get(bik=44525823)   # Достаю явно из БД, в работе надо по-другому
        # method = 'crm.requisite.bankdetail.add'
        # params = {
        #     'fields': {
        #         # "ENTITY_TYPE_ID": 8,    # Тип родительской сущности(ID) 8 - реквизит
        #         # "ENTITY_ID": 6026,     # ID обычного реквизита
        #         # "COUNTRY_ID": 122,
        #         # "NAME": "(ТЕСТ) Банковские реквизиты сейчас создаю",
        #         # "RQ_BANK_NAME": 'Тут название банка',
        #         # "RQ_BIK": 'тут бик банка',
        #         # "RQ_ACC_NUM": f"Тут РС ",     # РС
        #         # "RQ_ACC_CURRENCY": "RUB",
        #         # "RQ_COR_ACC_NUM": 'Тут Кор.счёт',   # Кор.счёт
        #         "ENTITY_ID": 6026,
        #         "COUNTRY_ID": 1,
        #         "NAME": "Реквизит банка",
        #         "XML_ID": "1e4641fd-2dd9-31e6-b2f2-105056c00008",
        #         "ACTIVE": "Y",
        #         "SORT": 100
        #     }
        # }   # метод вернул ID реквизита 540

        # # Привязываем компанию к сделке
        # method = 'crm.deal.update'
        # params = {
        #     'id': 86564,    # Установил явно, надо из вне брать (БД)
        #     'fields': {
        #         'COMPANY_ID': 20220  # Установил явно, надо из вне брать (результат создания компании)
        #     },
        #     'params': {'REGISTER_SONET_EVENT': 'Y'}
        # }

        # # Получаем список документов
        # method = 'crm.documentgenerator.template.list'
        # params = {'select': ['*']}

        # # Генерируем документ по ID шаблона
        # method = 'crm.documentgenerator.document.add'
        # params = {
        #     'templateId': 2,    # ID шаблона счёта
        #     'entityTypeId': 2,   # ID типа сущности CRM - сделка
        #     'entityId': 86564,  # ID тестовой сделки
        #     'stampsEnabled': 1  # 1 - значит ставим штампы и подписи
        # }
        # # document_id = method_rslt['result']['document']['id'] - здесь лежит ID документа в ответе Битры

        # # Получаем ранее сгенерированный документ по ID и выдёргиваем от туда ссылку на PDF
        # method = 'crm.documentgenerator.document.get'
        # params = {'id': 3660}
        # # pdf_link = method_rslt['result']['document']['pdfUrl'] - здесь ссылка на PDF док-та

        # # Получаем товар по его ID
        # method = 'crm.product.get'
        # params = {'id': 1474}

        # # Создание чата
        # method = 'im.chat.add'
        # params = {
        #     'TYPE': 'CHAT',
        #     'TITLE': 'ТЕСТ Чат бота-регистратора',
        #     'DESCRIPTION': 'Тестовый чат',
        #     'COLOR': 'PINK',
        #     'MESSAGE': 'Тестовое первичное сообщение',
        #     'USERS': [32698, 17134],
        #     # 'ENTITY_TYPE': 'CHAT',
        #     # 'ENTITY_ID' = > 13,
        #     # 'OWNER_ID' = > 39,
        # }

        # # Отправка сообщения в чат
        # method = 'im.message.add'
        # params = {
        #     'DIALOG_ID': 'chat61534',
        #     'MESSAGE': 'Сообщение от бота-регистратора\n\n'
        #                '#12345678\n\n'
        #                'Пользователь с TG ID 1123345\n'
        #                'Отправил сообщение (нажал кнопку):'
        #                'Текст сообщения (название кнопки)'
        # }

        # # Получаем реквизит
        # # # ID реквизита 6018 и 6020 (6026 для ООО)
        # method = 'crm.requisite.get'
        # params = {'id': 6090}

        # # Получаем поля реквизита
        # method = 'crm.requisite.fields'
        # params = None

        # # Создаём адрес для реквизита
        # method = 'crm.address.add'
        # params = {
        #     'fields': {
        #         "TYPE_ID": 11,  # Тип адреса (1 - фактический)
        #         "ENTITY_TYPE_ID": 8,  # ID род. сущности (8 - реквизит, 4 - компания)
        #         "ENTITY_ID": 6020,  # ID реквизита
        #         "ADDRESS_1": "пр-т Героев Сталинграда",
        #         "CITY": "Севастополь",
        #         "POSTAL_CODE": 299059,  # Индекс
        #     }
        # }

        # # Типы адресов
        # method = 'crm.enum.addresstype'
        # params = None

        # # Получаем банковский реквизит
        # method = 'crm.requisite.bankdetail.get'
        # params = {
        #     'id': 540
        # }

        # # Получаем список шаблонов документов
        # method = 'crm.documentgenerator.template.list'
        # params = {
        #     'select': ['*']
        # }

        # # Получаем сделку по ID
        # method = 'crm.deal.get'
        # params = {'id': 86564}

        # # Ставим задачу пользователю Битрикс
        # method = 'tasks.task.add'
        # params = {
        #     'fields': {
        #         'TITLE': '(REG.BOT TEST)Название задачи',
        #         'DESCRIPTION': '(REG.BOT TEST)Описание задачи',
        #         'AUDITORS': [29508],  # ID наблюдателя
        #         'RESPONSIBLE_ID': 28074,  # ID ответственного
        #         'UF_CRM_TASK': ['D_86564'],  # <тип сущности CRM>_<id сущности>
        #     }
        # }

        # # Получаем список компаний
        # method = 'crm.company.list'
        # params = {
        #     'filter': {
        #         'TITLE': 'ООО "БОДРЫЙ ЕДИНОРОГ"'
        #     },
        #     'select': ["ID", "TITLE"],
        # }

        # Двигаем сделку по воронке
        method = 'crm.deal.update'
        params = {
            'id': 86740,
            'fields': {
                'STAGE_ID': 'WON',
                'CATEGORY_ID': 22,
                'UF_CRM_1637673196084': 2824,
            }
        }

        # # Получаем список категорий
        # method = 'crm.category.list'
        # params = {
        #     'entityTypeId': 2
        # }

        # # Обновляем категорию сделки
        # method = 'crm.category.update'
        # params = {
        #     'entityTypeId': 2,
        #     'id': 22,
        #     'fields': {
        #         'DEAL_ID': 86740,
        #     }
        # }

        # # Достаём список реквизитов и фильтруем по ИНН
        # method = 'crm.requisite.list'
        # params = {
        #     'order': {"DATE_CREATE": "ASC"},
        #     'filter': {"RQ_INN": 7202255340, 'ENTITY_TYPE_ID': 4},    # INN 7202255340
        #     'select': ['ENTITY_ID']
        # }

        # Записываю в сделку ID маркетплейсов
        method = 'crm.deal.update'
        params = {
            'id': 86920,    # Установил явно, ID сделки
            'fields': {
                'UF_CRM_1675152964610': [13268, 13274]  # Установил явно, ID маркетплеса(ов)
            },
        }

        method_rslt = bitra.call(method=method, params=params)
        print('=' * 10, f'РЕЗУЛЬТАТ МЕТОДА {method}', '=' * 10, f'\n\n{method_rslt}')
        return HttpResponse(f'{json.dumps(method_rslt, indent=4, ensure_ascii=False)}', status=http.HTTPStatus.OK)
