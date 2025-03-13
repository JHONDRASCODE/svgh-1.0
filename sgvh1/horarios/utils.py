import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font
from django.conf import settings
from .models import Instructor, ActividadSistema
import os
from django.utils import timezone

def create_instructor_template():
    try:
        # Obtener todos los instructores de la base de datos
        instructores = Instructor.objects.all()
        
        # Crear lista de datos
        data = []
        for instructor in instructores:
            data.append({
                'nombres': instructor.nombres,
                'apellidos': instructor.apellidos,
                'correo_institucional': instructor.correo_institucional,
                'numero_celular': instructor.numero_celular,
                'numero_cedula': instructor.numero_cedula
            })
        
        # Crear DataFrame con los datos de los instructores
        df = pd.DataFrame(data)
        
        # Si no hay instructores, crear una plantilla vacía con las columnas
        if df.empty:
            df = pd.DataFrame(columns=[
                'nombres',
                'apellidos',
                'correo_institucional',
                'numero_celular',
                'numero_cedula'
            ])
            # Añadir una fila de ejemplo
            df.loc[0] = [
                'Juan Carlos',
                'Pérez González',
                'jperez@sena.edu.co',
                '3001234567',
                '1234567890'
            ]

        # Asegurarse de que el directorio existe
        template_dir = os.path.join(settings.STATIC_ROOT, 'templates')
        os.makedirs(template_dir, exist_ok=True)

        # Guardar la plantilla
        template_path = os.path.join(template_dir, 'plantilla_instructores.xlsx')
        
        # Configurar el writer para dar formato al Excel
        writer = pd.ExcelWriter(template_path, engine='openpyxl')
        
        # Escribir el DataFrame al Excel con formato
        df.to_excel(writer, index=False, sheet_name='Instructores')
        
        # Obtener la hoja activa
        worksheet = writer.sheets['Instructores']
        
        # Ajustar el ancho de las columnas
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length
        
        # Dar formato al encabezado
        for cell in worksheet[1]:
            cell.style = 'Headline 3'
            cell.fill = openpyxl.styles.PatternFill(
                start_color='E2EFDA',
                end_color='E2EFDA',
                fill_type='solid'
            )
        
        # Guardar el archivo con el formato
        writer.close()
        
        return template_path
        
    except Exception as e:
        print(f"Error creando la plantilla: {str(e)}")
        raise e

# Nueva función para registrar actividades del sistema
def registrar_actividad(usuario, tipo, accion, descripcion, elemento_id=None, elemento_nombre=None):
    """
    Registra una actividad en el sistema.
    
    Args:
        usuario: Usuario que realiza la acción (objeto Administrador)
        tipo: Tipo de elemento (instructor, competencia, programa, ambiente, horario)
        accion: Acción realizada (crear, editar, eliminar, generar)
        descripcion: Descripción detallada de la actividad
        elemento_id: ID del elemento afectado (opcional)
        elemento_nombre: Nombre o identificador del elemento (opcional)
    
    Returns:
        La instancia de ActividadSistema creada
    """
    try:
        actividad = ActividadSistema.objects.create(
            usuario=usuario,
            tipo=tipo,
            accion=accion,
            descripcion=descripcion,
            elemento_id=elemento_id,
            elemento_nombre=elemento_nombre,
            fecha_hora=timezone.now()
        )
        return actividad
    except Exception as e:
        print(f"Error al registrar actividad: {str(e)}")
        # En producción, podrías querer manejar este error de otra manera
        # Por ejemplo, enviando una notificación al administrador
        return None

# Función para obtener las actividades recientes, excluyendo actividades de administradores
def obtener_actividades_recientes(limite=10):
    """
    Obtiene una lista de las actividades más recientes del sistema,
    excluyendo las actividades relacionadas con administradores.
    
    Args:
        limite: Número máximo de actividades a obtener (por defecto: 10)
        
    Returns:
        QuerySet con las actividades ordenadas por fecha descendente
    """
    return ActividadSistema.objects.exclude(tipo='administrador').order_by('-fecha_hora')[:limite]

# Función para obtener actividades recientes por tipo
def obtener_actividades_por_tipo(tipo, limite=10):
    """
    Obtiene las actividades recientes filtradas por tipo.
    
    Args:
        tipo: Tipo de actividad ('instructor', 'competencia', etc.)
        limite: Número máximo de actividades a obtener
        
    Returns:
        QuerySet con las actividades del tipo especificado
    """
    return ActividadSistema.objects.filter(tipo=tipo).order_by('-fecha_hora')[:limite]

# Función para obtener actividades recientes por usuario
def obtener_actividades_por_usuario(usuario_id, limite=10):
    """
    Obtiene las actividades recientes realizadas por un usuario específico.
    
    Args:
        usuario_id: ID del usuario (Administrador)
        limite: Número máximo de actividades a obtener
        
    Returns:
        QuerySet con las actividades del usuario especificado
    """
    return ActividadSistema.objects.filter(usuario_id=usuario_id).order_by('-fecha_hora')[:limite]

# Función para formatear la descripción de una actividad de creación
def generar_descripcion_creacion(tipo, elemento_nombre):
    """
    Genera una descripción estándar para actividades de creación.
    
    Args:
        tipo: Tipo de elemento creado
        elemento_nombre: Nombre del elemento creado
        
    Returns:
        Cadena con la descripción formateada
    """
    tipo_formateado = tipo.capitalize()
    if tipo == 'instructor':
        return f"Se creó el instructor {elemento_nombre}"
    elif tipo == 'competencia':
        return f"Se creó la competencia '{elemento_nombre}'"
    elif tipo == 'programa':
        return f"Se creó el programa de formación '{elemento_nombre}'"
    elif tipo == 'ambiente':
        return f"Se creó el ambiente '{elemento_nombre}'"
    elif tipo == 'horario':
        return f"Se generó un horario para {elemento_nombre}"
    else:
        return f"Se creó {tipo_formateado}: {elemento_nombre}"