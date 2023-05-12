import time
from celery import shared_task
import requests
from registration_bot.MyBitrix23 import Bitrix23
from registration_bot.models import BotSettings
from loguru import logger


@shared_task
def get_pdf_doc_from_btrx(invoice_doc_id, contract_doc_id, tlg_id):
    """
    Отложенная задача, которая ждёт 30 сек и получает ссылку на документ в PDF формате от Битрикса.
    Затем отправляет документ пользователю от лица бота.
    """
    logger.info('Запуск отложенной задачи\nПолучение и отправка документов.')
    logger.info(f'ПАРАМЕТРЫ В ОТЛОЖЕННОЙ ЗАДАЧЕ:\n\t{invoice_doc_id}\t{contract_doc_id}\t{tlg_id}')

    time.sleep(30)  # Ждём пока в Битриксе сгенерируется документ в PDF формате
    # Создаём инстанс битры и рефрешим токены
    bitra = Bitrix23(
        hostname=BotSettings.objects.get(key="subdomain").value,
        client_id=BotSettings.objects.get(key="client_id").value,
        client_secret=BotSettings.objects.get(key="client_secret").value,
        access_token=BotSettings.objects.get(key="access_token").value,
        refresh_token=BotSettings.objects.get(key="refresh_token").value,
    )
    bitra.refresh_tokens()
    bot_token = BotSettings.objects.get(key='bot_token').value

    # Получаем счёт в PDF формате
    method = 'crm.documentgenerator.document.get'
    params = {'id': invoice_doc_id}
    invoice_rslt = bitra.call(method=method, params=params)
    invoice_pdf_link = invoice_rslt['result']['document'].get('pdfUrlMachine')
    if not invoice_pdf_link:
        logger.warning('Ссылка на ПДФ док-т счёта отсутствует, запрашиваю ещё 5 раз с паузой в 5 сек')
        for _ in range(10):
            time.sleep(5)
            params = {'id': invoice_doc_id}
            invoice_rslt = bitra.call(method=method, params=params)
            invoice_pdf_link = invoice_rslt['result']['document'].get('pdfUrlMachine')
            if invoice_pdf_link:    # Если ссылка на PDF получена, выходим из цикла
                break

    # Получаем договор в PDF формате
    params = {'id': contract_doc_id}
    contract_rslt = bitra.call(method=method, params=params)
    contract_pdf_link = contract_rslt['result']['document'].get('pdfUrlMachine')
    if not contract_pdf_link:
        logger.warning('Ссылка на ПДФ док-т счёта отсутствует, запрашиваю ещё 10 раз с паузой в 5 сек')
        for _ in range(10):
            time.sleep(5)
            params = {'id': contract_doc_id}
            contract_rslt = bitra.call(method=method, params=params)
            contract_pdf_link = contract_rslt['result']['document'].get('pdfUrlMachine')
            if contract_pdf_link:  # Если ссылка на PDF получена, выходим из цикла
                break

    if invoice_pdf_link and contract_pdf_link:
        # Отправка счёта
        bot_send_invoice_rslt = requests.post(
            url=f'https://api.telegram.org/bot{bot_token}/sendDocument',
            data={
                'chat_id': tlg_id,
                'document': invoice_pdf_link,
                'caption': '📄 Ваш счёт.'
            }
        )
        # Отправка договора
        bot_send_contract_rslt = requests.post(
            url=f'https://api.telegram.org/bot{bot_token}/sendDocument',
            data={
                'chat_id': tlg_id,
                'document': contract_pdf_link,
                'caption': '📄 Ваш договор.'
            }
        )

        if bot_send_invoice_rslt.status_code != 400 and bot_send_contract_rslt.status_code != 400:
            logger.success('Успешная отправка ПДФ документов клиенту. Отложенная задача выполнена!')
        else:
            logger.critical('Отправка документов через "сырой" запрос телеграма не удалось!Отложенная задача завершена.')
    else:   # Если ссылки на ПДФ не получены
        logger.critical(f'Ссылки на ПДФ не получены. ВОт результаты запросов\n\n{invoice_rslt}\n\n{contract_rslt}')


@shared_task
def remind_user(tlg_id, reminder_type):
    """
    Напоминание пользователю спустя сутки.
    """
    logger.info(f'Запуск отложенной задачи!\nОтправка напоминания пользователю с TG ID == {tlg_id}.')
    while True:
        time.sleep(86400)    # 86400
        if reminder_type == 'p':    # Берём текст напоминания об оплате
            msg_text = 'Напоминаем Вам о необходимости оплаты счёта.\n\nПосле оплаты, нажмите кнопку "Я ОПЛАТИЛ".'
        elif reminder_type == 's':  # Берём текст напоминания о подписи
            msg_text = 'Напоминаем Вам о необходимости подписания МЧД Вашей электронной цифровой подписью.\n' \
                       'Документы были отправлены на Вашу эл.почту.\n\n' \
                       'После подписания, нажмите кнопку "Я ПОДПИСАЛ".'
        else:
            msg_text = ''
        # Отправка напоминания
        bot_token = BotSettings.objects.get(key='bot_token').value
        send_remind_rslt = requests.post(
            url=f'https://api.telegram.org/bot{bot_token}/sendMessage',
            data={
                'chat_id': tlg_id,
                'text': msg_text,
            }
        )
        if send_remind_rslt.status_code != 400:
            logger.success(f'Успешная отправка напоминания пользователю с TG ID == {tlg_id}')
        else:
            logger.warning(f'Отправка напоминания пользователю с TG ID == {tlg_id} НЕ УДАЛАСЬ!')
