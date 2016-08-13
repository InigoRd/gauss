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

def parseRecord(record, gbudget):
    # try:
    if record[0] == '~V':
        _parseV(record, gbudget)
    elif record[0] == '~K':
        _parseK(record, gbudget)
    elif record[0] == '~C':
        _parseC(record, gbudget)
    elif record[0] == '~T':
        _parseT(record, gbudget)
    elif record[0] == '~D':
        _parseD(record, gbudget)
    elif record[0] == '~R':
        _parseR(record, gbudget)
    elif record[0] == '~L':
        _parseL(record, gbudget)
    elif record[0] == '~W':
        _parseW(record, gbudget)
    elif record[0] == '~Q':
        _parseQ(record, gbudget)
    elif record[0] == '~J':
        _parseJ(record, gbudget)
    elif record[0] == '~G':
        _parseG(record, gbudget)
    elif record[0] == '~E':
        _parseE(record, gbudget)
    elif record[0] == '~O':
        _parseO(record, gbudget)
    elif record[0] == '~X':
        _parseX(record, gbudget)
    elif record[0] == '~M':
        _parseM(record, gbudget)
    elif record[0] == '~A':
        _parseA(record, gbudget)
    elif record[0] == '~B':
        _parseB(record, gbudget)
    elif record[0] == '~F':
        _parseF(record, gbudget)
    # except:
    #    # warning('Error de lectura en el la línea %s' % "|".join(record)
        # pass

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
                complete_line = ''
                with open(MEDIA_PATH + fnombre, "r") as bc3:
                    current_line = bc3.readline().rstrip('\r\n ') #remove linebreak and spaces
                    while True:
                        next_line = bc3.readline()
                        if not next_line:
                            record = current_line.split('|')
                            parseRecord(record, gbudget)
                            break
                        elif next_line[0] == '~':
                            record = current_line.split('|')
                            current_line = next_line.rstrip('\r\n ')
                            parseRecord(record, gbudget)
                        else:
                            current_line += next_line.rstrip('\r\n ')




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
        except:  # it could arise an error if the two first characters are 0, i.e. '00042019'
            return datetime.strptime(data[2:], '%m%Y').date()
    elif len(data) > 4:
        try:
            return datetime.strptime(data, '%d%m%y').date()
        except:  # it could arise an error if the two first characters are 0, i.e. '00042019'
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
        try:
            version = version_date[0]
            date = _todate(version_date[1])
        except:
            version = version_date[0]
            date = None
        emisor = data[3]
        header = data[4].split('\\')[0]
        char_set = data[5]
        try:
            comment = data[6]
        except:
            comment = ''
        try:
            type = int(data[7])
        except:
            type = 1
        try:
            certification_number = int(data[8])
        except:
            certification_number = None
        try:
            certification_date = _todate(data[9])  # datetime.strptime(data[9], '%d%m%Y').date()
        except:
            certification_date = None
        try:
            url = data[10]
        except:
            url = None
        vrecord = Vrecord.objects.create(gbudget=gbudget, owner=owner, version=version, date=date, emisor=emisor,
                                         header=header, char_set=char_set, comment=comment, type=type, url=url,
                                         certification_number=certification_number,
                                         certification_date=certification_date)
        titles = data[4].split('\\')[1:]
        for title in titles:
            Vrecord_label.objects.create(vrecord=vrecord, title=title)


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
    if len(params2) > 4:
        krecord.ci = float(params2[0])
        krecord.gg = float(params2[1])
        krecord.bi = float(params2[2])
        krecord.baja = float(params2[3])
        krecord.iva = float(params2[4])
        krecord.save()
    elif len(params2) == 4:
        krecord.ci = float(params2[0])
        krecord.gg = float(params2[1])
        krecord.bi = float(params2[2])
        krecord.baja = float(params2[3])
        krecord.iva = 21
        krecord.save()
    elif len(params2) == 3:
        krecord.ci = float(params2[0])
        krecord.gg = float(params2[1])
        krecord.bi = float(params2[2])
        krecord.baja = 0
        krecord.iva = 21
        krecord.save()
    elif len(params2) == 2:
        krecord.ci = float(params2[0])
        krecord.gg = float(params2[1])
        krecord.bi = 0
        krecord.baja = 0
        krecord.iva = 21
        krecord.save()
    else:
        krecord.ci = float(params2[0])
        krecord.gg = 0
        krecord.bi = 0
        krecord.baja = 0
        krecord.iva = 21
        krecord.save()


    vrecord_labels = Vrecord_label.objects.filter(vrecord__gbudget=gbudget).order_by('id')
    params1 = data[1].split('\\')
    params3 = data[3].split('\\')
    if len(params1) > len(params3):
        # len(params1) - 1 because last \ creates a new split element, / 9 because there are 9 splits (fields)
        scopes_range = range((len(params1) - 1) / 9)
        for scope in scopes_range:
            try:
                vrecord_label = vrecord_labels[scope]
                Krecord_scope.objects.create(krecord=krecord, dn=int_conv(params1[0 + scope * 9], 2),
                                             dd=int_conv(params1[1 + scope * 9], 2),
                                             ds=int_conv(params1[2 + scope * 9], 2),
                                             drc=int_conv(params1[3 + scope * 9], 3),
                                             di=int_conv(params1[4 + scope * 9], 2),
                                             duo=int_conv(params1[5 + scope * 9], 2),
                                             drs=int_conv(params1[3 + scope * 9], 3),
                                             dc=int_conv(params1[6 + scope * 9], 2),
                                             divisa=int_conv(params1[8 + scope * 9], 2), vrecord_label=vrecord_label)
            except:
                # That means that there are more krecord_scopes than vrecord_labels. Thus, krecord_scope is not defined
                # because relation between krecord_scopes and vrecord_labels is a bijection
                pass
    else:
        if (len(params3) - 1) % 15 == 0:
            # The especification has a double definition. In this case params3 are defined as:
            # { DRC \ DC \ \ DFS \ DRS \ \ DUO \ DI \ DES \ DN \ DD \ DS \ DSP \ DEC \ DIVISA \ }
            # len(params3) - 1 because last \ creates a new split element, / 15 because there are 15 splits (fields)
            scopes_range = range((len(params3) - 1) / 15)
            for scope in scopes_range:
                try:
                    vrecord_label = vrecord_labels[scope]
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
                                                 divisa=int_conv(params3[14 + scope * 15], 2),
                                                 vrecord_label=vrecord_label)
                except:
                    # That means there are more krecord_scopes than vrecord_labels. Thus, krecord_scope is not defined
                    # because relation between krecord_scopes and vrecord_labels is a bijection
                    pass
        elif (len(params3) - 1) % 13 == 0:
            # The especification has a double definition. In this case params3 are defined as:
            # { DRC \ DC \ DFS \ DRS \ DUO \ DI \ DES \ DN \ DD \ DS \ DSP \ DEC \ DIVISA \ }
            # len(params3) - 1 because last \ creates a new split element, / 13 because there are 13 splits (fields)
            scopes_range = range((len(params3) - 1) / 13)
            for scope in scopes_range:
                try:
                    vrecord_label = vrecord_labels[scope]
                    Krecord_scope.objects.create(krecord=krecord, drc=int_conv(params3[0 + scope * 13], 3),
                                                 dc=int_conv(params3[1 + scope * 13], 2),
                                                 dfs=int_conv(params3[2 + scope * 13], 3),
                                                 drs=int_conv(params3[3 + scope * 13], 3),
                                                 duo=int_conv(params3[4 + scope * 13], 2),
                                                 di=int_conv(params3[5 + scope * 13], 2),
                                                 des=int_conv(params3[6 + scope * 13], 2),
                                                 dn=int_conv(params3[7 + scope * 13], 2),
                                                 dd=int_conv(params3[8 + scope * 13], 2),
                                                 ds=int_conv(params3[9 + scope * 13], 2),
                                                 dsp=int_conv(params3[10 + scope * 13], 2),
                                                 dec=int_conv(params3[11 + scope * 13], 2),
                                                 divisa=int_conv(params3[12 + scope * 13], 2),
                                                 vrecord_label=vrecord_label)
                except:
                    # That means there are more krecord_scopes than vrecord_labels. Thus, krecord_scope is not defined
                    # because relation between krecord_scopes and vrecord_labels is a bijection
                    pass


def get_or_createC(gbudget, code):
    hierarchy = 2
    if code[-2:] == '##':
        hierarchy = 0  # That means that it is a 'root concept'
        code = code[:-2]
    elif code[-1:] == '#':
        hierarchy = 1  # That means that it is a 'chapter concept'
        code = code[:-1]
    try:
        try:
            crecord = Crecord.objects.get(gbudget=gbudget, code=code)
        except:
            crecord_alias = Crecord_alias.objects.get(code=code, crecord__gbudget=gbudget)
            crecord = crecord_alias.crecord
    except:
        crecord = Crecord.objects.create(gbudget=gbudget, code=code, hierarchy=hierarchy)
    return crecord


def _parseC(data, gbudget):
    """
    ~C | CODIGO { \ CODIGO } | [ UNIDAD ] | [ RESUMEN ] | { PRECIO \ } | { FECHA \ } | [ TIPO ] |
    """
    code_syn = data[1].split('\\')
    code = code_syn[0]
    crecord = get_or_createC(gbudget, code)
    crecord.unit = data[2]
    crecord.summary = data[3]
    crecord.type = data[6]
    crecord.save()
    for code in code_syn[1:]:
        if code:
            Crecord_alias.objects.get_or_create(crecord=crecord, code=code)
    prices = data[4].split('\\')
    dates = data[5].split('\\')

    vrecord_labels = Vrecord_label.objects.filter(vrecord__gbudget=gbudget).order_by('id')
    n = 0
    before_price = 0
    before_date = None
    for label in vrecord_labels:  # relation between prices and vrecord_labels is a bijection
        try:
            price = float(prices[n])
            before_price = price
            try:
                date = _todate(dates[n])  # It arises an error if n > len(dates)
            except:
                date = before_date
            before_date = date
            Crecord_price.objects.create(crecord=crecord, price=price, date=date, vrecord_label=label)
            n += 1
        except:
            # This happens because price[n] is not a number, then we select before_price
            Crecord_price.objects.create(crecord=crecord, price=before_price, date=before_date, vrecord_label=label)


def _parseT(data, gbudget):
    """
    ~T | CODIGO_CONCEPTO |  TEXTO_DESCRIPTIVO  |
    """
    code = data[1]
    if code[-2:] == '##':
        code = code[:-2]
    elif code[-1:] == '#':
        code = code[:-1]
    try:
        crecord = Crecord.objects.get(code=code, gbudget=gbudget)
    except:
        crecord_alias = Crecord_alias.objects.get(code=code, crecord__gbudget=gbudget)
        crecord = crecord_alias.crecord
    crecord.text = data[2]
    crecord.save()


def _parseD(data, gbudget):
    """
    ~D | CODIGO_PADRE | < CODIGO_HIJO \ [ FACTOR ] \ [ RENDIMIENTO ] \ > |
    < CODIGO_HIJO \ [ FACTOR ] \ [ RENDIMIENTO ] \ {CODIGO_PORCENTAJE ; } \ > |
    """
    p_code = data[1]

    parent = get_or_createC(gbudget, p_code)
    children1 = data[2].split('\\')
    children2 = data[3].split('\\')
    children = children1 if len(children1) > len(children2) else children2
    n = 3 if len(children1) > len(children2) else 4
    children_range = range((len(children) - 1) / n)
    for i in children_range:
        code = children[0 + i * n]
        child = get_or_createC(gbudget, code)
        factor = children[1 + i * n] if children[1 + i * n] else 1.0
        efficency = children[2 + i * n] if children[2 + i * n] else 1.0
        drecord = Drecord.objects.create(gbudget=gbudget, parent=parent, child=child, factor=factor,
                                         efficency=efficency)
        if n == 4:
            percentages = children[3 + i * n].split(';')
            for percentage in percentages:
                if percentage:
                    Drecord_percentage_code.objects.create(drecord=drecord, percentage_code=percentage)


def _parseR(data, gbudget):
    """
    ~ R | CODIGO_PADRE | { TIPO_DESCOMPOSICION \ CODIGO_HIJO \ { PROPIEDAD \ VALOR \ [UM] \ } | } |
    """
    p_code = data[1]
    parent = get_or_createC(gbudget, p_code)
    children = data[2:]
    for child in children:
        if child:
            t = None  # default value for TIPO_DESCOMPOSICION
            c = None  # default value for CODIGO_HIJO
            info = child.split('\\')
            if len(info) > 1:
                t = info[0]
                c = get_or_createC(gbudget, info[2])
            rrecord = Rrecord.objects.create(gbudget=gbudget, parent=parent, child=c, type=t)
            if len(info) > 3:
                properties = info[2:]
                properties_range = range((len(properties) - 1) / 3)
                for i in properties_range:
                    property = properties[0 + i * 3]
                    value = properties[1 + i * 3]
                    unit = properties[2 + i * 3]
                    Rrecord_property.objects.create(rrecord=rrecord, property=property, value=value, unit=unit)


def _parseW(data, gbudget):
    """
    ~W | < ABREV_AMBITO \ [ AMBITO ] \ > |
    """
    for scope in data[1:]:
        fields = scope.split('\\')
        try:
            wrecord = Wrecord.objects.get(gbudget=gbudget, abbrev=fields[0])
            wrecord.scope = fields[1]
        except:
            Wrecord.objects.create(gbudget=gbudget, abbrev=fields[0], scope=fields[1])


def get_or_createL(gbudget, code):
    try:
        lrecord = Lrecord.objects.get(gbudget=gbudget, section_code=code)
    except:
        lrecord = Lrecord.objects.create(gbudget=gbudget, section_code=code)
    return lrecord


def _parseL(data, gbudget):
    """
    ~L | | < CODIGO_SECCION_PLIEGO \ [ ROTULO_SECCION_PLIEGO ] \ > |

    ~L | CODIGO_CONCEPTO | { CODIGO_SECCION_PLIEGO \ TEXTO_SECCION_PLIEGO \ } |
    { CODIGO_SECCION_PLIEGO \ ARCHIVO_TEXTO_RTF \ } | { CODIGO_SECCION_PLIEGO \ ARCHIVO_TEXTO_HTM \ } |
    """
    if data[1]:  # If data[1] exists the  CODIGO_CONCEPTO must be read
        crecord = get_or_createC(gbudget, data[1])
        if len(data[
                   2]) > 10:  # If CODIGO_SECCION_PLIEGO and TEXTO_SECCION_PLIEGO exist must have a len() bigger than 10
            sections = data[2].split('\\')
            sections_range = range((len(sections) - 1) / 2)
            for i in sections_range:
                lrecord = get_or_createL(gbudget, sections[0 + i * 2])
                text = sections[0 + i * 2]
                Lrecord_section.objects.create(lrecord=lrecord, crecord=crecord, text=text)
        if len(data[3]) > 10:  # If CODIGO_SECCION_PLIEGO and ARCHIVO_TEXTO_RTF exist must have a len() bigger than 10
            sections = data[3].split('\\')
            sections_range = range((len(sections) - 1) / 2)
            for i in sections_range:
                lrecord = get_or_createL(gbudget, sections[0 + i * 2])

                # TODO hay que subir el archivo según la url indicada en ~V
                # budget_file = Budget_file.objects.create(file=bc3_file, content_type=bc3_file.content_type,
                #                                          description="Fichero BC3 cargado")
                # gbudget = Gbudget.objects.create(gentity=guser.gentity, title='New budget created from a bc3 file',
                #                                  administrator=guser, initial_bc3=budget_file)
                # # Secondly, the file is uploaded to /media/budgets/ path
                # fnombre = budget_file.file.url
                # with open(MEDIA_PATH + fnombre, 'w+') as destination:
                #     for chunk in bc3_file.chunks():
                #         destination.write(chunk)

                Lrecord_section.objects.create(lrecord=lrecord, crecord=crecord, text=text)
        if len(data[4]) > 10:  # If CODIGO_SECCION_PLIEGO and ARCHIVO_TEXTO_HTM exist must have a len() bigger than 10
            pass
    else:
        sections = data[2].split('\\')
        sections_range = range((len(sections) - 1) / 2)
        for i in sections_range:
            lrecord = get_or_createL(gbudget, sections[0 + i * 2])
            lrecord.section_title = sections[1 + i * 2]
            lrecord.save()


def _parseQ(data, gbudget):
    """
    ~Q | < CODIGO_CONCEPTO \ > | { CODIGO_SECCION_PLIEGO \ CODIGO_PARRAFO \ { ABREV_AMBITO ; } \ } |
    :param data:
    :param budget:
    :return:
    """
    cs = data[1].split('\\')
    crecords = []
    n = 0
    for c in cs:
        if c:
            crecords[n] = get_or_createC(gbudget, data[1])
            n += 1
    ps = data[2]
    ps_range = range((len(ps) - 1) / 3)
    for i in ps_range:
        lrecord = get_or_createL(gbudget, ps[0 + i * 2])
        paragraph_code = ps[1 + i * 2]
        abbrevs = Wrecord.objects.filter(gbudget=gbudget, abbrev__in=ps[2 + i * 2].split(';'))
        for crecord in crecords:
            qrecord = Qrecord.objects.create(crecord=crecord, lrecord=lrecord, paragraph_code=paragraph_code)
            qrecord.abbrev.add(*abbrevs)


def _parseJ(data, gbudget):
    """
    ~J | CODIGO_PARRAFO | [ TEXTO_PARRAFO ] | | [ ARCHIVO_PARRAFO_RTF ] | [ ARCHIVO_PARRAFO_HTM ] |
    :param data:
    :param gbudget:
    :return:
    """
    try:
        qrecord = Qrecord.objects.get(gbudget=gbudget, paragraph_code=data[1])
        paragraph_text = data[2]
        Jrecord.objects.create(qrecord=qrecord, paragraph_text=paragraph_text)
        # TODO Make _parseJ able to read rtf and html files
    except:
        # Arise an error: qrecord with paragraph_code should be defined before J record
        pass


def _parseG(data, gbudget):
    """
    ~G | CODIGO_CONCEPTO | < ARCHIVO_GRAFICO.EXT \ > | [URL_EXT] |
    :param data:
    :param gbudget:
    :return:
    """
    pass


def _parseE(data, gbudget):
    """
    ~E | CODIGO_ENTIDAD | [ RESUMEN ] | [ NOMBRE ] | { [ TIPO ] \ [ SUBNOMBRE ] \ [ DIRECCIÓN ] \ [ CP ] \
        [ LOCALIDAD ] \ [ PROVINCIA ] \ [ PAIS ] \ { TELEFONO ; } \ { FAX ; } \ { PERSONA_CONTACTO ; } \ } |
        [ CIF ] \ [ WEB ] \ [ EMAIL ] \ |
    :param data:
    :param gbudget:
    :return:
    """
    code = data[1]
    summary = data[2]
    name = data[3]
    several = data[4].split('\\')
    type = several[0]
    subname = several[1]
    address = several[2]
    cp = several[3] if several[3] else None
    location = several[4]
    province = several[5]
    country = several[6]
    tel = several[7]
    fax = several[8]
    contact = several[9]
    cif = data[5].split('\\')[0]
    web = data[5].split('\\')[1]
    email = data[5].split('\\')[2]
    Erecord.objects.create(gbudget=gbudget, code=code, summary=summary, name=name, type=type, subname=subname,
                           address=address, cp=cp, location=location, province=province, country=country,
                           tel=tel, fax=fax, contact=contact, cif=cif, web=web, email=email)


def _parseO(data, gbudget):
    """
    ~O | CODIGO_RAIZ_BD # CODIGO_CONCEPTO | | < CODIGO_ARCHIVO \ CODIGO_ENTIDAD # CODIGO_CONCEPTO \ > |
    :param data:
    :param gbudget:
    :return:
    """
    # Class Orecord has not been defined yet
    pass


def _parseX(data, gbudget):
    """
    ~X | | < CODIGO_IT \ DESCRIPCION_IT \ UM \ > |
    ~X | CODIGO_CONCEPTO | < CODIGO_IT \ VALOR_IT \ > |
    :param data:
    :param gbudget:
    :return:
    """
    if " ".join(data[1].split()):  # In order to remove all blank spaces
        crecord = get_or_createC(gbudget, data[1])
        itcodes = data[2].split('\\')
        itcodes_range = range((len(itcodes) - 1) / 2)
        for i in itcodes_range:
            code = itcodes[0 + i * 2].strip()
            xrecord_ti, created = Xrecord_ti.objects.get_or_create(gbudget=gbudget, ti_code=code)
            if created:
                if code == 'ce':
                    xrecord_ti.description = 'Energetic cost'
                    xrecord_ti.unit = 'MJ'
                elif code == 'eCO2':
                    xrecord_ti.description = 'CO2 emission'
                    xrecord_ti.unit = 'kg'
                elif code == 'ler':
                    xrecord_ti.description = 'ler code provided by the european residue list'
                    xrecord_ti.unit = ''
                elif code == 'm':
                    xrecord_ti.description = 'Mass of the element'
                    xrecord_ti.unit = 'kg'
                elif code == 'v':
                    xrecord_ti.description = 'Volume of the element'
                    xrecord_ti.unit = 'm3'
                xrecord_ti.save()
            Xrecord.objects.create(crecord=crecord, xrecord_ti=xrecord_ti, value=itcodes[1 + i * 2])
    else:
        itcodes = data[2].split('\\')
        itcodes_range = range((len(itcodes) - 1) / 3)
        for i in itcodes_range:
            xrecord_ti = Xrecord_ti.objects.get_or_create(gbudget=gbudget, ti_code=itcodes[0 + i * 3])[0]
            xrecord_ti.description = itcodes[1 + i * 3]
            xrecord_ti.unit = itcodes[2 + i * 3]
            xrecord_ti.save()


def _parseM(data, gbudget):
    """
    ~M | [ CODIGO_PADRE \ ] CODIGO_HIJO | { POSICION \ } | MEDICION_TOTAL |
        { TIPO \ COMENTARIO { # ID_BIM } \ UNIDADES \ LONGITUD \ LATITUD \ ALTURA \ } | [ ETIQUETA ] |
    :param data:
    :param gbudget:
    :return:
    """
    p_c = " ".join(data[1].split()).split('\\')  # The first join and split are to remove all blank spaces
    if len(p_c) == 2:
        parent = get_or_createC(gbudget, p_c[0])
        child = get_or_createC(gbudget, p_c[1])
    else:
        parent = None
        child = get_or_createC(gbudget, p_c[0])
    pos = data[2].split('\\')[:-1]  # Breakdown position eliminating last \
    if len(pos) == 1:
        cpos, spos, ipos = None, None, pos[0]
    elif len(pos) == 2:
        cpos, spos, ipos = pos[0], None, pos[1]
    elif len(pos) == 3:
        cpos, spos, ipos = pos[0], pos[1], pos[2]
    else:
        cpos, spos, ipos = pos[0], pos[1], pos[2]

    m_total = data[3]
    label = data[5]
    mrecord = Mrecord.objects.create(parent=parent, child=child, cpos=cpos, spos=spos, ipos=ipos, m_total=m_total,
                                     label=label)
    m_ts = data[4].split('\\')
    m_ts_range = range((len(m_ts) - 1) / 6)
    for i in m_ts_range:
        t = m_ts[0 + i * 6] if m_ts[0 + i * 6] in [1, 2, 3, '1', '2', '3'] else 0
        comment_bims = m_ts[1 + i * 6].split('#')
        comment = comment_bims[0]
        id_bims = comment_bims[1:]
        units = m_ts[2 + i * 6] if m_ts[2 + i * 6] else None
        longitude = m_ts[3 + i * 6] if m_ts[3 + i * 6] else None
        latitude = m_ts[4 + i * 6] if m_ts[4 + i * 6] else None
        height = m_ts[5 + i * 6] if m_ts[5 + i * 6] else None
        mrecord_type = Mrecord_type.objects.create(mrecord=mrecord, type=t, comment=comment, units=units,
                                                   longitude=longitude, latitude=latitude, height=height)
        for id_bim in id_bims:
            id = Id_bim.objects.get_or_create(id_bim=id_bim)[0]
            mrecord_type.id_bims.add(id)


def _parseA(data, gbudget):
    """
    ~A | CODIGO_CONCEPTO | < CLAVE_TESAURO \ > |
    :param data:
    :param gbudget:
    :return:
    """
    crecord = get_or_createC(gbudget, "".join(data[1].split()))  # The split and join is to remove all blank spaces
    keys = "".join(data[2].split()).split('\\')
    for key in keys:
        Arecord.objects.create(crecord=crecord, key=key)


def _parseB(data, gbudget):
    """
    ~B | CODIGO_CONCEPTO | CODIGO_NUEVO |
    :param data:
    :param gbudget:
    :return:
    """
    old_code = "".join(data[1].split())
    new_code = "".join(data[2].split())
    crecord = get_or_createC(gbudget, old_code)  # The split and join is to remove all blank spaces
    crecord.code = new_code
    crecord.save()
    Crecord_alias.objects.create(crecord=crecord, code=old_code)


def _parseF(data, gbudget):
    """
    ~F | CODIGO_CONCEPTO | { TIPO \  { ARCHIVO.EXT ; } \ [ DESCRIPCION_ARCHIVO ] \ } | [URL_EXT] |
    :param data:
    :param gbudget:
    :return:
    """
    crecord = get_or_createC(gbudget, "".join(data[1].split()))  # The split and join is to remove all blank spaces
    url = data[3]
    frecord = Frecord.objects.create(crecord=crecord, url=url)
    f_files = data[2].split('\\')
    f_files_range = range((len(f_files) - 1) / 3)
    for i in f_files_range:
        type = f_files[0 + i * 3]
        description = f_files[2 + i * 3]
        frecord_files = Frecord_files.objects.create(frecord=frecord, type=type, description=description)
        for f in f_files[1 + i * 3].split(';')[:-1]:
            # 1. open f
            # 2. create Gbudget_file
            # 3. frecord_files.files.add(Gbudget_file)
            pass
