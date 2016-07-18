# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
# Register your models here.
from models import *


class GuserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Guser


class GuserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Guser


class GuserAdmin(UserAdmin):
    form = GuserChangeForm

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': (
        'photo', 'gentity', 'position', 'gdepartment', 'gprofiles', 'gpermissions', 'sex', 'idcard', 'address',
        'postalcode', 'locality', 'province', 'born', 'tel1', 'tel2', 'notes')}),
    )

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("user_permissions")
        self.fieldsets[2][1]["fields"] = ('is_active',)
        form = super(GuserAdmin, self).get_form(request, obj, **kwargs)
        return form


admin.site.register(Guser, GuserAdmin)
admin.site.register(Gentity)
