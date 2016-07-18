# -*- coding: utf-8 -*-
import random
import string

from django.shortcuts import render, redirect
import unicodedata
import csv
from datetime import date, datetime, timedelta
import simplejson as json

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
from models import *


class GprojectForm(ModelForm):
    class Meta:
        model = Gproject
        exclude = ('gentity', 'active')


def gprojects(request):
    try:
        gproject_id = request.GET['id']
    except:
        gproject_id = None
    if request.method == 'POST':
        if request.POST['action'] == 'create_project':
            gproject = Gproject.objects.create(gentity=request.user.gentity, active=True, name='Nuevo proyecto',
                                               administrator=request.user, notes='', start_date=datetime.today())
            # start_datetime = datetime.combine(gproject.start_date, datetime.min.time())
            # Gbaseline.objects.create(gproject=gproject, name='First baseline', start_date = start_datetime)

    gresources = Gresource.objects.filter(guser=request.user)
    gprojects = Gproject.objects.filter(Q(removed=False),
                                        Q(gresources__in=gresources) | Q(administrator=request.user) | Q(
                                            gusers_edit__in=[request.user])).distinct().order_by('-active', 'start_date')

    return render_to_response("gprojects.html",
                              {
                                  'actions':
                                      ({'name': 'plus', 'text': 'Nuevo', 'href': '/create_project/',
                                        'title': 'Crear un nuevo proyecto', 'permission': 'create_projects'},
                                       ),
                                  'gprojects': gprojects,
                                  'gproject_id': gproject_id,
                              },
                              context_instance=RequestContext(request))


def gprojects_ajax(request):
    guser = request.user
    gproject = Gproject.objects.get(Q(id=request.POST['id']), Q(gusers_edit__in=[guser]) | Q(administrator=guser))
    if request.is_ajax():
        if request.POST['action'] == 'project_data':
            if gproject.active:
                html = render_to_string('project_data.html', {'gproject': gproject})
            else:
                html = render_to_string('project_data_locked.html', {'gproject': gproject})
            return HttpResponse(html)
        elif request.POST['action'] == 'change_active':
            gproject.active = not gproject.active
            gproject.save()
            if gproject.active:
                html = render_to_string('project_data.html', {'gproject': gproject})
                return JsonResponse({'remove': 'fa-lock', 'add': 'fa-unlock', 'html': html})
            else:
                html = render_to_string('project_data_locked.html', {'gproject': gproject})
                return JsonResponse({'remove': 'fa-unlock', 'add': 'fa-lock', 'html': html})
        elif request.POST['action'] == 'change_name':
            gproject.name = request.POST['name']
            gproject.save()
            return HttpResponse(gproject.name)
        elif request.POST['action'] == 'change_administrator':
            gproject.administrator = Guser.objects.get(id=request.POST['administrator'])
            gproject.save()
            return HttpResponse(gproject.name)
        elif request.POST['action'] == 'change_date':
            gproject.start_date = datetime.strptime(request.POST['start_date'], '%d-%m-%Y')
            gproject.save()
            return HttpResponse(gproject.start_date)
        elif request.POST['action'] == 'change_notes':
            gproject.notes = request.POST['notes']
            gproject.save()
            return HttpResponse(gproject.notes)
        elif request.POST['action'] == 'remove':
            gproject.removed = True
            gproject.save()
            return HttpResponse(True)
        return HttpResponse('Error')


class GtaskForm(ModelForm):
    class Meta:
        model = Gtask
        exclude = ('gbaseline',)
        widgets = {
            'predecessors': SelectMultiple(attrs={'class': 'predecessors'}),
        }


def gantt(request, gproject_id):
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
                                        'title': 'Convertir en subtareas de la inmediatamente superior', 'type': 'sliders'},
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
                                       {'name': 'plus-circle', 'text': 'Nueva baseline', 'permission': 'create_projects',
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


def change_pos(gtask, new_pos=None):
    if not new_pos:
        gtasks = Gtask.objects.filter(gbaseline=gtask.gbaseline, pos__gt=gtask.pos)
        for t in gtasks:
            t.pos -= 1
            t.save()
        return True
    elif gtask.pos > new_pos:
        gtasks = Gtask.objects.filter(gbaseline=gtask.gbaseline, pos__gte=new_pos, pos__lt=gtask.pos)
        for t in gtasks:
            t.pos += 1
            t.save()
    elif gtask.pos < new_pos:
        gtasks = Gtask.objects.filter(gbaseline=gtask.gbaseline, pos__gt=gtask.pos, pos__lte=new_pos)
        for t in gtasks:
            t.pos -= 1
            t.save()
    gtask.pos = new_pos
    gtask.save
    return True


def gproject_dict(gbaseline, link=None, gtask=None):
    gantt_tasks = []
    gantt_links = []
    if link:
        tasks = link.successor.all_successors
        links = Gtask_link.objects.filter(Q(predecessor__in=tasks) | Q(successor__in=tasks))
    elif gtask:
        tasks = gtask.all_successors
        links = Gtask_link.objects.filter(Q(predecessor__in=tasks) | Q(successor__in=tasks))
    else:
        tasks = Gtask.objects.filter(gbaseline=gbaseline)
        links = Gtask_link.objects.filter(gbaseline=gbaseline)

    gcols = Gcolumn.objects.filter(gbaseline=gbaseline)
    for t in tasks:
        cols = []
        # for gcol in gcols:
        #     cols.append({'name': gcol.get_content_display(), 'pos': gcol.pos, 'value': getattr(t, gcol.content)})
        gantt_tasks.append({'id': t.id, 'name': t.name, 'left': t.left, 'width': t.width, 'pos': t.pos,
                            'width_progress': t.width_progress, 'cols': cols})
    for l in links:
        gantt_links.append(
            {'id': l.id, 'source': l.predecessor.id, 'target': l.successor.id, 'type': l.dependency})
    return gantt_tasks, gantt_links


def gantt_ajax(request):
    guser = request.user
    if request.is_ajax():
        action = request.POST['action']
        if action == 'add_task':
            gbaseline = Gbaseline.objects.get(id=request.POST['id'])
            if (gbaseline.gproject.administrator == guser or gbaseline.gproject.can_guser_edit(guser)):
                if gbaseline.gtask_set.all().count() == 0:
                    pos = 0
                else:
                    pos = gbaseline.gtask_set.all().aggregate(Max('pos'))['pos__max'] + 1
                gtask = Gtask.objects.create(gbaseline=gbaseline, name="Nueva actividad", pos=pos)
            return HttpResponse(serializers.serialize('json', [gtask]))
        elif action == 'insert_task':
            task_orig = Gtask.objects.get(id=request.POST['id'])
            gproject = task_orig.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                new_task_pos = task_orig.pos
                for gtask in Gtask.objects.filter(gbaseline=task_orig.gbaseline, pos__gte=new_task_pos):
                    gtask.pos = gtask.pos + 1
                    gtask.save()
                new_task = Gtask.objects.create(gbaseline=task_orig.gbaseline, name="Nueva actividad", pos=new_task_pos)
            return HttpResponse(serializers.serialize('json', [new_task]))
        elif action == 'moveup_gtask':
            prev = Gtask.objects.get(id=request.POST['prev'])
            curr = Gtask.objects.get(id=request.POST['curr'])
            gproject = prev.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                prev_pos = prev.pos
                prev.pos = curr.pos
                prev.save()
                curr.pos = prev_pos
                curr.save()
            return HttpResponse(True)
        elif action == 'movedown_gtask':
            next = Gtask.objects.get(id=request.POST['next'])
            curr = Gtask.objects.get(id=request.POST['curr'])
            gproject = next.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                next_pos = next.pos
                next.pos = curr.pos
                next.save()
                curr.pos = next_pos
                curr.save()
            return HttpResponse(True)
        elif action == 'gantt_task_data':
            gtask = Gtask.objects.get(id=request.POST['id'])
            form = GtaskForm(instance=gtask)
            gtasks = Gtask.objects.filter(gbaseline=gtask.gbaseline)
            if gtask.gbaseline.gproject.can_guser_edit(request.user):
                html = render_to_string('gantt_gtask_data.html', {'form': form, 'gtask': gtask, 'gtasks': gtasks})
                return HttpResponse(html)
        elif action == 'seek_tasks':
            text = request.POST['q']
            gtask = Gtask.objects.get(id=request.POST['id'])
            gtasks_impossible = gtask.all_successors
            gbaseline = Gbaseline.objects.get(id=request.POST['gbaseline'])
            gtasks = []
            if gbaseline.gproject.can_guser_edit(request.user):
                gtasks = Gtask.objects.filter(Q(gbaseline=gbaseline), Q(name__icontains=text),
                                              ~Q(id__in=gtasks_impossible),
                                              ~Q(id__in=gtask.predecessors.all())).values_list('id', 'name')
            keys = ('id', 'text')
            return JsonResponse([dict(zip(keys, row)) for row in gtasks], safe=False)
        elif action == 'gcolumn-align-center':
            gcolumn = Gcolumn.objects.get(id=request.POST['id'])
            gproject = gcolumn.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                gcolumn.align = 'center'
                gcolumn.save()
            return HttpResponse(True)
        elif action == 'gcolumn-align-left':
            gcolumn = Gcolumn.objects.get(id=request.POST['id'])
            gproject = gcolumn.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                gcolumn.align = 'left'
                gcolumn.save()
            return HttpResponse(True)
        elif action == 'gcolumn-align-right':
            gcolumn = Gcolumn.objects.get(id=request.POST['id'])
            gproject = gcolumn.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                gcolumn.align = 'right'
                gcolumn.save()
            return HttpResponse(True)
        elif action == 'gcolumn-move-right':
            col_orig = Gcolumn.objects.get(id=request.POST['id'])
            gproject = col_orig.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                current_column_pos = col_orig.pos
                try:
                    col_dest = Gcolumn.objects.get(gbaseline=col_orig.gbaseline, pos=current_column_pos+1)
                    col_orig.pos = col_dest.pos
                    col_orig.save()
                    col_dest.pos = current_column_pos
                    col_dest.save()
                except:
                    pass
            return HttpResponse(True)
        elif action == 'gcolumn-move-left':
            col_orig = Gcolumn.objects.get(id=request.POST['id'])
            gproject = col_orig.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                current_column_pos = col_orig.pos
                try:
                    col_dest = Gcolumn.objects.get(gbaseline=col_orig.gbaseline, pos=current_column_pos-1)
                    col_orig.pos = col_dest.pos
                    col_orig.save()
                    col_dest.pos = current_column_pos
                    col_dest.save()
                except:
                    pass
            return HttpResponse(True)
        elif action == 'gcolumn-insert':
            col_orig = Gcolumn.objects.get(id=request.POST['id'])
            new_content = request.POST['content']
            gproject = col_orig.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                new_col_pos = col_orig.pos if (request.POST['direction'] == 'left') else (col_orig.pos + 1)
                for gcol in Gcolumn.objects.filter(gbaseline=col_orig.gbaseline, pos__gte=new_col_pos):
                    gcol.pos = gcol.pos + 1
                    gcol.save()
                new_col = Gcolumn.objects.create(gbaseline=col_orig.gbaseline, pos=new_col_pos, content=new_content)
            return HttpResponse(serializers.serialize('json', [new_col]))
        elif action == 'gcolumn-remove':
            col = Gcolumn.objects.get(id=request.POST['id'])
            gproject = col.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                gcols = Gcolumn.objects.filter(gbaseline=col.gbaseline, pos__gt=col.pos)
                for gcol in gcols:
                    gcol.pos = gcol.pos - 1
                    gcol.save()
                col.delete()
            return HttpResponse(True)
        elif action == 'update_gtask_name':
            gtask = Gtask.objects.get(id=request.POST['id'])
            gtask.name = request.POST['value']
            gtask.save()
            return HttpResponse(True)
        elif action == 'update_estimate_time_days':
            gtask = Gtask.objects.get(id=request.POST['id'])
            val = timedelta(days=float(request.POST['value']))
            gtask.optimistic_time = val
            gtask.likely_time = val
            gtask.pessimistic_time = val
            gtask.save()
            return JsonResponse('%s'%(val), safe=False)
        elif action == 'update_optimistic_time':
            gtask = Gtask.objects.get(id=request.POST['id'])
            val = timedelta(days=float(request.POST['value']))
            gtask.optimistic_time = val
            gtask.save()
            return JsonResponse('%s'%(val), safe=False)
        elif action == 'update_likely_time':
            gtask = Gtask.objects.get(id=request.POST['id'])
            val = timedelta(days=float(request.POST['value']))
            gtask.likely_time = val
            gtask.save()
            return JsonResponse('%s'%(val), safe=False)
        elif action == 'update_pessimistic_time':
            gtask = Gtask.objects.get(id=request.POST['id'])
            val = timedelta(days=float(request.POST['value']))
            gtask.pessimistic_time = val
            gtask.save()
            return JsonResponse('%s'%(val), safe=False)
        # elif action == 'change_cell':
        #     gtask = Gtask.objects.get(id=request.POST['gtask_id'])
        #     content = request.POST['content']
        #     data = request.POST['text']
        #     if content == 'gtask_name':
        #         gtask.name = data
        #     elif content == 'estimate_time_days':
        #         duration = ''.join(c for c in data if (c.isdigit() or c == '.'))
        #         days = float(duration) / 8 if 'h' in data else float(duration)
        #         gtask.optimistic_time = timedelta(days=days)
        #         gtask.likely_time = timedelta(days=days)
        #         gtask.pessimistic_time = timedelta(days=days)
        #         resp = {'col'}
        #     elif content == 'pessimistic_time':
        #         duration = ''.join(c for c in data if (c.isdigit() or c == '.'))
        #         days = float(duration) / 8 if 'h' in data else float(duration)
        #         gtask.pessimistic_time = timedelta(days=days)
        #     elif content == 'optimistic_time':
        #         duration = ''.join(c for c in data if (c.isdigit() or c == '.'))
        #         days = float(duration) / 8 if 'h' in data else float(duration)
        #         gtask.optimistic_time = timedelta(days=days)
        #     elif content == 'likely_time':
        #         duration = ''.join(c for c in data if (c.isdigit() or c == '.'))
        #         days = float(duration) / 8 if 'h' in data else float(duration)
        #         gtask.likely_time = timedelta(days=days)
        #     elif content == 'early_start':
        #         pass
        #     gtask.save()
        #     return HttpResponse(data)
        elif action == 'num_cols':
            gbaseline = Gbaseline.objects.get(id=request.POST['id'])
            gbaseline.columns = request.POST['right']
            gbaseline.save()
            return HttpResponse(True)
        elif action == 'change_time':
            gtask = Gtask.objects.get(id=request.POST['id'])
            duration = ''.join(c for c in request.POST['duration'] if (c.isdigit() or c == '.'))
            days = float(duration) / 8 if 'h' in request.POST['duration'] else float(duration)
            if request.POST['type'] == 'estimate':
                gtask.optimistic_time = timedelta(days=days)
                gtask.likely_time = timedelta(days=days)
                gtask.pessimistic_time = timedelta(days=days)
            elif request.POST['type'] == 'optimistic':
                gtask.optimistic_time = timedelta(days=days)
            elif request.POST['type'] == 'likely':
                gtask.likely_time = timedelta(days=days)
            elif request.POST['type'] == 'pessimistic':
                gtask.pessimistic_time = timedelta(days=days)
            gtask.save()
            return JsonResponse(
                {'estimate': gtask.estimate_time.days + round(float(gtask.estimate_time.seconds) / 3600 / 24, 2),
                 'optimistic': gtask.optimistic_time.days + round(float(gtask.optimistic_time.seconds) / 3600 / 24, 2),
                 'likely': gtask.likely_time.days + round(float(gtask.likely_time.seconds) / 3600 / 24, 2),
                 'pessimistic': gtask.pessimistic_time.days + round(float(gtask.pessimistic_time.seconds) / 3600 / 24, 2)})
        elif action == 'update_predecessors':
            gtask = Gtask.objects.get(id=request.POST['gtask_id'])
            gproject = gtask.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                old_predecessors = Gtask_link.objects.filter(successor=gtask).values_list('predecessor__id', flat=True)
                new_predecessors = request.POST.getlist('predecessors')
                sop = set(old_predecessors)
                snp = set(new_predecessors)
                deleted = Gtask.objects.filter(id__in=list(sop - snp))
                for predecessor in deleted:
                    Gtask_link.objects.get(predecessor=predecessor, successor=gtask, gbaseline=gtask.gbaseline).delete()
                added = Gtask.objects.filter(id__in=list(snp - sop))
                for predecessor in added:
                    Gtask_link.objects.create(predecessor=predecessor, successor=gtask, gbaseline=gtask.gbaseline)
            return HttpResponse(True)
        elif action == 'remove_predecessor':
            gtask = Gtask.objects.get(id=request.POST['gtask_id'])
            gproject = gtask.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                pass
            return HttpResponse(True)
        elif action == 'add_predecessor':
            gtask = Gtask.objects.get(id=request.POST['gtask_id'])
            gproject = gtask.gbaseline.gproject
            if (gproject.administrator == guser or gproject.can_guser_edit(guser)):
                pass
            return HttpResponse(True)
        elif action == 'gantt_schedule':
            gbaseline = Gbaseline.objects.get(id=request.POST['id'])
            gantt_tasks, gantt_links = gproject_dict(gbaseline)
            return JsonResponse({'tasks': gantt_tasks, 'links': gantt_links}, safe=False)
        elif action == 'remove_glink':
            glink = Gtask_link.objects.get(id=request.POST['id'])
            gproject_id = glink.gbaseline.gproject.id
            try:
                Gproject.objects.get(Q(id=gproject_id), Q(administrator=guser) | Q(gusers_edit__in=[guser]))
                glink.delete()
                return HttpResponse(True)
            except:
                return HttpResponse(False)
            # # p = glink.predecessor
            # s = glink.successor
            # glink.delete()
            # gantt_tasks, gantt_links = gproject_dict(gbaseline, gtask=s)
            # return JsonResponse({'tasks': gantt_tasks, 'links': gantt_links}, safe=False)
        elif action == 'create_gtask':
            gtask = Gtask.objects.create(id=request.POST['id'])
            gproject_id = gtask.gbaseline.gproject.id
            try:
                Gproject.objects.get(Q(id=gproject_id), Q(administrator=guser) | Q(gusers_edit__in=[guser]))
                gtask.delete()
                return HttpResponse(True)
            except:
                return HttpResponse(False)
        elif action == 'remove_gtask':
            gtask = Gtask.objects.get(id=request.POST['id'])
            gproject_id = gtask.gbaseline.gproject.id
            try:
                Gproject.objects.get(Q(id=gproject_id), Q(administrator=guser) | Q(gusers_edit__in=[guser]))
                gtask.delete()
                return HttpResponse(True)
            except:
                return HttpResponse(False)
        # elif action == 'delete_gtasks':
        #     gtasks = Gtask.objects.filter(id__in=request.POST.getlist('gtasks'))
        #     gbaseline = gtasks[0].gbaseline
        #     Gtask_link.objects.filter(Q(successor__in=gtasks) | Q(predecessor__in=gtasks)).delete()
        #     gtasks.delete()
        #     n = 0
        #     for gtask in gbaseline.gtask_set.all():
        #         gtask.pos = n
        #         gtask.save()
        #         n += 1
        #     return HttpResponse(True)
        elif action == 'create_link':
            gbaseline = Gbaseline.objects.get(id=request.POST['b_id'])
            p = Gtask.objects.get(gbaseline=gbaseline, id=request.POST['gtask_o'])
            s = Gtask.objects.get(gbaseline=gbaseline, id=request.POST['gtask_d'])
            d = request.POST['dependency']
            if p != s and s not in p.all_successors:
                # "link" is the created object or get it, "created" is a boolean True if created and False if get it
                link, created = Gtask_link.objects.get_or_create(gbaseline=gbaseline, successor=s, predecessor=p,
                                                                 dependency=d)
                return HttpResponse(serializers.serialize('json', [link, p]))
            else:
                return HttpResponse(serializers.serialize('json', []))


        elif action == 'dedent':
            gtasks = Gtask.objects.filter(id__in=request.POST.getlist('gtasks'))
            for gtask in gtasks:
                parent = gtask.gtask_parent
                gtask.gtask_parent = parent.gtask_parent
                change_pos(gtask, new_pos=parent.pos + 1)
                # gtask.save()
            html = render_to_string('gantt_schedule.html', {'gbaseline': gtasks[0].gbaseline})
            return HttpResponse(html)
        elif action == 'indent':
            gtasks = Gtask.objects.filter(id__in=request.POST.getlist('gtasks'))
            for gtask in gtasks:
                new_parent = Gtask.objects.filter(pos__lt=gtask.pos, gtask_parent=gtask.gtask_parent).reverse()[0]
                gtask.gtask_parent = new_parent
                gtask.save()
            html = render_to_string('gantt_schedule.html', {'gbaseline': gtasks[0].gbaseline})
            return HttpResponse(html)
        elif action == 'get_links':
            gbaseline = Gbaseline.objects.get(id=request.POST['gbaseline'])
            links = Gtask_link.objects.filter(gbaseline=gbaseline)
            gantt_links = []
            for l in links:
                gantt_links.append(
                    {'id': l.id, 'source': l.predecessor.id, 'target': l.successor.id, 'type': l.dependency})
            return JsonResponse(gantt_links, safe=False)
        elif action == 'get_tasks':
            gbaseline = Gbaseline.objects.get(id=request.POST['gbaseline'])
            tasks = Gtask.objects.filter(gbaseline=gbaseline)
            gantt_tasks = []
            for t in tasks:
                gantt_tasks.append(
                    {'id': t.id, 'name': t.name, 'left': t.left, 'width': t.width, 'width_progress': t.width_progress})
            return JsonResponse(gantt_tasks, safe=False)
        elif action == 'columns':
            gt = Gtask.objects.get(id=request.POST['id'])
            gcols = Gcolumn.objects.filter(gbaseline=gt.gbaseline)
            cols = []
            for gcol in gcols:
                cols.append({'name': gcol.get_content_display(), 'pos': gcol.pos, 'value': getattr(gt, gcol.content)})
            return JsonResponse(cols, safe=False)
        elif action == 'gcolumn_width':
            gcol = Gcolumn.objects.get(id=request.POST['colpk'])
            gcol.width = request.POST['width']
            gcol.save()
            return HttpResponse(True)

