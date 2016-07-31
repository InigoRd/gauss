# -*- coding: utf-8 -*-
from django.shortcuts import render

from django.shortcuts import render_to_response
from django.core import serializers
from django.template import RequestContext
from django.db.models import Q, Max
import csv
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
import xlrd  # Permite leer archivos xls
from django.forms import ModelForm, Select, SelectMultiple
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_unicode
from datetime import datetime

from gentities.models import Guser, Glink
from gauss.paths import *
from models import *


# Create your views here.

def gbudgets(request):
    guser = request.user
    data = ''
    try:
        gbudget_id = request.GET['id']
    except:
        gbudget_id = None
    if request.method == 'POST':
        if request.POST['action'] == 'load_bc3':
            if 'bc3' in request.FILES:
                # Firstly, the Budget_file instance is created
                bc3_file = request.FILES['bc3']
                budget_file = Budget_file.objects.create(file=bc3_file, content_type=bc3_file.content_type,
                                                         description="Fichero BC3 cargado")
                gbudget = Gbudget.objects.create(gentity=guser.gentity, title='New budget created from a bc3 file',
                                                 administrator=guser, initial_bc3=budget_file)
                # Secondly, the file is uploaded to /media/budgets/ path
                fnombre = budget_file.file.url
                with open(MEDIA_PATH + fnombre, 'w+') as destination:
                    for chunk in bc3_file.chunks():
                        destination.write(chunk)
                # Last, the file is processed
                with open(MEDIA_PATH + fnombre, "r") as bc3:
                    bc3reader = csv.reader(bc3, delimiter='|')
                    for row in bc3reader:
                        if len(row) > 0:
                            if row[0] == '~V':
                                _parseV(row, gbudget)
                            if row[0] == '~K':
                                _parseK(row, gbudget)
                            if row[0] == '~C':
                                _parseC(row, gbudget)
                            data = data + row[0]

                            # bc3 = open(MEDIA_PATH + fnombre, "r")


                            # for input_file, object_file in request.FILES.items():
                            #     for fichero in request.FILES.getlist(input_file):
                            #         archivo = Fichero.objects.create(fichero=fichero, content_type=fichero.content_type)
                            #         registro.ficheros.add(archivo)

                            # csv_file = open(csv_file_name, "r")



                            # with bc3_file.open() as bc3:
                            #     bc3reader = csv.reader(bc3, delimiter='|')
                            #     for row in bc3reader:
                            #         data = data + row[0]



                            # fichero = csv.DictReader(bc3_file.open(mode='r'), delimiter='|')
                            # for row in fichero:
                            #     # yield [unicode(cell, 'utf-8') for cell in row]
                            #     # create_usuario([unicode(cell, 'utf-8') for cell in row], request)
                            #     if len(row['id_socio']) > 2:
                            #         create_usuario(row, request)

        elif request.POST['action'] == 'create_budget':
            gbudget = Gbudget.objects.create(gentity=request.user.gentity, active=True, name='Nuevo proyecto',
                                             administrator=request.user, notes='', start_date=datetime.today())
            # start_datetime = datetime.combine(gbudget.start_date, datetime.min.time())
            # Gbaseline.objects.create(gbudget=gbudget, name='First baseline', start_date = start_datetime)

    # gresources = Gresource.objects.filter(guser=request.user)
    # gbudgets = Gbudget.objects.filter(Q(removed=False),
    #                                     Q(gresources__in=gresources) | Q(administrator=request.user) | Q(
    #                                         gusers_edit__in=[request.user])).distinct().order_by('-active',
    #                                                                                              'start_date')
    gbudgets = Gbudget.objects.filter(Q(removed=False),
                                      Q(administrator=request.user) | Q(
                                          gusers_edit__in=[request.user])).distinct().order_by('-active',
                                                                                               'start_date')

    return render_to_response("gbudgets.html",
                              {
                                  'actions':
                                      ({'name': 'plus', 'text': 'Nuevo', 'href': '/create_project/',
                                        'title': 'Crear un nuevo proyecto', 'permission': 'create_projects'},
                                       {'name': 'check', 'text': 'Aceptar', 'href': '/create_project/',
                                        'title': 'Crear un nuevo proyecto', 'permission': 'create_projects'},
                                       {'name': 'check', 'text': 'Aceptar', 'permission': 'create_projects',
                                        'title': '', 'type': 'button'},
                                       ),
                                  'gbudgets': gbudgets,
                                  'gbudget_id': gbudget_id,
                                  'data': data
                              },
                              context_instance=RequestContext(request))

def _todate(data):
    if len(data) == 8:
        try:
            return datetime.strptime(data, '%d%m%Y').date()
        except: #it could arise an error if the two first characters are 0, i.e. '00042019'
            return datetime.strptime(data[2:], '%m%Y').date()
    elif len(data) > 4:
        try:
            return datetime.strptime(data, '%d%m%y').date()
        except: #it could arise an error if the two first characters are 0, i.e. '00042019'
            return datetime.strptime(data[2:], '%m%Y').date()
    elif len(data) > 2:
        return datetime.strptime(data, '%m%y').date()
    else:
        return None

def _parseV(data, gbudget):
    """
    ~V | [ PROPIEDAD_ARCHIVO ] | VERSION_FORMATO [ \ DDMMAAAA ] | [ PROGRAMA_EMISION ] |
    [ CABECERA ] \ { ROTULO_IDENTIFICACION \ } | [ JUEGO_CARACTERES ] | [ COMENTARIO ] | [ TIPO INFORMACION ] |
    [ NUMERO CERTIFICACION  ] | [  FECHA CERTIFICACION ] | [ URL_BASE ] |

    data: field list of the record
        0- V :Property and Version
        1- [File_Owner]
        2- Format_Version[\DDMMYYYY]
        3- [Program_Generator]
        4- [Header]\{Title\}
        5- [Chaters_set]
        6- [Comment]
        7- [Data type], it can be: (1, 'Base de datos'), (2, 'Presupuesto'), (3, 'Certificación (a origen)'),
                                                                                (4, u'Actualización de base de datos'))
        8- [Number budget certificate]
        9- [Date budget certificate]
        10- [Url where documents and images can be found]
    """
    try:
        Vrecord.objects.get(gbudget=gbudget)
    except:
        owner = data[1]
        version_date = data[2].split('\\')
        version = version_date[0]
        date = _todate(version_date[1])
        emisor = data[3]
        header = data[4].split('\\')[0]
        char_set = data[5]
        comment = data[6]
        type = int(data[7])
        certification_number = int(data[8])
        certification_date = _todate(data[9]) #datetime.strptime(data[9], '%d%m%Y').date()
        url = data[10]
        vrecord = Vrecord.objects.create(gbudget=gbudget, owner=owner, version=version, date=date, emisor=emisor,
                                         header=header, char_set=char_set, comment=comment, type=type, url=url,
                                         certification_number=certification_number,
                                         certification_date=certification_date)
        titles = data[4].split('\\')[1:]
        pos = 0
        for title in titles:
            Vrecord_label.objects.create(vrecord=vrecord, title=title, pos=pos)
            pos += 1


def _parseK(data, gbudget):
    """
    ~K | { DN \ DD \ DS \ DR \ DI \ DP \ DC \ DM \ DIVISA \ } | CI \ GG \ BI \ BAJA \ IVA |
    { DRC \ DC \ \ DFS \ DRS \ \ DUO \ DI \ DES \ DN \ DD \ DS \ DSP \ DEC \ DIVISA \ } [ n ] |
    The first field only is there because compatibility. We will not read it.
    """

    def int_conv(value, default):
        try:
            val = int(value) if int(value) > 0 else 10
            return val
        except:
            return default

    krecord = Krecord.objects.get_or_create(gbudget=gbudget)[0]
    params2 = data[2].split('\\')
    krecord.ci = float(params2[0])
    krecord.gg = float(params2[1])
    krecord.bi = float(params2[2])
    krecord.baja = float(params2[3])
    krecord.iva = float(params2[4])
    krecord.save()

    params1 = data[1].split('\\')
    params3 = data[3].split('\\')
    if len(params1) > len(params3):
        # len(params1) - 1 because last \ creates a new split element, / 9 because there are 9 splits (fields)
        scopes_range = range((len(params1) - 1) / 9)
        for scope in scopes_range:
            Krecord_scope.objects.create(krecord=krecord, dn=int_conv(params1[0 + scope * 9], 2),
                                         dd=int_conv(params1[1 + scope * 9], 2), ds=int_conv(params1[2 + scope * 9], 2),
                                         drc=int_conv(params1[3 + scope * 9], 3),
                                         di=int_conv(params1[4 + scope * 9], 2),
                                         duo=int_conv(params1[5 + scope * 9], 2),
                                         drs=int_conv(params1[3 + scope * 9], 3),
                                         dc=int_conv(params1[6 + scope * 9], 2),
                                         divisa=int_conv(params1[8 + scope * 9], 2))
    else:
        # len(params3) - 1 because last \ creates a new split element, / 15 because there are 15 splits (fields)
        scopes_range = range((len(params3) - 1) / 15)
        for scope in scopes_range:
            Krecord_scope.objects.create(krecord=krecord, drc=int_conv(params3[0 + scope * 15], 3),
                                         dc=int_conv(params3[1 + scope * 15], 2),
                                         dfs=int_conv(params3[3 + scope * 15], 3),
                                         drs=int_conv(params3[4 + scope * 15], 3),
                                         duo=int_conv(params3[6 + scope * 15], 2),
                                         di=int_conv(params3[7 + scope * 15], 2),
                                         des=int_conv(params3[8 + scope * 15], 2),
                                         dn=int_conv(params3[9 + scope * 15], 2),
                                         dd=int_conv(params3[10 + scope * 15], 2),
                                         ds=int_conv(params3[11 + scope * 15], 2),
                                         dsp=int_conv(params3[12 + scope * 15], 2),
                                         dec=int_conv(params3[13 + scope * 15], 2),
                                         divisa=int_conv(params3[14 + scope * 15], 2))


def _parseC(data, gbudget):
    """
    ~C | CODIGO { \ CODIGO } | [ UNIDAD ] | [ RESUMEN ] | { PRECIO \ } | { FECHA \ } | [ TIPO ] |
    """
    code_syn = data[1].split('\\')
    hierarchy = 2 #Initially the concept is considered a 'normal concept'
    code = code_syn[0]
    if code[-2:] == '##':
        hierarchy = 0 # That means that it is a 'root concept'
        code = code[:-2]
    elif code[-1:] == '#':
        hierarchy = 1 # That means that it is a 'chapter concept'
        code = code[:-1]

    crecord = Crecord.objects.create(gbudget=gbudget, code=code, unit=data[2], summary=data[3], type=data[6],
                                     hierarchy=hierarchy)
    for code in code_syn[1:]:
        if code:
            Crecord_alias.objects.create(crecord=crecord, code=code)
    prices = data[4].split('\\')
    dates = data[5].split('\\')
    next_date = None
    pos = 0
    for price in prices:
        try:
            p = float(price)
            try:
                date = _todate(dates[pos]) # It arises an error if pos > len(dates)
            except:
                date = None
            next_date = date if date else next_date
            Crecord_price.objects.create(crecord=crecord, price=p, date=next_date, pos=pos)
            pos += 1
        except:
            # Price is not a number, then Crecord_price is not created
            pass
