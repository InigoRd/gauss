# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-01 08:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gprojects', '0035_gtask_pos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gtask',
            name='restriction',
            field=models.CharField(choices=[('ASAP', 'Lo antes posible'), ('ALAP', 'Lo m\xe1s tarde posible'), ('SD', 'Debe empezar el ...'), ('ED', 'Debe terminar el ...'), ('SNBD', 'No iniciar antes del ...'), ('SNLD', 'Iniciar como muy tarde el ...'), ('ENBD', 'No terminar antes del ...'), ('ENLD', 'Terminar como muy tarde el ...')], default='ASAP', max_length=10, verbose_name='Restriction type'),
        ),
    ]
