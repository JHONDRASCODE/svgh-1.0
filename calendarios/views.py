from django.shortcuts import render
from .models import Calendar
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
import datetime
import json
import logging
from functools import wraps
from django.utils.dateparse import parse_datetime

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

# Nombres de los días para referencia
nombres_dias = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}

def error_handler(func):
    """
    Decorador para manejo de errores en vistas
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {func.__name__}: {str(e)}", exc_info=True)
            return JsonResponse({
                "error": "Se produjo un error en el servidor",
                "detail": str(e),
                "events": []
            }, status=500)
    return wrapper

def cal_eventos(request):
    """
    Renderiza la plantilla principal del calendario
    """
    logger.info("Renderizando plantilla de calendario")
    return render(request, 'calendarios/cal_eventos.html')

def parsear_dias_recurrencia(dias_recurrencia):
    """
    Parsea y valida el campo dias_recurrencia
    """
    if dias_recurrencia is None:
        return []
        
    # Si es string, intentar deserializar como JSON
    if isinstance(dias_recurrencia, str):
        try:
            dias_recurrencia = json.loads(dias_recurrencia)
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar dias_recurrencia: '{dias_recurrencia}'")
            return []
    
    # Asegurar que sea iterable
    if not hasattr(dias_recurrencia, '__iter__'):
        logger.error(f"dias_recurrencia no es iterable: {type(dias_recurrencia)}")
        return []
        
    return dias_recurrencia

def generar_eventos_recurrentes(event, fecha_desde=None, fecha_hasta=None):
    """
    Genera eventos recurrentes a partir de un evento base
    
    Args:
        event: Objeto Calendar
        fecha_desde: Fecha de inicio para filtrar (opcional)
        fecha_hasta: Fecha de fin para filtrar (opcional)
    """
    eventos_recurrentes = []
    try:
        # Determinar fechas de inicio y fin
        fecha_actual = event.start.date()
        fecha_fin = event.end.date()
        
        # Si se proporcionan filtros de fecha, ajustar el rango
        if fecha_desde and fecha_desde > fecha_actual:
            fecha_actual = fecha_desde
        if fecha_hasta and fecha_hasta < fecha_fin:
            fecha_fin = fecha_hasta
        
        # Parsear días de recurrencia
        dias_recurrencia = parsear_dias_recurrencia(event.dias_recurrencia)
        if not dias_recurrencia:
            logger.warning(f"Event {event.id} no tiene días de recurrencia válidos")
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
                        
                        # Generar un ID único para cada instancia
                        unique_id = f"{event.id}_{fecha_actual.strftime('%Y%m%d')}"
                        
                        # Manejo seguro de valores potencialmente nulos
                        programa = f"{event.codigo_programa or ''} - {event.nombre_programa or 'Sin programa'}".strip(' -')
                        instructor = f"{event.nombres_instructor or ''} {event.apellidos_instructor or ''}".strip()
                        ambiente = f"{event.codigo_ambiente or ''} - {event.nombre_ambiente or 'Sin ambiente'}".strip(' -')
                        competencia = f"{event.nombre_competencia or ''} - {event.norma_competencia or ''}".strip(' -') or 'Sin competencia'
                        
                        evento = {
                            'id': unique_id,
                            'id_programa': event.programa_id,
                            'programa': programa,
                            'id_instructor': event.instructor_id,
                            'instructor': instructor,
                            'startDate': hora_inicio.isoformat(),
                            'endDate': hora_fin.isoformat(),
                            'id_ambiente': event.ambiente_id,
                            'ambiente': ambiente,
                            'competencia': competencia
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

@require_GET
@error_handler
def get_all_events(request):
    """
    Obtiene todos los eventos del calendario con sus recurrencias
    
    Parámetros de query:
    - start: Fecha de inicio (ISO format)
    - end: Fecha de fin (ISO format)
    - instructor_id: ID del instructor
    - programa_id: ID del programa
    - ambiente_id: ID del ambiente
    """
    try:
        logger.info("Obteniendo todos los eventos")
        
        # Extraer parámetros de filtro
        fecha_desde_str = request.GET.get('start')
        fecha_hasta_str = request.GET.get('end')
        instructor_id = request.GET.get('instructor_id')
        programa_id = request.GET.get('programa_id')
        ambiente_id = request.GET.get('ambiente_id')
        
        # Parsear fechas si se proporcionan
        fecha_desde = None
        fecha_hasta = None
        
        if fecha_desde_str:
            try:
                fecha_desde = parse_datetime(fecha_desde_str).date()
            except (ValueError, AttributeError):
                logger.warning(f"Formato de fecha inválido para 'start': {fecha_desde_str}")
        
        if fecha_hasta_str:
            try:
                fecha_hasta = parse_datetime(fecha_hasta_str).date()
            except (ValueError, AttributeError):
                logger.warning(f"Formato de fecha inválido para 'end': {fecha_hasta_str}")
        
        # Consulta base con optimización
        events_query = Calendar.objects.all()
        
        # Aplicar filtros a nivel de consulta
        if instructor_id:
            events_query = events_query.filter(instructor_id=instructor_id)
        if programa_id:
            events_query = events_query.filter(programa_id=programa_id)
        if ambiente_id:
            events_query = events_query.filter(ambiente_id=ambiente_id)
        
        # Si se proporcionan fechas, filtrar por superposición con el rango
        if fecha_desde:
            events_query = events_query.filter(end__date__gte=fecha_desde)
        if fecha_hasta:
            events_query = events_query.filter(start__date__lte=fecha_hasta)
        
        # Ejecutar la consulta optimizada
        events = list(events_query)
        
        if not events:
            logger.warning("No se encontraron eventos en la base de datos con los filtros aplicados")
            return JsonResponse({"events": []})
        
        # Generar todos los eventos recurrentes
        event_list = []
        for event in events:
            try:
                # Verificar que el evento tiene los campos necesarios
                if not all([event.start, event.end]):
                    logger.warning(f"Event {event.id} tiene fechas faltantes")
                    continue
                    
                # Generar los eventos recurrentes para este evento base
                eventos_recurrentes = generar_eventos_recurrentes(
                    event, 
                    fecha_desde=fecha_desde, 
                    fecha_hasta=fecha_hasta
                )
                event_list.extend(eventos_recurrentes)
                
            except Exception as e:
                logger.error(f"Error procesando evento {event.id}: {str(e)}")
                continue
        
        # Ordenar eventos por fecha de inicio
        event_list.sort(key=lambda x: x['startDate'])
                
        logger.info(f"Devolviendo {len(event_list)} eventos en total")
        
        # Envolver los eventos en el formato esperado por el frontend
        response_data = {
            "events": event_list
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error general en get_all_events: {str(e)}")
        return JsonResponse({"error": str(e), "events": []}, status=500)

@cache_page(60 * 15)  # Caché de 15 minutos
@require_GET
@error_handler
def get_filter_options(request):
    """
    Obtiene las opciones disponibles para los filtros
    """
    logger.info("Obteniendo opciones de filtro")
    
    try:
        # Recuperar instructores únicos de los eventos
        instructores = set()
        for evento in Calendar.objects.values('instructor_id', 'nombres_instructor', 'apellidos_instructor').distinct():
            if evento['instructor_id']:
                nombre_completo = f"{evento['nombres_instructor'] or ''} {evento['apellidos_instructor'] or ''}".strip()
                instructores.add((evento['instructor_id'], nombre_completo))
        
        # Recuperar programas únicos
        programas = set()
        for evento in Calendar.objects.values('programa_id', 'codigo_programa', 'nombre_programa').distinct():
            if evento['programa_id']:
                nombre = f"{evento['codigo_programa'] or ''} - {evento['nombre_programa'] or ''}".strip(' -')
                programas.add((evento['programa_id'], nombre))
        
        # Recuperar ambientes únicos
        ambientes = set()
        for evento in Calendar.objects.values('ambiente_id', 'codigo_ambiente', 'nombre_ambiente').distinct():
            if evento['ambiente_id']:
                nombre = f"{evento['codigo_ambiente'] or ''} - {evento['nombre_ambiente'] or ''}".strip(' -')
                ambientes.add((evento['ambiente_id'], nombre))
        
        # Convertir a listas ordenadas por nombre
        instructores_list = [{"id": id, "nombre": nombre} for id, nombre in sorted(instructores, key=lambda x: x[1])]
        programas_list = [{"id": id, "nombre": nombre} for id, nombre in sorted(programas, key=lambda x: x[1])]
        ambientes_list = [{"id": id, "nombre": nombre} for id, nombre in sorted(ambientes, key=lambda x: x[1])]
        
        response_data = {
            "instructores": instructores_list,
            "programas": programas_list,
            "ambientes": ambientes_list
        }
        
        logger.info(f"Opciones de filtro obtenidas: {len(instructores_list)} instructores, "
                   f"{len(programas_list)} programas, {len(ambientes_list)} ambientes")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo opciones de filtro: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)