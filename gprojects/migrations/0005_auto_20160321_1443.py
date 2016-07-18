# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-21 14:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gentities', '0001_initial'),
        ('gprojects', '0004_remove_gcalendar_gproject'),
    ]

    operations = [
        migrations.AddField(
            model_name='gcalendar',
            name='gentity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gentities.Gentity'),
        ),
        migrations.AddField(
            model_name='gproject',
            name='gresources',
            field=models.ManyToManyField(blank=True, to='gprojects.Gresource'),
        ),
    ]