# Generated by Django 4.1.4 on 2023-01-26 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration_bot', '0014_alter_reminders_options_alter_reminders_table'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companydata',
            name='address',
            field=models.CharField(max_length=5000, verbose_name='Адрес компании'),
        ),
        migrations.AlterField(
            model_name='companydata',
            name='comp_name',
            field=models.CharField(max_length=5000, verbose_name='Название компании'),
        ),
        migrations.AlterField(
            model_name='companydata',
            name='top_management_name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='ФИО управляющего'),
        ),
        migrations.AlterField(
            model_name='companydata',
            name='top_management_post',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Должность управляющего комп.'),
        ),
    ]
