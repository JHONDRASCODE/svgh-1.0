from django.contrib import admin
from .models import Calendar

@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    list_display = ['instructor', 'programa', 'ambiente', 'competencia', 'start', 'end', 'dias_recurrencia']
    list_filter = ['instructor', 'programa', 'ambiente']
    search_fields = ['instructor__nombres', 'programa__nombre_programa', 'ambiente__nombre_ambiente']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('instructor', 'programa', 'ambiente', 'competencia')
        }),
        ('Horario', {
            'fields': ('start', 'end', 'dias_recurrencia'),
            'description': 'Seleccione las fechas y días de recurrencia'
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si es una edición
            return []  # No hay campos de solo lectura
        return []  # No hay campos de solo lectura en la creación

    def save_model(self, request, obj, form, change):
        if not change:  # Si es una creación nueva
            obj.save()
        super().save_model(request, obj, form, change)
