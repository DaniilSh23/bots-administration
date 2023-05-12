# Generated by Django 4.1.4 on 2022-12-20 11:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BotSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=500, verbose_name='Ключ настройки')),
                ('value', models.CharField(max_length=500, verbose_name='Значение настройки')),
            ],
            options={
                'verbose_name': 'Настройки бота-регистратора',
                'verbose_name_plural': 'Настройки бота-регистратора',
                'db_table': 'Настройки бота-регистратора',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='BotUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tlg_id', models.IntegerField(default=0, verbose_name='Telegram ID')),
                ('tlg_username', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telegram username')),
                ('telephone', models.CharField(blank=True, max_length=12, null=True, verbose_name='Контактный телефон')),
                ('email', models.EmailField(blank=True, max_length=50, null=True, verbose_name='Контактный email')),
                ('deal_id', models.CharField(blank=True, max_length=50, null=True, verbose_name='ID сделки')),
                ('start_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата старта бота')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Статус персонала')),
            ],
            options={
                'verbose_name': 'Пользователь бота-регистратора',
                'verbose_name_plural': 'Пользователи бота-регистратора',
                'db_table': 'Пользователи бота-регистратора',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='CompanyData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_name', models.CharField(max_length=500, verbose_name='Название компании')),
                ('address', models.CharField(max_length=1000, verbose_name='Адрес компании')),
                ('ogrn', models.IntegerField(default=0, max_length=13, verbose_name='ОГРН')),
                ('inn', models.IntegerField(default=0, max_length=12, verbose_name='ИНН')),
                ('top_management_post', models.CharField(max_length=200, verbose_name='Должность управляющего комп.')),
                ('top_management_name', models.CharField(max_length=85, verbose_name='ФИО управляющего')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration_bot.botusers', verbose_name='Пользователь бота')),
            ],
            options={
                'verbose_name': 'Компания бота-регистратора',
                'verbose_name_plural': 'Компании бота-регистратора',
                'db_table': 'Компании бота-регистратора',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='BankData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bik', models.IntegerField(default=0, max_length=9, verbose_name='БИК')),
                ('rs', models.IntegerField(default=0, max_length=20, verbose_name='Расч.счёт')),
                ('cor_a', models.IntegerField(default=0, max_length=20, verbose_name='Кор.счёт')),
                ('bank_name', models.CharField(max_length=500, verbose_name='Наименов.банка')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration_bot.companydata', verbose_name='Компания')),
            ],
            options={
                'verbose_name': 'Банк.реквизиты бота-регистратора',
                'verbose_name_plural': 'Банк.реквизиты бота-регистратора',
                'db_table': 'Банк.реквизиты бота-регистратора',
                'ordering': ['-id'],
            },
        ),
    ]
