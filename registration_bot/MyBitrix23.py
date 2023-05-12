from pybitrix24 import Bitrix24


class Bitrix23(Bitrix24):
    """
    Наследуюсь от класса Bitrix24 той библиотечки и переопределяю его конструктор.
    В конструкторе нужно сразу прописать значения для _access_token и _refresh_token.

    Как это работает?
        1. Создаём локальное веб-приложение (серверное) на своем портале Битрикс.
        2. От туда берём client_id, client_secret
        3. При создании приложения мы назначили "Путь для первоначальной установки" - это вьюха,
        в которой мы создадим инстанс этого класса.
        4. Битрикс отправит запрос на адрес из пункта выше (3) и в POST запросе прилетят access_token, refresh_token.
        5. В этой вьюхе ("Путь для первоначальной установки") создаём инстанс этого класса со всеми параметрами,
        которые мы уже получили.
    """

    def __init__(self, hostname, client_id, client_secret, access_token, refresh_token, expires=None):
        super().__init__(hostname, client_id, client_secret)
        self._access_token = access_token
        self._refresh_token = refresh_token
        self.expires = expires

    def refresh_tokens(self):
        """
        Переопределяем метод для рефреша токенов.
        """
        import requests
        import json
        import time
        import random

        if self.expires:
            local = time.localtime()
            t = time.localtime(int(self.expires) - random.randint(0, 120))
            if local < t:
                return

        url = f"https://oauth.bitrix.info/oauth/token/?grant_type=refresh_token&client_id={self.client_id}" \
              f"&client_secret={self.client_secret}&refresh_token={self._refresh_token}"
        response = requests.get(url)
        data = json.loads(response.text)

        # Если запрос успешный
        if data.get("access_token"):
            # Записываем в инстанс класса новые access_token, refresh_token и expires(когда истекают)
            self._access_token = data.get("access_token")
            self._refresh_token = data.get("refresh_token")
            # выкидываем из метода access_token, refresh_token и tokens_expires(когда истекают)
            return (
                ("access_token", data.get("access_token")),
                ("refresh_token", data.get("refresh_token")),
                ("tokens_expires", data.get("expires")),
            )
        else:
            raise Exception('Авторизация в битрикс неактуальна')
