# -*- coding: utf-8 -*-
import random
import string

from django.shortcuts import render, redirect
import unicodedata
import csv
from datetime import date, datetime, timedelta
import simplejson as json

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
import xlrd  # Permite leer archivos xls
from django.forms import ModelForm
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_unicode

from gmessages.views import create_queue_mail

# from gauss.rutas import *
# from gauss.funciones import usuarios_de_gauss, pass_generator
# from models import glink, Gauser_extra, Permiso, Gauser
# from mensajes.views import crear_aviso, crea_mensaje_cola
# from mensajes.models import Aviso, Mensaje
# from entidades.models import Subentidad, Cargo, Entidad
# from bancos.views import asocia_banco_ge
# from menu.models import Menu
# from control_acceso import access_required, LogGauss
# from gauss.funciones import html_to_pdf


# Las siguientes 3 líneas y la nº 114 (o alrededor) que contiene la variable "user_language" son para establecer
# El español como idioma por defecto a través de una variable de sessión
from django.utils import translation

from gentities.models import Guser, Glink, Gentity

user_language = 'es'
translation.activate(user_language)

# TRAS LA AUTENTICACIÓN SE CREAN LAS SIGUIENTES VARIABLES DE SESIÓN:
# request.session["gauser_extra"], que instancia la relación del usuario con el entidad
# ( Con estas dos variables y las asociadas a los usuarios aportadas por request.user se dispone de toda la información referente
# al usuario y al entidad con el que está actuando en GAUSS en la sesión actual )
# request.session["lateral"], que proporciona la información necesaria para que GAUSS cree el menú lateral
# Estas variables de sesión no hay que pasarlas en cada una de las views porque en settings.py se ha añadido la línea:
# "django.core.context_processors.request", a TEMPLATE_CONTEXT_PROCESSORS. Con esto se puede acceder a las variables de sesión
# llamándolas request.session.variable_sesión

from django import forms
from captcha.fields import CaptchaField


class CaptchaForm(forms.Form):
    captcha = CaptchaField()


def pass_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


def crea_menu(u):
    menus = Menu.objects.filter(entidad=u.entidad, acceso=True).order_by('code_menu')
    lateral = render_to_string('menu.html', {'g_e': u, 'menus': menus})
    lateral_off_canvas = render_to_string('menu_off_canvas.html', {'g_e': u, 'menus': menus})
    return lateral, lateral_off_canvas


def seek_users(request):
    text = request.GET['q']
    gusers = Guser.objects.filter(Q(gentity=request.user.gentity), ~Q(username='gauss'),
                                  Q(first_name__icontains=text) | Q(last_name__icontains=text)).values_list('id',
                                                                                                            'last_name',
                                                                                                            'first_name',
                                                                                                            'gdepartment__name')
    keys = ('id', 'last_name', 'first_name', 'department')
    # from django.core import serializers
    # data = serializers.serialize('json', socios2, fields=('gauser__first_name', 'id'))
    return JsonResponse([dict(zip(keys, row)) for row in gusers], safe=False)


def recover_password(request):
    data = {'reveal': '', 'email': '', 'form': ''}
    if request.method == 'POST':
        if request.POST['action'] == 'reload_captcha' and request.is_ajax():
            return HttpResponse(render_to_string("captcha.html", {'form': CaptchaForm()}))
        else:
            data['reveal'] = 'afasfda'
            form = CaptchaForm(request.POST)
            data['email'] = request.POST['email']
            if form.is_valid():
                gusers = Guser.objects.filter(email=request.POST['email'], is_active=True)
                if gusers.count() > 0:
                    glinks = []
                    for guser in gusers:
                        glinks.append(Glink.objects.create(guser=guser, code=pass_generator(size=40),
                                                           link='/set_password/',
                                                           deadline=date.today() + timedelta(days=2)))
                    mail_text = render_to_string("mail_recover_password.html", {'glinks': glinks},
                                                 context_instance=RequestContext(request))
                    # create_queue_mail(to=request.POST['email'], subject="Recuperar contraseña GAUSS Project",
                    #                   html=mail_text)
                    data['reveal'] = 'reveal_check_correct'
                else:
                    data['reveal'] = 'reveal_check_email'
            else:
                data['reveal'] = 'reveal_check_captcha'
    data['form'] = CaptchaForm()
    return render_to_response("recover_password.html", data, context_instance=RequestContext(request))


# @LogGauss
def index(request):
    # dominio = request.META['HTTP_HOST'].split('.')[0]
    # entidad = Gentity.objects.get(domain=dominio)
    if request.method == 'POST':
        if 'action' in request.POST:
            usuario = request.POST['usuario']
            passusuario = request.POST['passusuario']
            guser = authenticate(username=usuario, password=passusuario)
            if guser is not None:
                if guser.is_active:
                    login(request, guser)
                    # request.session["hoy"] = datetime.today()
                    request.session[translation.LANGUAGE_SESSION_KEY] = user_language
                    return redirect('/gprojects/', permanent=True)
                else:
                    return render_to_response("no_account.html", {}, context_instance=RequestContext(request))
            else:
                # Aviso.objects.create(usuario=Gauser_extra.objects.get(id=1), aviso="Usuario no reconocido", fecha=date.today())
                # return HttpResponseRedirect(reverse('autenticar.views.index'))
                logout(request)
                return render_to_response("autenticar.html", {}, context_instance=RequestContext(request))
    else:
        logout(request)
        return render_to_response("autenticar.html", {}, context_instance=RequestContext(request))



# @LogGauss
def enlazar(request):
    # #crear_aviso(request, True, 'enlazar')
    try:
        # #crear_aviso(request, True, 'try')
        g_e = Guser.objects.get(id=request.GET['u'])
        # crear_aviso(request, True, 'g_e')
        glink = Glink.objects.get(usuario=g_e.gauser, code=request.GET['c'])
        # crear_aviso(request, True, 'glink')
        if glink.usuario.is_active:
            # crear_aviso(request, True, 'activo')
            if (glink.deadline > date.today()):
                # crear_aviso(request, True, 'today')
                glink.usuario.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, glink.usuario)
                request.session["gauser_extra"] = g_e
                request.session["lateral"], request.session["lateral_off_canvas"] = crea_menu(g_e)
                request.session['num_items_page'] = 15
                # crear_aviso(request, True,
                # glink.usuario.get_full_name() + u' se loguea en el GAUSS a través de un glink')
                return render_to_response("enlazar.html", {'page': glink.glink},
                                          context_instance=RequestContext(request))
            else:
                # crear_aviso(request, True, 'no today')
                return render_to_response("no_glink.html", {'usuario': glink.usuario,},
                                          context_instance=RequestContext(request))
        else:
            return render_to_response("no_account.html", {'usuario': glink.usuario,},
                                      context_instance=RequestContext(request))
    except:
        logout(request)
        form = CaptchaForm()
        return render_to_response("autenticar.html", {'form': form, 'email': 'aaa@aaa', 'tipo': 'acceso'},
                                  context_instance=RequestContext(request))


def no_login(request):
    pag = request.GET['next']
    return render_to_response("no_login.html", {'pag': pag,}, context_instance=RequestContext(request))


@login_required()
def vistageneral(request):
    # contenido = '/home/juanjo/django/gauss/static_files/files/cal.svg'
    try:
        fichero = PATH_FILES + 'principal_' + str(request.session['entidad'].code) + '.svg'
        contenido = open(fichero, 'r').read()
    except:
        contenido = ''
        # if request.GET['next'] != '':
        # #crear_aviso(request,False,u"Aunque estás autenticado, no tienes acceso a la página seleccionada.")
    avisos = Aviso.objects.filter(usuario=request.session["gauser_extra"], aceptado=False)
    return render_to_response("principal.html", {'contenido': contenido, 'avisos': avisos},
                              context_instance=RequestContext(request))


# ------------------------------------------------------------------#
# DEFINICIÓN DE FUNCIONES BÁSICAS
# ------------------------------------------------------------------#

# Crear el nombre de usuario a partir del nombre real
def crear_nombre_usuario(nombre, apellidos):
    # En primer lugar quitamos tildes, colocamos nombres en minúsculas y :
    nombre = ''.join(
        (c for c in unicodedata.normalize('NFD', smart_unicode(nombre)) if
         unicodedata.category(c) != 'Mn')).lower().split()
    apellidos = ''.join(
        (c for c in unicodedata.normalize('NFD', smart_unicode(apellidos)) if
         unicodedata.category(c) != 'Mn')).lower().split()
    iniciales_nombre = ''
    for parte in nombre:
        iniciales_nombre = iniciales_nombre + parte[0]
    try:
        iniciales_apellidos = apellidos[0]
    except:  # Estas dos líneas están para crear usuarios cuando no tienen apellidos
        iniciales_apellidos = 'sin'
    for ind in range(len(apellidos))[1:]:
        try:  # Por si acaso el usuario sólo tuviera un apellido:
            iniciales_apellidos = iniciales_apellidos + apellidos[ind][0]
        except IndexError:
            pass
    usuario = iniciales_nombre + iniciales_apellidos
    valid_usuario = False
    n = 1
    while valid_usuario == False:
        username = usuario + str(n)
        try:
            user = Gauser.objects.get(username=username)
            n += 1
        except:
            valid_usuario = True
    return username


def devuelve_fecha(string):
    DATE_FORMATS = ['%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y']
    for date_format in DATE_FORMATS:
        try:
            fecha = datetime.strptime(string, date_format)
            return fecha
        except:
            pass
    return datetime.strptime('01/01/2000', '%d/%m/%Y')


def create_usuario_tutor(datos, request):
    g_e = request.session['gauser_extra']

    if len(datos['dni_tutor']) > 2:  # comprobar si tiene dni. Sin dni no se crea usuario
        try:
            gauser = Gauser.objects.get(dni=datos['dni_tutor'])
            # crear_aviso(request, True, u'Existe el Gauser para el tutor')
        except:  # Si se produce esta excepción es porque el usuario no existe y hay que crearlo
            # crear_aviso(request, True, u'No existe el gauser para el tutor y se procede a su creación')
            nombre = datos['nombre_tutor']
            apellidos = datos['apellidos_tutor']
            usuario = crear_nombre_usuario(nombre, apellidos)
            # el dni es el datos[0] y el email es datos[4]. Usuario, mail y password
            gauser = Gauser.objects.create_user(usuario, datos['email_tutor'].lower(), datos['dni_tutor'])
            gauser.first_name = nombre.title()[0:28]
            gauser.last_name = apellidos.title()[0:28]
            propiedades = ['dni', 'telfij', 'telmov', 'address', 'postalcode', 'localidad', 'provincia', 'sexo',
                           'nacimiento', 'fecha_alta']
            headnames = ['dni_tutor', 'telefono_fijo_tutor', 'telefono_movil_tutor', 'direccion_tutor', 'cp_tutor',
                         'localidad_tutor', 'provincia_tutor', 'sexo_tutor',
                         'nacimiento_tutor', 'fecha_alta_tutor']
            for ind, val in enumerate(headnames):
                if val in datos:
                    if val == 'nacimiento_tutor':
                        gauser.nacimiento = devuelve_fecha(datos[val])
                    elif val == 'fecha_alta_tutor':
                        gauser.fecha_alta = devuelve_fecha(datos[val])
                    else:
                        setattr(gauser, propiedades[ind], datos[val])
            gauser.save()

        try:
            gauser_extra = Gauser_extra.objects.get(gauser=gauser, ronda=g_e.ronda, entidad=g_e.entidad)
            # crear_aviso(request, True, u'Existe el Gauser_extra para el tutor')
            if 'subentidades_tutor' in datos:
                # La siguientes dos líneas no se si funcionarán en python3 debido a que filter en python3 no devuelve
                # una lista. Incluida la conversión list() para evitar errores.
                subentidades_id = list(filter(None, datos['subentidades_tutor'].replace(' ', '').split(',')))
                subentidades = Subentidad.objects.filter(id__in=subentidades_id, entidad=g_e.entidad)
                gauser_extra.subentidades.add(*subentidades)
            if 'perfiles_tutor' in datos:
                # La siguientes dos líneas no se si funcionarán en python3 debido a que filter en python3 no devuelve
                # una lista. Incluida la conversión list() para evitar errores.
                cargos_id = list(filter(None, datos['perfiles'].replace(' ', '').split(',')))
                cargos = Cargo.objects.filter(id__in=cargos_id, entidad=g_e.entidad)
                gauser_extra.subentidades.add(*cargos)
        except:  # Si se produce exta excepción hay que crear el Gauser_extra correspondiente
            # crear_aviso(request, True, u'No existe el Gauser_extra para el tutor y se procede a su creación')
            gauser_extra = Gauser_extra.objects.create(gauser=gauser, entidad=g_e.entidad, ronda=g_e.ronda, activo=True,
                                                       id_asociacion=datos['id_socio_tutor'],
                                                       num_cuenta_bancaria=datos['iban_tutor'],
                                                       observaciones=datos['observaciones_tutor'])

            try:
                asocia_banco_ge(gauser_extra)
            except:
                pass
                # crear_aviso(request, False,
                # u'El IBAN asociado a %s parece no ser correcto. No se ha podido asociar una entidad bancaria al mismo.' % (
                #     gauser.first_name.decode('utf8') + ' ' + gauser.last_name.decode('utf8')))

            if 'subentidades_tutor' in datos:
                # La siguientes dos líneas no se si funcionarán en python3 debido a que filter en python3 no devuelve
                # una lista. Incluida la conversión list() para evitar errores.
                subentidades_id = list(filter(None, datos['subentidades_tutor'].replace(' ', '').split(',')))
                subentidades = Subentidad.objects.filter(id__in=subentidades_id, entidad=g_e.entidad)
                gauser_extra.subentidades.add(*subentidades)
            else:
                pass
                # crear_aviso(request, False,
                # u'No se ha podido asignar ningún departamento o sección al usuario.' % (
                #     gauser.first_name.decode('utf8') + ' ' + gauser.last_name.decode('utf8')))

            if 'perfiles_tutor' in datos:
                # La siguientes dos líneas no se si funcionarán en python3 debido a que filter en python3 no devuelve
                # una lista. Incluida la conversión list() para evitar errores.
                cargos_id = list(filter(None, datos['perfiles'].replace(' ', '').split(',')))
                cargos = Cargo.objects.filter(id__in=cargos_id, entidad=g_e.entidad)
                gauser_extra.subentidades.add(*cargos)
            gauser_extra.save()
        menus = Menu.objects.filter(entidad=g_e.entidad, acceso=True, tipo='Global').values_list('code_menu')
        permisos = Permiso.objects.filter(code_nombre__in=menus)
        gauser_extra.permisos.add(*permisos)
        return gauser_extra
    else:
        # crear_aviso(request, True,
        # u'El tutor a crear no tiene DNI y se cancela la creación. Valor asignado al tutor: None')
        return None


def create_usuario(datos, request):
    g_e = request.session['gauser_extra']
    try:
        # Si encuentra un usuario con el id indicado no dará error y por tanto no lo grabará
        # Sólo grabamos nuevos usuarios
        Gauser_extra.objects.get(id_asociacion=datos['id_socio'])
        # crear_aviso(request, False,
        # u'Ya hay un usuario creado con el identificador %s, por esta razón %s %s no se carga/actualiza a través de este fichero' % (
        #     datos['id_socio'], datos['nombre'].decode('utf8'), datos['apellidos'].decode('utf8')))
    except:
        # Si se da esta situación quiere decir que no existe un Gauser asociado y debemos crearlo
        # crear_aviso(request, True,
        # u'No existe el Gauser para el usuario %s %s y se procede a la creación' % (
        #     smart_unicode(datos['nombre']), smart_unicode(datos['apellidos'])))
        nombre = datos['nombre']
        apellidos = datos['apellidos']
        usuario = crear_nombre_usuario(nombre, apellidos)
        gauser = Gauser.objects.create_user(usuario, datos['email'].lower(), datos['dni'])
        gauser.first_name = nombre.title()[0:28]
        gauser.last_name = apellidos.title()[0:28]
        propiedades = ['dni', 'telfij', 'telmov', 'address', 'postalcode', 'localidad', 'provincia', 'sexo',
                       'nacimiento', 'fecha_alta']
        headnames = ['dni', 'telefono_fijo', 'telefono_movil', 'direccion', 'cp', 'localidad', 'provincia', 'sexo',
                     'nacimiento', 'fecha_alta']
        for ind, val in enumerate(headnames):
            if val in datos:
                if val == 'nacimiento':
                    gauser.nacimiento = devuelve_fecha(datos[val])
                elif val == 'fecha_alta':
                    gauser.fecha_alta = devuelve_fecha(datos[val])
                else:
                    setattr(gauser, propiedades[ind], datos[val])
        gauser.save()
        id_organizacion = datos['id_organizacion'] if 'id_organizacion' in datos else datos['id_socio']
        gauser_extra = Gauser_extra.objects.create(gauser=gauser, entidad=g_e.entidad, ronda=g_e.ronda, activo=True,
                                                   id_asociacion=datos['id_socio'], num_cuenta_bancaria=datos['iban'],
                                                   observaciones=datos['observaciones'],
                                                   id_organizacion=id_organizacion)

        # create_usuario_tutor([dni, apellidos,nombre,móvil,email,observaciones])
        datos_tutor = {'dni_tutor': '', 'apellidos_tutor': '', 'nombre_tutor': '', 'telefono_fijo_tutor': '',
                       'telefono_movil_tutor': '', 'email_tutor': '', 'observaciones_tutor': '', 'sexo_tutor': '',
                       'iban_tutor': '', 'direccion_tutor': '', 'localidad_tutor': '', 'provincia_tutor': '',
                       'cp_tutor': '', 'nacimiento_tutor': '', 'id_socio_tutor': '', 'subentidades_tutor': '',
                       'perfiles_tutor': ''}
        for ind in ['1', '2']:
            for h in datos_tutor:
                if (h + ind) in datos:
                    datos_tutor[h] = datos[h + ind]
            setattr(gauser_extra, 'tutor' + ind, create_usuario_tutor(datos_tutor, request))
        # for h in headnames1:
        # if h in datos:
        # datos_tutor[h[:-1]] = datos[h]
        # tutor1 = create_usuario_tutor(datos_tutor, request)
        # datos_tutor = {'dni_tutor': '', 'apellidos_tutor': '', 'nombre_tutor': '', 'telefono_fijo_tutor': '',
        # 'telefono_movil_tutor': '', 'email_tutor': '', 'observaciones_tutor': '', 'sexo_tutor': ''}
        # for h in headnames2:
        # if h in datos:
        #         datos_tutor[h[:-1]] = datos[h]
        # tutor2 = create_usuario_tutor(datos_tutor, request)
        #
        # if 'id_organizacion' in datos:
        #     id_organizacion = datos['id_organizacion']
        # else:
        #     id_organizacion = datos['id_socio']
        # # Será necesario crear también un Gauser_extra
        # gauser_extra = Gauser_extra.objects.create(gauser=gauser, entidad=g_e.entidad, ronda=g_e.ronda, activo=True,
        #                                            id_asociacion=datos['id_socio'], tutor1=tutor1, tutor2=tutor2,
        #                                            num_cuenta_bancaria=datos['iban'],
        #                                            observaciones=datos['observaciones'],
        #                                            id_organizacion=id_organizacion)
        try:
            asocia_banco_ge(gauser_extra)
        except:
            pass
            # crear_aviso(request, False,
            # u'El IBAN asociado a %s parece no ser correcto. No se ha podido asociar una entidad bancaria al mismo.' % (
            #     gauser.first_name.decode('utf8') + ' ' + gauser.last_name.decode('utf8')))
        if 'subentidades' in datos:
            # La siguientes dos líneas no se si funcionarán en python3 debido a que filter en python3 no devuelve
            # una lista. Incluida la conversión list() para evitar errores.
            subentidades_id = list(filter(None, datos['subentidades'].replace(' ', '').split(',')))
            subentidades = Subentidad.objects.filter(id__in=subentidades_id, entidad=g_e.entidad)
            gauser_extra.subentidades.add(*subentidades)
        if 'perfiles' in datos:
            # La siguientes dos líneas no se si funcionarán en python3 debido a que filter en python3 no devuelve
            # una lista. Incluida la conversión list() para evitar errores.
            cargos_id = list(filter(None, datos['perfiles'].replace(' ', '').split(',')))
            cargos = Cargo.objects.filter(id__in=cargos_id, entidad=g_e.entidad)
            gauser_extra.subentidades.add(*cargos)
        gauser_extra.save()
        menus = Menu.objects.filter(entidad=g_e.entidad, acceso=True, tipo='Global').values_list('code_menu')
        permisos = Permiso.objects.filter(code_nombre__in=menus)
        gauser_extra.permisos.add(*permisos)


# @access_required
@login_required()
def carga_masiva(request):
    if request.method == 'POST':
        # crear_aviso(request, True, u'Carga de archivo de tipo: ' + request.FILES['file_masivo'].content_type)
        ronda = request.session['gauser_extra'].ronda
        if 'excel' in request.FILES['file_masivo'].content_type:
            # Las siguientes líneas son para leer el archivo de usuarios y añadirlos al sistema
            # Cargamos el fichero y definimos el índice de cada uno de los campos para que posteriormente puedan referenciarse:
            book = xlrd.open_workbook(file_contents=request.FILES['file_masivo'].read())
            sh = book.sheet_by_index(0)

            # Iniciamos un forloop para recorrer todas las filas del archivo (no la primera que contiene nombre de los campos)
            datos_file = []
            for i in range(sh.nrows)[2:]:
                fila = []
                for col in range(sh.ncols):
                    fila.append(unicodedata.normalize('NFC', unicode(sh.cell_value(rowx=i, colx=col))))
                # Después de leer toda las columnas de la fila se ordena la creación del usuario
                create_usuario(fila, request)
        elif 'csv' in request.FILES['file_masivo'].content_type:
            # Las siguientes líneas son para leer el archivo de usuarios y añadirlos al sistema
            # Cargamos el fichero y definimos el índice de cada uno de los campos para que posteriormente puedan referenciarse:
            csv_file_name = '%scsv_data.csv' % (MEDIA_FILES)
            csv_file = open(csv_file_name, 'w+')
            fichero = request.FILES['file_masivo']
            with csv_file as destination:
                for chunk in fichero.chunks():
                    destination.write(chunk)

            csv_file = open(csv_file_name, "r")
            fichero = csv.DictReader(csv_file, delimiter=';')
            for row in fichero:
                # yield [unicode(cell, 'utf-8') for cell in row]
                # create_usuario([unicode(cell, 'utf-8') for cell in row], request)
                if len(row['id_socio']) > 2:
                    create_usuario(row, request)
        else:
            pass
            # crear_aviso(request, False, u'El archivo cargado no tiene el formato adecuado.')

    return render_to_response("carga_masiva.html",
                              {
                                  'actions': ({'tipo': 'button', 'nombre': 'check', 'texto': 'Aceptar',
                                              'title': 'Aceptar los cambios realizados', 'permiso': 'm20i20'}, {}),
                                  'formname': 'carga_masiva',
                                  'avisos': Aviso.objects.filter(usuario=request.session["gauser_extra"],
                                                                 aceptado=False),
                              },
                              context_instance=RequestContext(request))


class Gauser_per_Form(ModelForm):
    class Meta:
        model = Guser
        fields = ('gpermissions', 'gprofiles')


# @access_required
@login_required()
def perfiles_permisos(request):
    g_e = request.session['gauser_extra']
    usuarios = Gauser_extra.objects.filter(entidad=g_e.entidad, ronda=g_e.ronda).distinct()
    gauser_extra = usuarios[0]
    form = Gauser_per_Form(instance=gauser_extra)
    if request.method == 'POST':
        # crear_aviso(request, True, u'Entra en ' + request.META['PATH_INFO'] + ' POST action: ' + request.POST['action'])
        if request.POST['action'] == 'gauser_extra_selected':
            gauser_extra = Gauser_extra.objects.get(id=request.POST['gauser_extra_selected'])
            form = Gauser_per_Form(instance=gauser_extra)

        if request.POST['action'] == 'aceptar':
            gauser_extra = Gauser_extra.objects.get(id=request.POST['gauser_extra_selected'])
            form = Gauser_per_Form(request.POST, instance=gauser_extra)
            if form.is_valid():
                form.save()

    menus = Menu.objects.filter(entidad=g_e.entidad, acceso=True).order_by('code_menu')

    respuesta = {
        'formname': 'permisos_perfiles',
        'form': form,
        'actions':
            ({'tipo': 'search', 'title': 'Buscar usuario por nombre', 'permiso': 'm20i15'},
             {'tipo': 'button', 'nombre': 'check', 'texto': 'Aceptar',
              'title': 'Aceptar los cambios realizados', 'permiso': 'm20i15'},
             ),
        'gauser_extra': gauser_extra,
        'avisos': Aviso.objects.filter(usuario=g_e, aceptado=False),
        'cargos': Cargo.objects.filter(
            entidad=g_e.entidad).order_by('nivel'),
        'menus': menus,
    }
    return render_to_response("perfiles_permisos.html", respuesta, context_instance=RequestContext(request))


@login_required()
def permisos_asociados(request):
    if request.is_ajax():
        ids = json.loads(request.POST['ids'])
        permisos_id = set(Cargo.objects.filter(id__in=ids).values_list('permisos__id', flat=True))
        permisos = list(Permiso.objects.filter(id__in=permisos_id).values_list('nombre', flat=True))
        data = json.dumps(permisos)
        return HttpResponse(data)
    else:
        return HttpResponse(status=400)


@login_required()
def acceso_menu(request):
    g_e = request.session['gauser_extra']
    menus = Menu.objects.filter(entidad=g_e.entidad, acceso=True, tipo='Global').values_list('code_menu')
    permisos = Permiso.objects.filter(code_nombre__in=menus)
    socios = usuarios_de_gauss(g_e.entidad)
    for socio in socios:
        socio.permisos.add(*permisos)

    return HttpResponse()


@login_required()
def asign_permisos(request, g_e):
    menus = Menu.objects.filter(entidad=g_e.entidad, acceso=True, tipo='Global').values_list('code_menu')
    permisos = Permiso.objects.filter(code_nombre__in=menus)
    g_e.permisos.add(*permisos)
    return HttpResponse()


@login_required()
def asign_permisos2(request, gauser_extra):
    g_e = gauser_extra
    p_ids = g_e.perfiles.all().values_list('id', flat=True)

    # 300: Acceso a menú calendario
    # 350: Acceso al menú: Correo y mensajería
    # 450: Acceso al menú: Actividades de la asociación
    # 455: Puede ver actividades
    # 470: Puede ver reuniones de rama
    permisos = Permiso.objects.filter(id__in=[300, 350, 450, 455, 470])
    g_e.permisos.add(*permisos)

    if len([perfil for perfil in p_ids if
            perfil in [20, 25, 30]]) > 0:  # Coordinador(20), #Informático(25), #Secretario(30)
        # 45: Acceso al menu: Gestión de la Asociación
        # 50: Puede modificar los datos de la Asociación
        # 51: Acceso al submenú: Gestión económica
        # 70: Puede ver datos de padres y madres
        # 80: Puede modificar datos de padres y madres
        # 90: Puede ver datos de los voluntarios
        # 100: Puede modificar datos de voluntarios
        # 110: Puede ver datos de los educandos
        # 115: Puede modificar datos de los educandos
        # 116: Puede ver datos de los socios adultos
        # 117: Puede modificar datos de los socios adultos
        # 460: Puede añadir actividades
        # 465: Puede modificar actividades
        permisos = Permiso.objects.filter(id__in=[45, 50, 51, 70, 80, 90, 100, 110, 115, 116, 117, 460, 465])
        g_e.permisos.add(*permisos)

    if len([perfil for perfil in p_ids if perfil in [35, ]]) > 0:  # Tesorero(35)
        # 45: Acceso al menu: Gestión de la Asociación
        # 51: Acceso al submenú: Gestión económica
        # 52: Puede crear presupuestos para el grupo
        # 53: Puede registrar gastos e ingresos generales
        # 55: Crea política de cuotas
        # 60: Emite remesas bancarias
        # 70: Puede ver datos de padres y madres
        # 90: Puede ver datos de los voluntarios
        # 110: Puede ver datos de los educandos
        # 116: Puede ver datos de los socios adultos
        permisos = Permiso.objects.filter(id__in=[45, 51, 52, 53, 55, 60, 70, 90, 110, 116])
        g_e.permisos.add(*permisos)

    if len([perfil for perfil in p_ids if perfil in [75, ]]) > 0:  # Voluntario(75)
        # 460: Puede añadir actividades
        # 472: Puede añadir reuniones de rama
        # 292: Puede ver padres y madres de su rama
        # 294: Puede ver educandos de su rama
        permisos = Permiso.objects.filter(id__in=[460, 472])
        g_e.permisos.add(*permisos)

    if len([perfil for perfil in p_ids if perfil in [20, 30]]) > 0:  # Coordinador(20), #Secretario(30)
        # 55: Crea política de cuotas
        # 67: Gestiona bajas de socios
        # 68: Puede dar de baja a socios
        # 69: Puede dar de alta a socios
        # 66: Puede borrar datos socios
        permisos = Permiso.objects.filter(id__in=[55, 66, 67, 68, 69])
        g_e.permisos.add(*permisos)

    return HttpResponse()


# @login_required()
# def altas_bajas(request):
# g_e = request.session['gauser_extra']
# entidad = g_e.entidad
# educandos = Gauser_extra.objects.filter(perfiles__in=[70])
# for educando in educandos:
# if educando.gauser.fecha_alta:
#             Alta_Baja.objects.create(entidad=entidad, fecha_alta=educando.gauser.fecha_alta, gauser=educando.gauser,
#                                      observaciones='')


@login_required()
# @access_required
def generar_claves(request):
    g_e = request.session['gauser_extra']
    subentidades = Subentidad.objects.filter(entidad=g_e.entidad)

    if request.POST:
        ids = request.POST.getlist('socios')
        g_es = Gauser_extra.objects.filter(id__in=ids)
        if g_es.count() > 0:
            if request.POST['action'] == 'correo_postal':
                data = []
                for g_ex in g_es:
                    password = pass_generator()
                    g_ex.gauser.set_password(password)
                    g_ex.gauser.save()
                    data.append((g_ex, password))

                fichero = 'Claves_%s' % (g_es[0].entidad.code)
                c = render_to_string('carta_claves.html', {
                    'data': data,
                    'MA': MEDIA_ANAGRAMAS,
                }, context_instance=RequestContext(request))
                fich = html_to_pdf(request, c, fichero=fichero, media=MEDIA_FILES, title=u'Claves GAUSS')

                response = HttpResponse(fich, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename=' + fichero + '.pdf'
                return response

            if request.POST['action'] == 'e_correo':
                for g_ex in g_es:
                    if g_ex.gauser.email:
                        password = pass_generator()
                        g_ex.gauser.set_password(password)
                        g_ex.gauser.save()
                        texto_mensaje = render_to_string('template_correo_claves.html',
                                                         {'g_e': g_ex, 'password': password,},
                                                         context_instance=RequestContext(request))

                        mensaje = Mensaje.objects.create(emisor=g_e, fecha=datetime.now(), tipo='mail',
                                                         asunto='Acceso a GAUSS',
                                                         mensaje=texto_mensaje.encode('utf-8'))
                        mensaje.receptores.add(g_ex)
                        crea_mensaje_cola(mensaje)
                        # crear_aviso(request, False,
                        # 'El envío completo de los correos con las claves puede tardar varios minutos. Recibirás un aviso cuando finalice.')
        else:
            pass
            # crear_aviso(request, False, 'No hay socios sobre los que crear las claves.')

    return render_to_response("generar_claves.html",
                              {
                                  'formname': 'generar_claves',
                                  'avisos': Aviso.objects.filter(usuario=request.session["gauser_extra"],
                                                                 aceptado=False),
                                  'actions':
                                      ({'tipo': 'button', 'nombre': 'check', 'texto': 'Aceptar',
                                        'title': 'Aceptar los cambios realizados', 'permiso': 'm20i25'},
                                       {'tipo': 'button', 'nombre': 'file-text-o', 'texto': 'Cartas',
                                        'title': 'Generar cartas con claves', 'permiso': 'm20i25'}),
                                  'subentidades': subentidades,
                              },
                              context_instance=RequestContext(request))


@login_required()
def politica_privacidad(request):
    return render_to_response("politica_privacidad.html", {}, context_instance=RequestContext(request))


@login_required()
def aviso_legal(request):
    return render_to_response("aviso_legal.html", {}, context_instance=RequestContext(request))


@login_required()
def borrar_gausers(request):
    Gauser.objects.filter(~Q(username='gauss')).delete()


@login_required()
def del_entidad_gausers(request):
    g_e = request.session['gauser_extra']
    gauser = g_e.gauser
    if g_e.gauser.username == 'gauss':
        if request.method == 'POST':
            if request.POST['action'] == 'borrar_entidad' and request.POST['pass'] == 'jucarihu':
                entidad = Entidad.objects.get(id=request.POST['entidad'])
                ges = Gauser_extra.objects.filter(entidad=entidad)
                for ge in ges:
                    g = ge.gauser
                    ge.delete()
                    otros_ge = Gauser_extra.objects.filter(gauser=g)
                    if otros_ge.count() == 0:
                        if g.username == 'gauss' or g.username == 'jjmartinr01':
                            pass
                            # crear_aviso(request, False, 'Intenta borrar a %s' % (g.username))
                        else:
                            g.delete()
                entidad.delete()
        entidades = Entidad.objects.all()
        return render_to_response("del_entidad_gausers.html",
                                  {
                                      'formname': 'del_entidad_gausers',
                                      'actions':
                                          ({'tipo': 'button', 'nombre': 'check', 'texto': 'Aceptar',
                                            'title': 'Eliminar la entidad y usuarios asociados', 'permiso': 'libre'},
                                           ),
                                      'entidades': entidades,
                                  },
                                  context_instance=RequestContext(request))
    else:
        return render_to_response("no_account.html", {'usuario': gauser,},
                                  context_instance=RequestContext(request))


def recupera_password(request):
    if request.method == 'GET' and 'id' in request.GET:
        glinks = glink.objects.filter(code=request.GET['id'])
        if glinks.count() == 1:
            if glinks[0].deadline >= date.today():
                return render_to_response("cambia_password.html", {'glink': glinks[0], 'formulario': True},
                                          context_instance=RequestContext(request))
            else:
                mensaje = 'El glink se ha caducado. Solicita de nuevo un cambio de contraseña.'
        else:
            mensaje = 'El identificador es erróneo. ¿Has copiado correctamente la url enviada a tu correo?'
    elif request.method == 'POST' and 'action' in request.POST:
        if request.POST['action'] == 'cambia_password':
            if request.POST['passusuario1'] == request.POST['passusuario2'] and request.POST['passusuario1'] != '':
                glink = glink.objects.get(code=request.POST['id'])
                glink.usuario.set_password(request.POST['passusuario1'])
                glink.usuario.save()
                mensaje = 'Contraseña cambiada correctamente'
    else:
        mensaje = 'Se ha producido un error y este glink no es correcto.'

    return render_to_response("cambia_password.html", {'formulario': False, 'mensaje': mensaje})
