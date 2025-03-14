from django.shortcuts import render
from .models import Calendar
from django.http import JsonResponse
import datetime
import json
import logging

# Configurar el logging para depuración
logger = logging.getLogger(__name__)

# Diccionario para mapear días de la semana a sus valores en Python
dias_semana = {
    "lunes": 0, 
    "martes": 1, 
    "miércoles": 2, 
    "miercoles": 2,  # versión sin tilde
    "jueves": 3, 
    "viernes": 4, 
    "sábado": 5, 
    "sabado": 5,     # versión sin tilde
    "domingo": 6
}

def cal_eventos(request):
    """
    Renderiza la plantilla principal del calendario
    """
    logger.info("Renderizando plantilla de calendario")
    return render(request, 'calendarios/cal_eventos.html')

def generar_eventos_recurrentes(event):
    """
    Genera eventos recurrentes a partir de un evento base
    """
    eventos_recurrentes = []
    try:
        fecha_actual = event.start.date()  # Fecha de inicio
        fecha_fin = event.end.date()       # Fecha de fin
        
        # Asegurarse de que dias_recurrencia es un objeto iterable
        dias_recurrencia = []
        
        if event.dias_recurrencia is None:
            logger.warning(f"Event {event.id} tiene dias_recurrencia None")
            return eventos_recurrentes
            
        # Si es string, intentar deserializar como JSON
        if isinstance(event.dias_recurrencia, str):
            try:
                dias_recurrencia = json.loads(event.dias_recurrencia)
                logger.info(f"Convertido dias_recurrencia string a lista: {dias_recurrencia}")
            except json.JSONDecodeError:
                logger.error(f"Error al decodificar dias_recurrencia: '{event.dias_recurrencia}'")
                return eventos_recurrentes
        else:
            dias_recurrencia = event.dias_recurrencia
            
        # Si después de todo, no es iterable, devolver lista vacía
        if not hasattr(dias_recurrencia, '__iter__'):
            logger.error(f"dias_recurrencia no es iterable: {type(dias_recurrencia)}")
            return eventos_recurrentes
            
        logger.info(f"Generando eventos recurrentes para event_id={event.id}, "
                   f"start={event.start}, end={event.end}, dias={dias_recurrencia}")

        # Generar eventos recurrentes entre start y end
        while fecha_actual <= fecha_fin:
            dia_semana_actual = fecha_actual.weekday()
            for dia in dias_recurrencia:
                try:
                    # Convertir el nombre del día a número de día de la semana (0-6)
                    if isinstance(dia, str):
                        dia_lower = dia.lower().strip()
                        if dia_lower in dias_semana:
                            dia_recurrencia = dias_semana[dia_lower]
                        else:
                            logger.warning(f"Día '{dia}' no reconocido en el diccionario")
                            continue
                    elif isinstance(dia, int) and 0 <= dia <= 6:
                        dia_recurrencia = dia
                    else:
                        logger.warning(f"Formato de día no válido: {dia}, tipo: {type(dia)}")
                        continue
                        
                    # Si el día actual coincide con el día de recurrencia, añadir evento
                    if dia_semana_actual == dia_recurrencia:
                        # Crear el evento para este día
                        hora_inicio = datetime.datetime.combine(fecha_actual, event.start.time())
                        hora_fin = datetime.datetime.combine(fecha_actual, event.end.time())
                        
                        evento = {
                            'id_programa': event.programa_id,
                            'programa': f"{event.codigo_programa} - {event.nombre_programa}",
                            'id_instructor': event.instructor_id,
                            'instructor': f"{event.nombres_instructor} {event.apellidos_instructor}",
                            'startDate': hora_inicio.isoformat(),
                            'endDate': hora_fin.isoformat(),
                            'id_ambiente': event.ambiente_id,
                            'ambiente': f"{event.codigo_ambiente} - {event.nombre_ambiente}",
                            'competencia': f"{event.nombre_competencia} - {event.norma_competencia}",
                        }
                        eventos_recurrentes.append(evento)
                        logger.debug(f"Evento añadido para el {fecha_actual.strftime('%d/%m/%Y')} "
                                   f"(día {dia_semana_actual}): {evento['programa']}")
                except Exception as e:
                    logger.error(f"Error procesando día {dia}: {str(e)}")
                    continue
                    
            # Avanzar al siguiente día
            fecha_actual += datetime.timedelta(days=1)
            
        logger.info(f"Total de eventos recurrentes generados: {len(eventos_recurrentes)}")
        
    except Exception as e:
        logger.error(f"Error general en generar_eventos_recurrentes: {str(e)}")
        
    return eventos_recurrentes

def get_all_events(request):
    """
    Obtiene todos los eventos del calendario con sus recurrencias
    """
    try:
        logger.info("Obteniendo todos los eventos")
        events = Calendar.objects.all()
        
        if not events:
            logger.warning("No se encontraron eventos en la base de datos")
            
        event_list = []
        for event in events:
            try:
                # Verificar que el evento tiene los campos necesarios
                if not all([event.start, event.end, event.dias_recurrencia]):
                    logger.warning(f"Event {event.id} tiene campos faltantes: "
                                  f"start={event.start}, end={event.end}, "
                                  f"dias_recurrencia={event.dias_recurrencia}")
                    continue
                    
                # Generar los eventos recurrentes para este evento base
                eventos_recurrentes = generar_eventos_recurrentes(event)
                event_list.extend(eventos_recurrentes)
                
            except Exception as e:
                logger.error(f"Error procesando evento {event.id}: {str(e)}")
                continue
                
        logger.info(f"Devolviendo {len(event_list)} eventos en total")
        
        # Envolver los eventos en el formato esperado por el frontend
        response_data = {
            "events": event_list
        }
        
        return JsonResponse(response_data, safe=False)
        
    except Exception as e:
        logger.error(f"Error general en get_all_events: {str(e)}")
        return JsonResponse({"error": str(e), "events": []}, status=500)