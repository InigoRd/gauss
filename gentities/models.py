# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class Gpermission(models.Model):
    TIPOS = (
        ('MEN', 'Permiso para acceder a un menú'),
        ('SUB', 'Permiso para acceder a un  submenú'),
        ('MTE', 'Permiso para acceder a un elemento de un menú'),
        ('STE', 'Permiso para acceder a un elemento de un submenú'),
        ('ESP', 'Permiso especial para determinadas acciones'),
    )
    name = models.CharField("Nombre del permiso", max_length=100)
    code_name = models.CharField("Código del permiso", max_length=50)
    type = models.CharField("tipo", max_length=10, choices=TIPOS)

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return u'%s' % (self.nombre)


def update_anagram_gentity(instance, filename):
    nombre = str(instance.id) + '_anagram.' + filename.partition('.')[2]
    return os.path.join("gentity_anagrams/", nombre)


PROVINCES = (('0', ''),)


class Gentity(models.Model):
    name = models.CharField("Nombre", max_length=250, null=True, blank=True)
    vat_number = models.CharField("CIF", max_length=20, null=True, blank=True)
    # bank = models.ForeignKey(Bank, null=True, blank=True)
    iban = models.CharField("IBAN", max_length=40, null=True, blank=True)
    address = models.CharField("Dirección", max_length=375, null=True, blank=True)
    locality = models.CharField("Localidad", max_length=200, null=True, blank=True)
    province = models.CharField("Provincia", max_length=4, choices=PROVINCES, default='0')
    postalcode = models.CharField("Código postal", max_length=20, null=True, blank=True)
    tel = models.CharField("Teléfono", max_length=20, null=True, blank=True)
    fax = models.CharField("Fax", max_length=20, null=True, blank=True)
    web = models.URLField("Web", max_length=100, null=True, blank=True)
    mail = models.EmailField("E-mail", max_length=100, null=True, blank=True)
    anagram = models.ImageField("Anagrama", upload_to=update_anagram_gentity, blank=True)
    domain = models.CharField("Subdominio", max_length=200, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Entidades"

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.vat_number)


LEVELS = ((1, 'Cargo/Perfil de primer nivel'), (2, 'Cargo/Perfil de segundo nivel'),
          (3, 'Cargo/Perfil de tercer nivel'), (4, 'Cargo/Perfil de cuarto nivel'),
          (5, 'Cargo/Perfil de quinto nivel'), (6, 'Cargo/Perfil de sexto nivel'))


class Gprofile(models.Model):
    gentity = models.ForeignKey(Gentity, null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True)
    name = models.CharField("Nombre", max_length=50)
    gpermissions = models.ManyToManyField(Gpermission, blank=True)
    level = models.IntegerField('Nivel jerárquico en el organigrama', null=True, blank=True, choices=LEVELS,
                                default=LEVELS[0][0])

    class Meta:
        verbose_name_plural = "Perfiles"
        ordering = ['pk']

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.level)


class Gdepartment(models.Model):
    gentity = models.ForeignKey(Gentity)
    name = models.CharField("Nombre", max_length=250, null=True, blank=True)
    messages = models.BooleanField("Están en lista de mensajería", default=False)
    notes = models.TextField("Observaciones", null=True, blank=True)

    @property
    def rango_edad(self):
        return self.edad_max - self.edad_min

    class Meta:
        verbose_name_plural = "Departamentos"

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.gentity.name)


def update_photo(instance, filename):
    nombre = str(instance.id) + '_photo.' + filename.partition('.')[2]
    return os.path.join("guser_photos/", nombre)


SEXO = (('H', 'Hombre'), ('M', 'Mujer'))


class Guser(AbstractUser):
    gentity = models.ForeignKey(Gentity, null=True, blank=True)
    sex = models.CharField("Sexo", max_length=10, choices=SEXO, blank=True)
    idcard = models.CharField("DNI", max_length=20, null=True, blank=True)
    address = models.CharField("Dirección", max_length=100, blank=True)
    postalcode = models.CharField("Código postal", max_length=10, blank=True)
    locality = models.CharField("Localidad de residencia", max_length=50, blank=True)
    province = models.CharField("Provincia", max_length=50, blank=True)
    born = models.CharField("Fecha de nacimiento", max_length=20, blank=True)
    tel1 = models.CharField("Teléfono fijo", max_length=30, blank=True)
    tel2 = models.CharField("Teléfono móvil", max_length=30, blank=True)
    gpermissions = models.ManyToManyField(Gpermission, blank=True)
    gprofiles = models.ManyToManyField(Gprofile, blank=True)
    gdepartment = models.ForeignKey(Gdepartment, null=True, blank=True)
    # active = models.NullBooleanField("Activo")
    position = models.CharField("Cargo que ocupa en la entidad", max_length=100, null=True, blank=True)
    notes = models.TextField("Resumen datos", null=True, blank=True)
    photo = models.ImageField("Fotografía", upload_to=update_photo, blank=True)

    @property
    def has_mail(self):
        if len(self.email) > 5:
            return True

    def has_gprofiles(self, gprofiles_check):
        if type(gprofiles_check) == list:
            p_ids = self.gprofiles.all().values_list('pk', flat=True)
            return len([perfil for perfil in p_ids if perfil in gprofiles_check]) > 0
        else:
            return len([perfil for perfil in self.gprofiles.all() if perfil in gprofiles_check]) > 0

    def has_gpermission(self, gpermission_check):
        """
        :param gpermission_check: string (code_name of gpermission) or integer (id of gpermission).
        :return: Boolean (True or False)
        """
        try:
            Gpermission.objects.get(code_name=gpermission_check)
            return len([p for p in self.gpermissions.all() if p.code_name == gpermission_check]) > 0
        except:
            return len([p for p in self.gpermissions.all() if p.id == gpermission_check]) > 0

    @property
    def gprofiles_id(self):
        p_ids = self.gprofiles.all().values_list('pk', flat=True)
        return p_ids

    @property
    def gpermissions_id(self):
        p_ids = self.gpermissions.all().values_list('pk', flat=True)
        for gprofile in self.gprofiles.all():
            p_ids = p_ids + gprofile.gpermissions.all().values_list('pk', flat=True)
        return p_ids

    class Meta:
        verbose_name_plural = "Usuarios (Guser)"
        ordering = ['gentity', 'last_name']

    def __unicode__(self):
        return u'%s %s -- %s (%s)' % (self.first_name, self.last_name, self.idcard, self.id)


class Glink(models.Model):
    guser = models.ForeignKey(Guser)
    code = models.CharField("Código", max_length=40)
    link = models.CharField("Enlace", max_length=100)
    deadline = models.DateField('Fecha límite de validez')

    def __unicode__(self):
        return u'%s -- %s (%s)' % (self.link, self.guser, self.deadline)


