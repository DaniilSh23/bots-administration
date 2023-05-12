# Админ панель для ботов

## Описание
Весь функционал бэкэнда веб-приложений, который необходим в Telegram ботах предоставляет данный проект.

Ниже немного детальнее.

Проект предназначен для администрирования различных ботов (vpn_bot, registration_bot, ServiceDeskBot), хранение и обработки различных данных ботов(БД), для работы с API Bitrix и много другого, в том числе рендер различных веб-страниц с формами и прочим, а также обработка запросов, связанных с ними.

### registration_bot:
Используется celery + redis, django rest framework.
Суть бота в том, чтобы упростить процесс регистрации на бухгалтерское сопровождение. Создаёт в Битриксе необходимые сущности: сделки, задачи и т.п. Насыщает сделки данными о клиенте, выполняет расчёт стоимости услуг, формируем счёт и договор, напоминает об оплате и многое другое...

### vpn_bot:
Необходим был как точка входа для новых клиентов на услугу клиентского VPN. Аккумулирует информацию о пользователях, собирая данные из Telegram, даём возможность собрать эти данные в отчёт из админ-панели. 

Отчёт - это файл, который можно будет использовать для загрузки клиентов с целью последующей рассылки по ним через Telegram или WhatsApp, используя иной мой проект. Этот проект на момент написания этого текста был доступен по адресу dyatel.pro

### ServiceDeskBot
Бот для корпоративного сервиса технической поддержки.
Рендерит веб-страницу с формой, используя Telegram WebApp. При отправке данных формы происходит проверка, что юзер с таким Telegram ID есть среди сотрудников корпоративного портала Битрикс. Работает с API Bitrix для выполнения необходимых действий по созданию новой заявки в техническую поддержку.

