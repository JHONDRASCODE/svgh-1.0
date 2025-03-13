from django.shortcuts import render
from .models import Calendar
from django.http import JsonResponse
import datetime

# Diccionario para mapear días de la semana a sus valores en Python
dias_semana = {"lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3, "viernes": 4, "sábado": 5, "domingo": 6}

def cal_eventos(request):
    # Renderiza la plantilla principal del calendario
    return render(request, 'calendarios/cal_eventos.html')

def generar_eventos_recurrentes(event):
    eventos_recurrentes = []
    fecha_actual = event.start.date()  # Fecha de inicio
    fecha_fin = event.end.date()  # Fecha de fin

    # Generar eventos recurrentes entre start y end
    while fecha_actual <= fecha_fin:
        dia_semana_actual = fecha_actual.weekday()
        for dia in event.dias_recurrencia:
            dia_recurrencia = dias_semana[dia.lower()]
            if dia_semana_actual == dia_recurrencia:
                eventos_recurrentes.append({
                    'id_programa': event.programa_id,
                    'programa': f"{event.codigo_programa} - {event.nombre_programa}",
                    'id_instructor': event.instructor_id,
                    'instructor': f"{event.nombres_instructor} {event.apellidos_instructor}",
                    'startDate': datetime.datetime.combine(fecha_actual, event.start.time()).isoformat(),
                    'endDate': datetime.datetime.combine(fecha_actual, event.end.time()).isoformat(),
                    'id_ambiente': event.ambiente_id,
                    'ambiente': f"{event.codigo_ambiente} - {event.nombre_ambiente}",
                    'competencia':  f"{event.nombre_competencia} - {event.norma_competencia}",
                })
        fecha_actual += datetime.timedelta(days=1)

    return eventos_recurrentes

def get_all_events(request):
    events = Calendar.objects.all()
    event_list = []
    for event in events:
        # Generar los eventos recurrentes por cada evento en la base de datos
        eventos_recurrentes = generar_eventos_recurrentes(event)
        event_list.extend(eventos_recurrentes)

    # Envolver los eventos en el formato solicitado
    response_data = {
        "events": event_list
    }

    return JsonResponse(response_data, safe=False)
