# -*- coding: utf-8 -*-
import random
import string

from django.shortcuts import render, redirect
import unicodedata
import csv
from datetime import date, datetime, timedelta
import simplejson as json
import locale

from django.shortcuts import render_to_response
from django.core import serializers
from django.template import RequestContext
from django.db.models import Q, Max
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
import xlrd  # Permite leer archivos xls
from django.forms import ModelForm, Select, SelectMultiple
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_unicode

from gentities.models import Guser, Glink
from gprojects.models import Gproject
from models import *

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
# Create your views here.



def human_resources(request):
    guser = request.user
    try:
        gproject = Gproject.objects.get(Q(id=gproject_id), Q(administrator=guser) | Q(gusers_edit__in=[guser]))
        # The first time gantt() is called there isn't a baseline and we must create it:
        try:
            gbaselines = Gbaseline.objects.filter(gproject=gproject)
            gbaseline = gbaselines.get(active=True)
        except:
            start_datetime = datetime.combine(gproject.start_date, datetime.min.time())
            gbaseline = Gbaseline.objects.create(gproject=gproject, name='First baseline', start_date=start_datetime)
            # It is created a task as a minimum element of a project:
            Gtask.objects.create(gbaseline=gbaseline, name='First task', pos=0)
            gbaselines = [gbaseline]
            # By default two columns are added to the Gantt diagram
            Gcolumn.objects.create(gbaseline=gbaseline, pos=0, content='gtask_name')
            Gcolumn.objects.create(gbaseline=gbaseline, pos=1, content='estimate_time_days')
    except:
        return redirect('/gprojects/', permanent=True)
    if request.method == 'POST':
        if request.POST['action'] == 'create':
            form = GprojectForm(request.POST, instance=Gproject(gentity=request.user.gentity, active=True))
            if form.is_valid():
                gproject = form.save()
                start_datetime = datetime.combine(gproject.start_date, datetime.min.time())
                Gbaseline.objects.create(gproject=gproject, name='First baseline', start_date=start_datetime)
                return redirect('/gprojects/?id=' + str(gproject.id), permanent=True)

    return render_to_response("gantt.html",
                              {
                                  # 'actions':
                                  #     ({'name': 'trash', 'text': 'Borrar', 'permission': 'create_projects',
                                  #       'title': 'Borrar las tareas seleccionadas'},
                                  #      {'name': 'indent', 'text': 'Sangrar', 'permission': 'create_projects',
                                  #       'title': 'Convertir en subtareas de la inmediatamente superior'},
                                  #      {'name': 'dedent', 'text': 'Desangrar', 'permission': 'create_projects',
                                  #       'title': 'Anular su catalogación como subtareas'},
                                  #      {'name': 'random', 'text': 'Links', 'permission': 'create_projects',
                                  #       'title': 'Mostrar/Ocultar enlaces entre tareas'},
                                  #      {'name': 'plus', 'text': 'Add/Insert', 'permission': 'create_projects',
                                  #       'title': 'Añadir o insertar una nueva tarea'},
                                  #      ),
                                  'actions':
                                      ({'name': 'sliders', 'text': 'Operaciones', 'permission': 'create_projects',
                                        'title': 'Operaciones con las tareas seleccionadas', 'type': 'menu'},
                                       {'name': 'trash', 'text': 'Borrar tareas', 'permission': 'create_projects',
                                        'title': 'Borrar las tareas seleccionadas', 'type': 'sliders'},
                                       {'name': 'indent', 'text': 'Hacer subtareas', 'permission': 'create_projects',
                                        'title': 'Convertir en subtareas de la inmediatamente superior',
                                        'type': 'sliders'},
                                       {'name': 'dedent', 'text': 'Deshacer subtareas', 'permission': 'create_projects',
                                        'title': 'Anular su catalogación como subtareas', 'type': 'sliders'},
                                       {'name': 'arrow-down', 'text': 'Mover abajo', 'permission': 'create_projects',
                                        'title': 'Desplazar tarea hacia abajo', 'type': 'sliders'},
                                       {'name': 'arrow-up', 'text': 'Mover arriba', 'permission': 'create_projects',
                                        'title': 'Desplazar tarea hacia arriba', 'type': 'sliders'},
                                       {'name': 'pencil', 'text': 'Editar tarea', 'permission': 'create_projects',
                                        'title': 'Editar propiedades de la tarea', 'type': 'sliders'},
                                       {'name': 'code-fork', 'text': 'Baselines', 'permission': 'create_projects',
                                        'title': 'Operaciones con las baselines del proyecto', 'type': 'menu'},
                                       {'name': 'plus-circle', 'text': 'Nueva baseline',
                                        'permission': 'create_projects',
                                        'title': 'Crear una nueva baseline a partir de la actual', 'type': 'code-fork'},
                                       {'name': 'random', 'text': 'Ocultar/Mostrar', 'permission': 'create_projects',
                                        'title': 'Mostrar/Ocultar enlaces entre tareas', 'type': 'button'},
                                       {'name': 'plus', 'text': 'Nueva tarea', 'permission': 'create_projects',
                                        'title': 'Añadir o insertar una nueva tarea', 'type': 'button'},
                                       ),
                                  'jgprojects': serializers.serialize('json', [gproject]),
                                  'jgbaselines': serializers.serialize('json', gbaselines),
                                  'gbaseline': gbaseline,
                                  'jgtasks': serializers.serialize('json', gbaseline.gtask_set.all().order_by('pos')),
                                  'jgtask_links': serializers.serialize('json', gbaseline.gtask_link_set.all()),
                                  'jgcolumns': serializers.serialize('json', gbaseline.gcolumn_set.all()),
                              },
                              context_instance=RequestContext(request))