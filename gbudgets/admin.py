from django.contrib import admin

# Register your models here.
from models import *

admin.site.register(Budget_file)
admin.site.register(Gbudget)
admin.site.register(Vrecord)
admin.site.register(Krecord)
admin.site.register(Krecord_scope)
admin.site.register(Crecord)
admin.site.register(Crecord_alias)
admin.site.register(Crecord_price)