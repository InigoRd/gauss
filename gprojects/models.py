# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from datetime import timedelta, datetime
from django.db.models import signals
from dateutil.rrule import rrule, MONTHLY, DAILY
# Create your models here.
import json

from gentities.models import Gentity, Guser
from gresources.models import Gresource
# from gcalendars.models import Gcalendar


class Gproject(models.Model):
    gentity = models.ForeignKey(Gentity, blank=True, null=True)
    name = models.CharField('Name of the project', blank=True, null=True, max_length=250)
    active = models.BooleanField('Is it active?', default=True)
    start_date = models.DateField('Starting date', blank=True, null=True)
    administrator = models.ForeignKey(Guser, blank=True, null=True)
    notes = models.TextField('Description of the project', blank=True, null=True)
    gresources = models.ManyToManyField(Gresource, blank=True)
    gusers_edit = models.ManyToManyField(Guser, blank=True, related_name='edit')
    removed = models.BooleanField('The project is removed', default=False)
    created = models.DateTimeField('Date of creation', auto_now_add=True)
    modified = models.DateTimeField('Last modification', auto_now=True)

    @property
    def end_date(self):
        return (datetime.today() + timedelta(days=10)).date()

    def can_guser_edit(self, guser):
        return True if (guser in self.gusers_edit.all() or guser == self.administrator) else False

    class Meta:
        ordering = ['active', 'created']

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.gentity.name)


########################################################################################

def update_active_baselines(sender, instance, created, **kwargs):
    if instance.active == True:
        baselines = Gbaseline.objects.filter(gproject=instance.gproject, active=True).exclude(id=instance.id)
        for baseline in baselines:
            baseline.active = False
            baseline.save()


class Gbaseline(models.Model):
    gproject = models.ForeignKey(Gproject, blank=True, null=True)
    name = models.CharField('Name', max_length=200, blank=True, null=True)
    start_date = models.DateTimeField('Starting date', blank=True, null=True)
    active = models.BooleanField('Is it the active one?', default=True)
    scale = models.IntegerField('Width in pixels for unit of time', blank=True, null=True, default=24)
    columns = models.IntegerField('Number of foundation columns occupied by the gantt chart', default=9)
    created = models.DateTimeField('Date of creation', auto_now_add=True)
    modified = models.DateTimeField('Last modification', auto_now=True)

    @property
    def jsonGtasks(self):
        def eval_col(t, col):
            if col == 'estimate_time_days':
                return t.estimate_time.seconds / 3600 / 24 + t.estimate_time.days
            elif col == 'ES':
                # return str(t.early_start)
                return t.pos
            elif col == 'LF':
                # return str(t.last_finish)
                return t.name
            else:
                return "error"

        tasks = self.gtask_set.all()
        gantt_tasks = []
        gcols = self.gcolumn_set.all()
        for t in tasks:
            cols = []
            # for gcol in gcols:
            # cols.append({'name': gcol.get_content_display(), 'pos': gcol.pos, 'value': getattr(t, gcol.content)})
            # cols.append({'name': gcol.get_content_display(), 'pos': gcol.pos, 'value': eval_col(t, gcol.content)})
            # gantt_tasks.append({'id': t.id, 'name': t.name, 'left': t.left, 'width': t.width, 'pos': t.pos,
            #                     'width_progress': t.width_progress, 'cols': cols})
            gantt_tasks.append({'id': t.id, 'name': t.name, 'left': t.left, 'width': t.width, 'pos': t.pos,
                                'width_progress': t.width_progress, 'es': str(t.es),
                                'duration': t.estimate_time_days, 'lf': str(t.lf)})
        return json.dumps(gantt_tasks)

    # @property
    # def jsonGtasks(self):
    #     def eval_col(t, col):
    #         if col == 'estimate_time_days':
    #             return t.estimate_time.seconds / 3600 / 24 + t.estimate_time.days
    #         elif col == 'ES':
    #             # return str(t.early_start)
    #             return t.pos
    #         elif col == 'LF':
    #             # return str(t.last_finish)
    #             return t.name
    #         else:
    #             return "error"
    #     tasks = self.gtask_set.all()
    #     gcols = self.gcolumn_set.all()
    #     gantt_tasks = {}
    #     cols = {}
    #     for t in tasks:
    #         cols.clear()
    #         for gcol in gcols:
    #             cols[gcol.id] = {'name': gcol.get_content_display(), 'pos': gcol.pos, 'value': eval_col(t, gcol.content)}
    #         gantt_tasks[t.id] = {'id': t.id, 'name': t.name, 'left': t.left, 'width': t.width, 'pos': t.pos,
    #                             'width_progress': t.width_progress, 'cols': cols}
    #     return json.dumps(gantt_tasks)

    @property
    def jsonGlinks(self):
        links = self.gtask_link_set.all()
        gantt_links = []
        for l in links:
            gantt_links.append(
                {'id': l.id, 'source': l.predecessor.id, 'target': l.successor.id, 'type': l.dependency})
        return json.dumps(gantt_links)

    @property
    def jsonGcolumns(self):
        gcols = self.gcolumn_set.all()
        gtasks = self.gtask_set.all()
        gantt_cols = []
        for t in gtasks:
            for gcol in gcols:
                gantt_cols.append({'gtask_id': t.id, 'name': gcol.get_content_display(), 'pos': gcol.pos,
                                   'value': str(getattr(t, gcol.content))})
        return json.dumps(gantt_cols)

    # @property
    # def start_date(self):
    #     return datetime.combine(self.gproject.start_date, datetime.min.time())

    @property
    def left_side(self):
        return 12 - self.columns

    @property
    def right_side(self):
        return self.columns

    # @property
    # def end_date(self):
    #     last_times = []
    #     last_tasks = Gtask.objects.filter(successors=None)
    #     for t in last_tasks:
    #         last_times.append(t.early_start + t.estimate_time)
    #     return max(last_times)

    @property
    def end_date(self):
        gtasks = Gtask.objects.filter(gbaseline=self)
        last_tasks = [gtask for gtask in gtasks if gtask.successors.count() == 0]
        last_times = [self.start_date]
        for t in last_tasks:
            last_times.append(t.early_start + t.estimate_time)
        return max(last_times)

    @property
    def project_duration(self):
        return self.end_date - self.start_date

    # @property
    # def month_list(self):
    #     diff_days = self.start_date.day - self.end_date.day
    #     end_date = self.end_date if diff_days < 0 else self.end_date + timedelta(diff_days)
    #     return rrule(MONTHLY, dtstart=self.start_date, until=end_date)

    @property
    def project_dates(self):
        current_month = self.start_date.month
        dates = [[]]
        n = 0
        for d in rrule(DAILY, dtstart=self.start_date, until=self.end_date):
            if current_month != d.month:
                current_month = d.month
                n += 1
                dates.append([])
            dates[n].append(d)
        return dates

    @property
    def project_num_days(self):
        return len(list(rrule(DAILY, dtstart=self.start_date, until=self.end_date)))

    @property
    def gtasks(self):
        return Gtask.objects.filter(gbaseline=self)

    # @property
    # def main_gtasks(self):
    #     return Gtask.objects.filter(gbaseline=self, gtask_parent=None)

    def __unicode__(self):
        return u'%s - %s (%s)' % (self.name, self.gproject, self.active)


signals.post_save.connect(update_active_baselines, sender=Gbaseline)

########################################################################################
# DIMENSIONS OF GANTT CHART BARS
########################################################################################

margin_task = 2
task_height = margin_task * 11
row_height = task_height + margin_task * 2


########################################################################################

class Gtask(models.Model):
    # As Soon As Possible, As Late As Possible, Starting Date, Ending Date, Start No Before that Date
    # Start No Later that Date, End No Before that Date, End No Later that Date
    TASK_RESTRICTIONS = (('ASAP', 'Lo antes posible'), ('ALAP', 'Lo más tarde posible'),
                         ('SD', 'Debe empezar el ...'), ('ED', 'Debe terminar el ...'),
                         ('SNBD', 'No iniciar antes del ...'), ('SNLD', 'Iniciar como muy tarde el ...'),
                         ('ENBD', 'No terminar antes del ...'), ('ENLD', 'Terminar como muy tarde el ...'))
    DISPLAY = (('none', 'none'), ('block', 'block'))
    gbaseline = models.ForeignKey(Gbaseline, blank=True, null=True)
    name = models.CharField('Name', max_length=200, blank=True, null=True)
    pos = models.IntegerField('Vertical position', blank=True, null=True)
    optimistic_time = models.DurationField('Optimistic time', blank=True, null=True, default=timedelta(days=1))
    likely_time = models.DurationField('Likely time', blank=True, null=True, default=timedelta(days=1))
    pessimistic_time = models.DurationField('Pessimistic time', blank=True, null=True, default=timedelta(days=1))
    gresources = models.ManyToManyField(Gresource, blank=True)
    priority = models.IntegerField('Priority', blank=True, null=True, default=500)
    restriction = models.CharField('Restriction type', choices=TASK_RESTRICTIONS, max_length=10, default='ASAP')
    restriction_date = models.DateTimeField('Restriction date', blank=True, null=True)
    progress = models.IntegerField('Progress', default=0, validators=[MaxValueValidator(100), MinValueValidator(0)])
    notes = models.TextField('Notes about the task', blank=True, null=True)
    created = models.DateTimeField('Date of creation', auto_now_add=True)
    modified = models.DateTimeField('Last modification', auto_now=True)
    # subtasks = models.ManyToManyField('self', blank=True, related_name='parents', symmetrical=False)
    gtask_parent = models.ForeignKey('self', blank=True, null=True)
    display_subtasks = models.BooleanField('Display subtasks', default=True)
    #########################################################
    ######## Retrieving data from database is faster than excute functions/properties,
    ######## then those data obtain from properties are storaged is the following columns:
    es = models.DateTimeField("Early start", blank=True, null=True)
    lf = models.DateTimeField("Last Finish", blank=True, null=True)

    def update_fields(self):
        self.es = self.early_start
        self.lf = self.last_finish
        self.save()
        return True

    @property
    def has_subtasks(self):
        return self.gtask_set.all().count() > 0

    @property
    def open_close(self):
        if self.has_subtasks and self.display_subtasks:
            return 'minus'
        elif self.has_subtasks and not self.display_subtasks:
            return 'plus'
        else:
            return ''

    @property
    def tree_depth(self):
        if self.gtask_parent:
            return self.gtask_parent.tree_depth + 1
        else:
            return 0

    # @property
    # def ancestors(self):
    #     if self.gtask_parent:
    #         return self.gtask_parent.ancestors.append(self.gtask_parent.id)
    #     else:
    #         return []


    @property
    def successors(self):
        id_gtasks = Gtask_link.objects.filter(predecessor=self).values_list('successor__id', flat=True)
        return Gtask.objects.filter(id__in=id_gtasks)

    @property
    def predecessors(self):
        id_gtasks = Gtask_link.objects.filter(successor=self).values_list('predecessor__id', flat=True)
        return Gtask.objects.filter(id__in=id_gtasks)

    @property
    def all_successors(self):
        r = []
        r.append(self.id)
        for c in self.successors:
            r += list(c.all_successors.values_list('id', flat=True))
        return Gtask.objects.filter(id__in=r)

    @property
    def early_start(self):
        tearlys_array = []
        for t in self.predecessors:
            tearlys_array.append(t.early_start + t.estimate_time)
        tearly = max(tearlys_array) if tearlys_array else self.gbaseline.start_date
        self.es = tearly
        self.save()
        return tearly

    @property
    def ES(self):
        return str(self.early_start)

    @property
    def last_finish(self):
        tlasts_array = []
        for t in self.successors:
            tlasts_array.append(t.last_finish - t.estimate_time)
        tlast = min(tlasts_array) if tlasts_array else self.gbaseline.end_date
        self.lf = tlast
        self.save()
        return tlast

    @property
    def LF(self):
        return str(self.last_finish)

    @property
    def estimate_time(self):
        return (self.optimistic_time + 4 * self.likely_time + self.pessimistic_time) / 6

    @property
    def estimate_time_days(self):
        return round(float(self.estimate_time.seconds) / 3600 / 24, 2) + self.estimate_time.days

    @property
    def left(self):
        left_delta = (self.early_start - self.gbaseline.start_date)
        return int(self.gbaseline.scale * (left_delta.days + float(left_delta.seconds) / 3600 / 24))

    @property
    def width(self):
        return int(self.gbaseline.scale * (self.estimate_time.days + float(self.estimate_time.seconds) / 3600 / 24))

    @property
    def top(self):
        return self.pos * row_height + margin_task

    @property
    def height(self):
        return task_height

    @property
    def right(self):
        return self.left + self.width

    @property
    def margin(self):
        return margin_task

    @property
    def row_height(self):
        return row_height

    @property
    def width_progress(self):
        return int(self.width * self.progress * 0.01)

    @property
    def is_milestone(self):
        return False if self.children.all().count() > 0 else True

    class Meta:
        ordering = ['-gbaseline', 'pos']

    def __unicode__(self):
        return u'%s %s (%s-%s)' % (self.pos, self.name, self.gbaseline.pk, self.gbaseline.name)


class Gtask_link(models.Model):
    line_width = 2
    link_wrapper_width = task_height / 2

    DEPENDENCIES = (('FS', 'Finish to Start'), ('FF', 'Finish to Finish'),
                    ('SS', 'Start to Start'), ('SF', 'Start to Finish'),)
    gbaseline = models.ForeignKey(Gbaseline, blank=True, null=True)
    predecessor = models.ForeignKey(Gtask, blank=True, null=True, related_name='predecessor')
    successor = models.ForeignKey(Gtask, blank=True, null=True, related_name='successor')
    dependency = models.CharField('Type of dependency', choices=DEPENDENCIES, max_length=10, default='FS')

    def shift(self, p0, p1):
        left = -1 * self.link_wrapper_width / 2
        top = -1 * self.link_wrapper_width / 2
        if p0['x'] - p1['x'] > 0:
            left = -self.link_wrapper_width / 2 - (p0['x'] - p1['x'])
        if p0['y'] - p1['y'] > 0:
            top = -self.link_wrapper_width / 2 - (p0['y'] - p1['y'])
        return {'left': left, 'top': top}

    @property
    def path(self):
        # Con tareas gap <= row_height/2
        if abs(self.predecessor.right - self.successor.left) <= row_height / 2:
            p1 = {'x': self.predecessor.right, 'y': int(self.predecessor.top + self.predecessor.height / 2)}
            p2 = {'x': p1['x'] + row_height / 2, 'y': p1['y']}
            p3 = {'x': p2['x'], 'y': p2['y'] + cmp(self.successor.top, self.predecessor.top) * row_height / 2}
            p4 = {'x': p3['x'] - row_height, 'y': p3['y']}
            p5 = {'x': p4['x'], 'y': self.successor.top + task_height / 2}
            p6 = {'x': p5['x'] + row_height / 2, 'y': p5['y']}
            points = [[p1, p2], [p2, p3], [p3, p4], [p4, p5], [p5, p6]]
        else:
            # Con tareas gap > row_height/2
            p1 = {'x': self.predecessor.right, 'y': int(self.predecessor.top + task_height / 2)}
            p2 = {'x': p1['x'] + row_height / 2, 'y': p1['y']}
            p3 = {'x': p2['x'], 'y': self.successor.top + task_height / 2}
            p4 = {'x': p3['x'] + self.successor.left - self.predecessor.right - row_height / 2, 'y': p3['y']}
            points = [[p1, p2], [p2, p3], [p3, p4]]

        paths = []
        # Para cada pareja de puntos:
        for p in points:
            top_wrapper = p[0]['y'] + self.shift(p[0], p[1])['top'] + self.line_width
            left_wrapper = p[0]['x'] + self.shift(p[0], p[1])['left']
            width_wrapper = self.link_wrapper_width + abs(p[0]['x'] - p[1]['x'])
            height_wrapper = self.link_wrapper_width + abs(p[0]['y'] - p[1]['y'])

            width_line = self.line_width + abs(p[0]['x'] - p[1]['x'])
            height_line = self.line_width + abs(p[0]['y'] - p[1]['y'])

            margin = self.link_wrapper_width / 2

            left_a = left_wrapper + width_wrapper - self.link_wrapper_width
            top_a = top_wrapper + margin - self.line_width

            paths.append({'top_w': top_wrapper, 'width_w': width_wrapper,
                          'width_l': width_line, 'left_w': left_wrapper,
                          'height_w': height_wrapper, 'height_l': height_line,
                          'margin': margin, 'left_a': left_a, 'top_a': top_a})

        return paths

    class Meta:
        ordering = ['-gbaseline']
    def __unicode__(self):
        if self.gbaseline.pk == self.predecessor.gbaseline.pk & self.gbaseline.pk == self.successor.gbaseline.pk:
            pk = self.gbaseline.pk
        else:
            pk = u'Error. Links entre diferentes baselines'
        return u'Gb: %s, %s -> %s (%s)' % (pk, self.predecessor.name, self.successor.name, self.dependency)


class Gcolumn(models.Model):
    TYPES = (('estimate_time_days', 'Estimate time (d)'), ('early_start_date', 'Early start (date)'),
             ('early_start_datetime', 'Early start (datetime)'), ('last_finish_date', 'Last Finish (date)'),
             ('last_finish_datetime', 'Last Finish (datetime)'), ('gtask_name', 'Task name'),
             ('total_float', 'Total float'), ('free_float', 'Free float'), ('optimistic_time', 'Optimistic time'),
             ('likely_time', 'Likely time'), ('pessimistic_time', 'Pessimistic time'))
    ALIGN = (('center', 'center'), ('left', 'left'), ('right', 'right'))
    gbaseline = models.ForeignKey(Gbaseline, blank=True, null=True)
    pos = models.IntegerField('Horizontal position', default=0)
                              # validators=[MaxValueValidator(len(TYPES)), MinValueValidator(0)])
    width = models.IntegerField('Width in px on screen', default=150)
    content = models.CharField('Content of the column', choices=TYPES, max_length=30, default='estimate_time')
    align = models.CharField('Text align', choices=ALIGN, max_length=30, default='center')

    class Meta:
        ordering = ['-gbaseline', 'pos']

    def __unicode__(self):
        return u'Gb: %s, %s (%s)' % (self.gbaseline.pk, self.pos, self.content)
