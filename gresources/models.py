# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
# Create your models here.

from gentities.models import Gentity, Guser
# from gcalendars.models import Gcalendar


class Gresource(models.Model):
    T_RESOURCE = (('EQU', 'Equipment'), ('STA', 'Staff'))
    # gcalendar = models.ForeignKey(Gcalendar, blank=True, null=True)
    guser = models.ForeignKey(Guser, blank=True, null=True)
    name = models.CharField('Name of the resource', blank=True, null=True, max_length=150)
    kind = models.CharField('Material or human resource', blank=True, null=True, choices=T_RESOURCE, max_length=10)
    outsourced = models.BooleanField('Is this outsourced', default=False)
    fixed_cost = models.FloatField('Fixed cost', blank=True, null=True)
    hourly_rate = models.FloatField('Hourly rate', blank=True, null=True)
    overtime_rate = models.FloatField('Overtime rate', blank=True, null=True)
    children = models.ManyToManyField('self', blank=True)

    def __unicode__(self):
        return u'%s - %s (%s)' % (self.name, self.kind, self.gcalendar.gproject)
