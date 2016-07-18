# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-21 16:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gprojects', '0011_auto_20160321_1539'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gbaseline',
            name='gentity',
        ),
        migrations.RemoveField(
            model_name='gproject',
            name='gbaselines',
        ),
        migrations.AddField(
            model_name='gbaseline',
            name='gproject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gprojects.Gproject'),
        ),
    ]