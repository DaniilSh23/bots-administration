# Generated by Django 4.1.4 on 2023-02-02 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration_bot', '0017_alter_reminders_proc_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companydata',
            name='inn',
            field=models.CharField(max_length=20, verbose_name='ИНН'),
        ),
        migrations.AlterField(
            model_name='companydata',
            name='ogrn',
            field=models.CharField(max_length=20, verbose_name='ОГРН'),
        ),
    ]
