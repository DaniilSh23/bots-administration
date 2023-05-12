from django.db import models


class BotUsers(models.Model):
    """
    Модель пользователей бота.
        tlg_id - Telegram ID
        consent_to_pers_data - Согласие на обработку персональных данных
        consent_datetime - Дата и время согласия на обработку персональных данных
        tlg_username - Telegram username
        telephone - Контактный телефон клиента
        email - Контактная эл.почта клиента
        deal_id - ID сделки
        chat_for_deal_id - ID чата для сделки
        start_at - Дата старта бота клиентом
        is_staff - Является ли персоналом
    """

    tlg_id = models.CharField(verbose_name='Telegram ID', max_length=30)
    consent_to_pers_data = models.BooleanField(verbose_name='Согласие на обработку персональных данных', default=False)
    consent_datetime = models.DateTimeField(verbose_name='Дата и время согласия на обработку персональных данных',
                                            blank=True, null=True)
    tlg_username = models.CharField(verbose_name='Telegram username', max_length=50, blank=True, null=True)
    telephone = models.CharField(verbose_name='Контактный телефон', max_length=12, blank=True, null=True)
    email = models.CharField(verbose_name='Контактный email', max_length=50, blank=True, null=True)
    deal_id = models.CharField(verbose_name='ID сделки', max_length=50, blank=True, null=True)
    chat_for_deal_id = models.IntegerField(verbose_name='ID чата для сделки', blank=True, null=True)
    start_at = models.DateTimeField(verbose_name='Дата старта бота', auto_now_add=True)
    is_staff = models.BooleanField(verbose_name='Статус персонала', default=False)

    def __str__(self):
        return str(self.tlg_id)

    class Meta:
        db_table = 'Пользователи бота-регистратора'
        ordering = ['-id']
        verbose_name = 'Пользователь бота-регистратора'
        verbose_name_plural = 'Пользователи бота-регистратора'


class CompanyData(models.Model):
    """
    Модель данных компаний.
        comp_name - название компании
        address - адрес компании
        ogrn - ОГРН компании
        inn - ИНН компании
        top_management_post - должность главного управляющего компанией
        top_management_name - ФИО главного управляющего компанией
        user - поле типа FK к таблице BotUser. Отсылка к пользователю, который запустил бота
        requisite_id - ID реквизита в Битриксе
    """

    comp_name = models.CharField(verbose_name='Название компании', max_length=5000)
    address = models.CharField(verbose_name='Адрес компании', max_length=5000)
    ogrn = models.CharField(verbose_name='ОГРН', max_length=20)
    inn = models.CharField(verbose_name='ИНН', max_length=20)
    top_management_post = models.CharField(verbose_name='Должность управляющего комп.', max_length=100, blank=True, null=True)
    top_management_name = models.CharField(verbose_name='ФИО управляющего', max_length=200, blank=True, null=True)
    user = models.ForeignKey(verbose_name='Пользователь бота', to=BotUsers, on_delete=models.CASCADE)
    requisite_id = models.IntegerField(verbose_name='ID реквизита в Битриксе', blank=True, null=True)

    def __str__(self):
        return self.comp_name

    class Meta:
        db_table = 'Компании бота-регистратора'
        ordering = ['-id']
        verbose_name = 'Компания бота-регистратора'
        verbose_name_plural = 'Компании бота-регистратора'


class BankData(models.Model):
    """
    Модель банковских реквизитов компании
        bik - БИК;
        rs - Расчётный счёт;
        cor_a - Корреспондентский счёт;
        bank_name - Название банка;
        company - FK к CompanyData, компания.
    """

    bik = models.IntegerField(verbose_name='БИК', default=0, )
    rs = models.CharField(verbose_name='Расч.счёт', max_length=20)
    cor_a = models.CharField(verbose_name='Кор.счёт', max_length=20)
    bank_name = models.CharField(verbose_name='Наименов.банка', max_length=500)
    company = models.ForeignKey(verbose_name='Компания', to=CompanyData, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.bik)

    class Meta:
        db_table = 'Банк.реквизиты бота-регистратора'
        ordering = ['-id']
        verbose_name = 'Банк.реквизиты бота-регистратора'
        verbose_name_plural = 'Банк.реквизиты бота-регистратора'


class BotSettings(models.Model):
    """
    Различные значения для настройки бота.
        key - ключ для значения;
        value - значение.
    """

    key = models.CharField(verbose_name='Ключ настройки', max_length=500)
    value = models.CharField(verbose_name='Значение настройки', max_length=500)

    def __str__(self):
        return self.value

    class Meta:
        db_table = 'Настройки бота-регистратора'
        ordering = ['-id']
        verbose_name = 'Настройки бота-регистратора'
        verbose_name_plural = 'Настройки бота-регистратора'


class BotRatings(models.Model):
    """
    Список напоминаний для бота-регистратора
    """
    user = models.ForeignKey(verbose_name='Пользователь бота', to=BotUsers, on_delete=models.CASCADE)
    rating = models.CharField(verbose_name='Оценка', max_length=1)
    created_at = models.DateTimeField(verbose_name='Дата', auto_now_add=True)
    comment = models.CharField(verbose_name='Комментарий', max_length=4096, blank=True, null=True)

    def __str__(self):
        return self.rating

    class Meta:
        db_table = 'Оценки бота-регистратора'
        ordering = ['-id']
        verbose_name = 'Оценки бота-регистратора'
        verbose_name_plural = 'Оценка бота-регистратора'


class Reminders(models.Model):
    """
    Напоминания для бота регистратора
    """
    CHOICES_LST = [
        ('p', 'оплата'),
        ('s', 'подпись')
    ]
    user = models.ForeignKey(verbose_name='Пользователь', to=BotUsers, on_delete=models.CASCADE)
    reminder_type = models.CharField(verbose_name='Тип напоминания', choices=CHOICES_LST, default='p', max_length=1)
    proc_id = models.CharField(verbose_name='ID процесса напоминания', max_length=150)

    def __str__(self):
        return self.proc_id

    class Meta:
        db_table = 'Напоминания бота-регистратора'
        ordering = ['-id']
        verbose_name = 'Напоминания бота-регистратора'
        verbose_name_plural = 'Напоминание бота-регистратора'
