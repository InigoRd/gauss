from django.contrib import admin

# Register your models here.
from models import *

admin.site.register(Budget_file)
admin.site.register(Gbudget)
admin.site.register(Vrecord)
admin.site.register(Vrecord_label)
admin.site.register(Krecord)
admin.site.register(Krecord_scope)

@admin.register(Crecord)
class CrecordAdmin(admin.ModelAdmin):
    list_filter = ('gbudget',)
    search_fields = ['code']

# admin.site.register(Crecord)
admin.site.register(Crecord_alias)
admin.site.register(Crecord_price)
admin.site.register(Drecord)
admin.site.register(Drecord_percentage_code)
admin.site.register(Rrecord)
admin.site.register(Rrecord_property)
admin.site.register(Wrecord)
admin.site.register(Lrecord)
admin.site.register(Lrecord_section)
admin.site.register(Qrecord)
admin.site.register(Jrecord)
admin.site.register(Grecord)
admin.site.register(Erecord)
admin.site.register(Xrecord)
admin.site.register(Xrecord_ti)
admin.site.register(Id_bim)
admin.site.register(Mrecord)
admin.site.register(Mrecord_type)
admin.site.register(Arecord)
admin.site.register(Frecord)
admin.site.register(Frecord_files)
