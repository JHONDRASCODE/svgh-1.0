from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q

# -----------------------
# MANAGER PERSONALIZADO
# -----------------------

class AdministradorManager(BaseUserManager):
    def create_user(self, correo_institucional, password=None, **extra_fields):
        if not correo_institucional:
            raise ValueError("El correo institucional debe ser proporcionado")
        
        email = self.normalize_email(correo_institucional)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', False)
        extra_fields.setdefault('is_active', True)
        
        user = self.model(correo_institucional=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo_institucional, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not all([
            extra_fields.get('is_admin'),
            extra_fields.get('is_staff'),
            extra_fields.get('is_superuser')
        ]):
            raise ValueError("Superuser debe tener is_admin, is_staff e is_superuser en True.")

        return self.create_user(correo_institucional, password, **extra_fields)

# -----------------------
# MODELOS PRINCIPALES
# -----------------------

class Administrador(AbstractBaseUser, PermissionsMixin):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    numero_cedula = models.CharField(max_length=20, unique=True)
    numero_celular = models.CharField(max_length=20)
    correo_institucional = models.EmailField(unique=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = AdministradorManager()

    USERNAME_FIELD = 'correo_institucional'
    REQUIRED_FIELDS = ['nombres', 'apellidos', 'numero_cedula', 'numero_celular']

    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    def nombre_completo(self):
        return self.__str__()

    def get_short_name(self):
        return self.nombres

    def get_username(self):
        return getattr(self, self.USERNAME_FIELD)

    @property
    def email(self):
        return self.correo_institucional

class Instructor(models.Model):
    nombres = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=50)
    correo_institucional = models.EmailField()
    numero_celular = models.CharField(max_length=15)
    numero_cedula = models.CharField(max_length=15, unique=True)
    competencias_imparte = models.CharField(max_length=255)

    class Meta:
        db_table = "Instructor"
        verbose_name = "Instructor"
        verbose_name_plural = "Instructores"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    def nombre_completo(self):
        return self.__str__()

class ProgramaFormacion(models.Model):
    class Jornada(models.TextChoices):
        MAÑANA = 'Mañana', 'Mañana'
        TARDE = 'Tarde', 'Tarde'
        NOCHE = 'Noche', 'Noche'

    codigo_programa = models.CharField(max_length=15)
    nombre_programa = models.CharField(max_length=100)
    jornada = models.CharField(max_length=50, choices=Jornada.choices)
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
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError("La fecha de fin debe ser mayor que la fecha de inicio.")

class Ambiente(models.Model):
    class Sede(models.TextChoices):
        PRINCIPAL = 'Principal', 'Principal'
        ALTERNATIVA = 'Alternativa', 'Alternativa'
        GRANJA = 'Granja', 'Granja'

    codigo_ambiente = models.CharField(max_length=15)
    nombre_ambiente = models.CharField(max_length=100)
    sede = models.CharField(max_length=100, choices=Sede.choices)

    class Meta:
        db_table = "Ambiente"
        verbose_name = "Ambiente"
        verbose_name_plural = "Ambientes"

    def __str__(self):
        return self.nombre_ambiente

class Competencia(models.Model):
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

# -----------------------
# ACTIVIDAD DEL SISTEMA
# -----------------------

class ActividadSistemaManager(models.Manager):
    def get_no_leidas(self):
        return self.filter(leido=False)

    def get_no_leidas_count(self):
        return self.get_no_leidas().count()

    def marcar_todas_como_leidas(self):
        return self.update(leido=True)

    def get_recientes(self, limit=10):
        return self.all().order_by('-fecha_hora')[:limit]

    def filtrar_por_tipo(self, tipo):
        return self.filter(tipo=tipo)

    def buscar(self, query):
        return self.filter(
            Q(descripcion__icontains=query) |
            Q(elemento_nombre__icontains=query) |
            Q(usuario__nombres__icontains=query) |
            Q(usuario__apellidos__icontains=query)
        ).distinct()

class ActividadSistema(models.Model):
    class Tipo(models.TextChoices):
        INSTRUCTOR = 'instructor', 'Instructor'
        COMPETENCIA = 'competencia', 'Competencia'
        PROGRAMA = 'programa', 'Programa de Formación'
        AMBIENTE = 'ambiente', 'Ambiente'
        HORARIO = 'horario', 'Horario'

    class Accion(models.TextChoices):
        CREAR = 'crear', 'Creación'
        EDITAR = 'editar', 'Edición'
        ELIMINAR = 'eliminar', 'Eliminación'
        GENERAR = 'generar', 'Generación'

    usuario = models.ForeignKey(
        Administrador,
        on_delete=models.CASCADE,
        related_name='actividades'
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    accion = models.CharField(max_length=20, choices=Accion.choices)
    descripcion = models.CharField(max_length=255)
    elemento_id = models.IntegerField(null=True, blank=True)
    elemento_nombre = models.CharField(max_length=255, blank=True)
    fecha_hora = models.DateTimeField(default=timezone.now, db_index=True)
    leido = models.BooleanField(default=False, verbose_name="Leído", db_index=True)

    objects = ActividadSistemaManager()

    class Meta:
        db_table = "ActividadSistema"
        ordering = ['-fecha_hora']
        verbose_name = "Actividad del Sistema"
        verbose_name_plural = "Actividades del Sistema"
        indexes = [
            models.Index(fields=['leido', 'fecha_hora']),
        ]

    def __str__(self):
        return f"{self.get_accion_display()} de {self.get_tipo_display()}: {self.descripcion}"

    def marcar_como_leida(self):
        self.leido = True
        self.save(update_fields=['leido'])
        return True

    def tiempo_transcurrido(self):
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
            return self.fecha_hora.strftime("el %d/%m/%Y a las %H:%M")
