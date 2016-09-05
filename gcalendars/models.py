# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta

from django.db import models
# Create your models here.

# from gentities.models import Gentity, Guser


class Gtime_slot(models.Model):
    # gentity = models.ForeignKey(Gentity, blank=True, null=True)
    from_time = models.DateTimeField('Hora de comienzo', max_length=10, blank=True, null=True)
    to_time = models.DateTimeField('Hora de finalización', max_length=10, blank=True, null=True)

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return u'From %s to %s (%s)' % (self.from_time, self.to_time, self.gentity.name)


class Gday(models.Model):
    # gentity = models.ForeignKey(Gentity, blank=True, null=True)
    date = models.DateField('Fecha señalada', max_length=10, blank=True, null=True)
    workable = models.BooleanField('Es laborable?', default=False)
    gtime_slots = models.ManyToManyField(Gtime_slot, blank=True)

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return u'%s - %s (%s)' % (self.date, ['nonworking', 'workable'][self.workable], self.gentity)


class Gcalendar(models.Model):
    # gentity = models.ForeignKey(Gentity, blank=True, null=True)
    monday = models.BooleanField("Lunes es laborable?", default=True)
    tuesday = models.BooleanField("Martes es laborable?", default=True)
    wednesday = models.BooleanField("Miércoles es laborable?", default=True)
    thursday = models.BooleanField("Jueves es laborable?", default=True)
    friday = models.BooleanField("Viernes es laborable?", default=True)
    saturday = models.BooleanField("Sábado es laborable?", default=False)
    sunday = models.BooleanField("Domingo es laborable?", default=False)
    gtime_slots = models.ManyToManyField(Gtime_slot, blank=True)
    gdays = models.ManyToManyField(Gday, blank=True)

    @property
    def workable_hours_per_day(self):
        total = timedelta(0)
        for slot in self.gtime_slots:
            total += slot.to_time - slot.from_time
        return total

    @property
    def workable_hours_per_week(self):
        total = timedelta(0)
        for slot in self.gtime_slots:
            total += slot.to_time - slot.from_time
        workable_days = [0, 1][self.monday] + [0, 1][self.tuesday] + [0, 1][self.wednesday] + [0, 1][self.thursday] + \
                        [0, 1][self.friday] + [0, 1][self.saturday] + [0, 1][self.sunday]
        return workable_days * total

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return u'Calendar of "%s"' % (self.gentity.name)
