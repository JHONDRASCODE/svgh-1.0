from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q

class AdministradorManager(BaseUserManager):
    def create_user(self, correo_institucional, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el correo institucional y contraseña dada.
        """
        if not correo_institucional:
            raise ValueError("El correo institucional debe ser proporcionado")
        
        # Normalizar el correo (convertir a minúsculas, etc.)
        email = self.normalize_email(correo_institucional)
        
        # Configurar valores predeterminados
        extra_fields.setdefault('is_staff', True)  # Los administradores deben tener acceso al panel
        extra_fields.setdefault('is_admin', False)  # No todos los usuarios creados son administradores
        extra_fields.setdefault('is_active', True)  # Por defecto, los usuarios están activos
        
        # Crear el usuario
        user = self.model(correo_institucional=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo_institucional, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el correo institucional y contraseña dada.
        """
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser debe tener is_admin=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(correo_institucional, password, **extra_fields)

class Administrador(AbstractBaseUser, PermissionsMixin):
    """
    Modelo personalizado para los administradores del sistema.
    Reemplaza al modelo User estándar de Django.
    """
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    numero_cedula = models.CharField(max_length=20, unique=True)
    numero_celular = models.CharField(max_length=20)
    correo_institucional = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)  # Define si tienen acceso al panel de administración
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)  # Campo útil para saber cuándo se creó la cuenta

    objects = AdministradorManager()

    # Campo que se usará como identificador principal para login
    USERNAME_FIELD = 'correo_institucional'
    
    # Campos requeridos al crear un usuario con createsuperuser (además del USERNAME_FIELD y password)
    REQUIRED_FIELDS = ['nombres', 'apellidos', 'numero_cedula', 'numero_celular']

    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    def get_short_name(self):
        """Devuelve el nombre corto del usuario."""
        return self.nombres
    
    def get_username(self):
        """Método que devuelve el identificador principal para autenticación."""
        return getattr(self, self.USERNAME_FIELD)

class Instructor(models.Model):
    """Modelo para instructores del sistema."""
    nombres = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=50)
    correo_institucional = models.EmailField()
    numero_celular = models.CharField(max_length=15)
    numero_cedula = models.CharField(max_length=15, unique=True)
    competencias_imparte = models.CharField(max_length=255)  # Ampliado a 255 caracteres
    
    class Meta:
        db_table = "Instructor"
        verbose_name = "Instructor"
        verbose_name_plural = "Instructores"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    
    def nombre_completo(self):
        """Método para obtener el nombre completo."""
        return f"{self.nombres} {self.apellidos}"

class ProgramaFormacion(models.Model):
    """Modelo para programas de formación."""
    JORNADAS = [
        ('Mañana', 'Mañana'),
        ('Tarde', 'Tarde'),
        ('Noche', 'Noche')
    ]
    codigo_programa = models.CharField(max_length=15)
    nombre_programa = models.CharField(max_length=100)  # Ampliado a 100 caracteres
    jornada = models.CharField(max_length=50, choices=JORNADAS)
    numero_ficha = models.CharField(max_length=10)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    class Meta:
        db_table = "ProgramaFormacion"
        verbose_name = "Programa de Formación"
        verbose_name_plural = "Programas de Formación"

    def __str__(self):
        return self.nombre_programa

    def clean(self):
        # Verificar que la fecha_fin sea mayor que la fecha_inicio
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError("La fecha de fin debe ser mayor que la fecha de inicio.")

class Ambiente(models.Model):
    """Modelo para ambientes físicos."""
    SEDE = [
        ('Principal', 'Principal'),
        ('Alternativa', 'Alternativa'),
        ('Granja', 'Granja')
    ]
    codigo_ambiente = models.CharField(max_length=15)
    nombre_ambiente = models.CharField(max_length=100)
    sede = models.CharField(max_length=100, choices=SEDE)
    
    class Meta:
        db_table = "Ambiente"
        verbose_name = "Ambiente"
        verbose_name_plural = "Ambientes"

    def __str__(self):
        return self.nombre_ambiente

class Competencia(models.Model):
    """Modelo para competencias académicas."""
    nombre = models.CharField(max_length=100)
    codigo_norma = models.IntegerField(blank=True, null=True, verbose_name="Código de la norma")
    unidad_competencia = models.CharField(max_length=500)
    duracion_estimada = models.CharField(
        max_length=50, 
        help_text="Duración estimada para lograr el aprendizaje", 
        verbose_name="Duración estimada (horas)"
    )
    resultado_aprendizaje = models.TextField()
    
    class Meta:
        db_table = "Competencia"
        verbose_name = "Competencia"
        verbose_name_plural = "Competencias"
        
    def __str__(self):
        return self.nombre

class ActividadSistemaManager(models.Manager):
    """Manager personalizado para el modelo ActividadSistema"""
    
    def get_no_leidas(self):
        """Retorna todas las actividades no leídas"""
        return self.filter(leido=False)
    
    def get_no_leidas_count(self):
        """Retorna la cantidad de actividades no leídas"""
        return self.filter(leido=False).count()
    
    def marcar_todas_como_leidas(self):
        """Marca todas las actividades como leídas"""
        return self.update(leido=True)
    
    def get_recientes(self, limit=10):
        """Retorna las actividades más recientes"""
        return self.all().order_by('-fecha_hora')[:limit]
    
    def filtrar_por_tipo(self, tipo):
        """Filtra actividades por tipo"""
        return self.filter(tipo=tipo)
    
    def buscar(self, query):
        """Busca actividades por término de búsqueda"""
        return self.filter(
            Q(descripcion__icontains=query) |
            Q(elemento_nombre__icontains=query) |
            Q(usuario__nombres__icontains=query) |
            Q(usuario__apellidos__icontains=query)
        ).distinct()

class ActividadSistema(models.Model):
    """
    Modelo para registrar actividades del sistema y gestionar notificaciones.
    Cada actividad representa una acción realizada por un administrador.
    """
    TIPO_CHOICES = (
        ('instructor', 'Instructor'),
        ('competencia', 'Competencia'),
        ('programa', 'Programa de Formación'),
        ('ambiente', 'Ambiente'),
        ('horario', 'Horario'),
    )
    
    ACCION_CHOICES = (
        ('crear', 'Creación'),
        ('editar', 'Edición'),
        ('eliminar', 'Eliminación'),
        ('generar', 'Generación'),
    )
    
    # Usuario que realizó la acción
    usuario = models.ForeignKey(
        Administrador, 
        on_delete=models.CASCADE, 
        related_name='actividades'
    )
    
    # Tipo de elemento afectado
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    # Acción realizada
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    
    # Descripción de la actividad
    descripcion = models.CharField(max_length=255)
    
    # ID del elemento afectado (opcional, para enlaces)
    elemento_id = models.IntegerField(null=True, blank=True)
    
    # Nombre del elemento afectado (ej: nombre del instructor)
    elemento_nombre = models.CharField(max_length=255, blank=True)
    
    # Fecha y hora de la actividad
    fecha_hora = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Indica si la notificación ha sido leída
    leido = models.BooleanField(default=False, verbose_name="Leído", db_index=True)
    
    # Manager personalizado
    objects = ActividadSistemaManager()
    
    class Meta:
        db_table = "ActividadSistema"
        ordering = ['-fecha_hora']
        verbose_name = "Actividad del Sistema"
        verbose_name_plural = "Actividades del Sistema"
        indexes = [
            models.Index(fields=['leido', 'fecha_hora']),  # Índice para mejorar rendimiento en consultas frecuentes
        ]
    
    def __str__(self):
        return f"{self.get_accion_display()} de {self.get_tipo_display()}: {self.descripcion}"
        
    def marcar_como_leida(self):
        """Marca la notificación como leída y guarda el cambio."""
        self.leido = True
        self.save(update_fields=['leido'])
        return True
    
    def tiempo_transcurrido(self):
        """Retorna el tiempo transcurrido desde la actividad en formato legible."""
        ahora = timezone.now()
        diferencia = ahora - self.fecha_hora
        
        segundos = diferencia.total_seconds()
        
        if segundos < 60:
            return "Hace un momento"
        elif segundos < 3600:
            minutos = int(segundos / 60)
            return f"Hace {minutos} {'minuto' if minutos == 1 else 'minutos'}"
        elif segundos < 86400:
            horas = int(segundos / 3600)
            return f"Hace {horas} {'hora' if horas == 1 else 'horas'}"
        elif segundos < 604800:
            dias = int(segundos / 86400)
            return f"Hace {dias} {'día' if dias == 1 else 'días'}"
        else:
            return self.fecha_hora.strftime('%d/%m/%Y')
    
    def obtener_icono(self):
        """Retorna el icono adecuado para Bootstrap Icons según el tipo de actividad"""
        if self.tipo == 'instructor':
            return "bi-person-fill"
        elif self.tipo == 'programa':
            return "bi-folder-fill"
        elif self.tipo == 'competencia':
            return "bi-journal-fill"
        elif self.tipo == 'ambiente':
            return "bi-building"
        elif self.tipo == 'horario':
            return "bi-calendar-week"
        else:
            return "bi-clock-history"