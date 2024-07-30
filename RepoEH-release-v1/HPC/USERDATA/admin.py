from django.contrib import admin

from .models import *


admin.site.register(Documentacion)
admin.site.register(Sucursal)
admin.site.register(Semana)
admin.site.register(Turno)
admin.site.register(Mes)
admin.site.register(Vacante)
admin.site.register(Nivel_educativo)
admin.site.register(Pagos)
admin.site.site_header = "Panel Administrador Hipocampo"