from rest_framework import serializers
from .models import Calendar

class CalendarSerializer(serializers.ModelSerializer):
    nombres_instructor = serializers.ReadOnlyField()
    apellidos_instructor = serializers.ReadOnlyField()
    codigo_programa = serializers.ReadOnlyField()
    nombre_programa = serializers.ReadOnlyField()
    codigo_ambiente = serializers.ReadOnlyField()
    nombre_ambiente = serializers.ReadOnlyField()
    norma_competencia = serializers.ReadOnlyField()
    nombre_competencia = serializers.ReadOnlyField()

    class Meta:
        model = Calendar
        fields = [
            'id',
            'instructor',
            'programa',
            'ambiente',
            'competencia',
            'start',
            'end',
            'nombres_instructor',
            'apellidos_instructor',
            'codigo_programa',
            'nombre_programa',
            'codigo_ambiente',
            'nombre_ambiente',
            'norma_competencia',
            'nombre_competencia',
        ]
