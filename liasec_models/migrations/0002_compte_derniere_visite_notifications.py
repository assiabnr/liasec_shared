# Generated by Django 5.1.6 on 2025-06-16 13:27

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('liasec_models', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='compte',
            name='derniere_visite_notifications',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Dernière visite des notifications'),
        ),
    ]
