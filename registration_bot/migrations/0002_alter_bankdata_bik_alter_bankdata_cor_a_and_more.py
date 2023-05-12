# Generated by Django 4.1.4 on 2022-12-20 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration_bot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankdata',
            name='bik',
            field=models.IntegerField(default=0, verbose_name='БИК'),
        ),
        migrations.AlterField(
            model_name='bankdata',
            name='cor_a',
            field=models.IntegerField(default=0, verbose_name='Кор.счёт'),
        ),
        migrations.AlterField(
            model_name='bankdata',
            name='rs',
            field=models.IntegerField(default=0, verbose_name='Расч.счёт'),
        ),
        migrations.AlterField(
            model_name='companydata',
            name='inn',
            field=models.IntegerField(default=0, verbose_name='ИНН'),
        ),
        migrations.AlterField(
            model_name='companydata',
            name='ogrn',
            field=models.IntegerField(default=0, verbose_name='ОГРН'),
        ),
    ]
