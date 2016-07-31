from django.contrib import admin

# Register your models here.
from models import *

admin.site.register(Gproject)
# admin.site.register(Gcalendar)
# admin.site.register(Gday)
# admin.site.register(Gtime_slot)
# admin.site.register(Gresource)
admin.site.register(Gbaseline)
admin.site.register(Gtask)
admin.site.register(Gtask_link)
admin.site.register(Gcolumn)

