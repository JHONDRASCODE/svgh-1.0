from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from calendarios.models import Calendar
from calendarios.serializers import CalendarSerializer
from horarios.models import Ambiente, Competencia, Instructor, ProgramaFormacion


class CalendarModelTests(TestCase):
    def setUp(self):
        self.instructor = Instructor.objects.create(
            nombres="Ana",
            apellidos="Gomez",
            correo_institucional="ana@sena.edu.co",
            numero_celular="3000000000",
            numero_cedula="123456",
            competencias_imparte="Programación",
        )
        self.programa = ProgramaFormacion.objects.create(
            codigo_programa="ADSO",
            nombre_programa="Análisis y Desarrollo",
            jornada=ProgramaFormacion.Jornada.MAÑANA,
            numero_ficha="99999",
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=30),
        )
        self.ambiente = Ambiente.objects.create(
            codigo_ambiente="A1",
            nombre_ambiente="Laboratorio 1",
            sede=Ambiente.Sede.PRINCIPAL,
        )
        self.competencia = Competencia.objects.create(
            nombre="Backend",
            codigo_norma=1234,
            unidad_competencia="Construcción de servicios web",
            duracion_estimada="40",
            resultado_aprendizaje="Implementar endpoints REST",
        )

    def test_calendar_clean_rejects_end_before_start(self):
        start = timezone.now()
        calendar = Calendar(
            instructor=self.instructor,
            programa=self.programa,
            ambiente=self.ambiente,
            competencia=self.competencia,
            start=start,
            end=start - timedelta(hours=1),
            dias_recurrencia=["lunes", "martes"],
        )

        with self.assertRaises(ValidationError):
            calendar.clean()

    def test_calendar_clean_allows_null_dates(self):
        calendar = Calendar(
            instructor=self.instructor,
            programa=self.programa,
            ambiente=self.ambiente,
            competencia=self.competencia,
            start=None,
            end=None,
            dias_recurrencia=["jueves"],
        )

        calendar.clean()


class CalendarSerializerTests(TestCase):
    def setUp(self):
        self.instructor = Instructor.objects.create(
            nombres="Luis",
            apellidos="Diaz",
            correo_institucional="luis@sena.edu.co",
            numero_celular="3111111111",
            numero_cedula="654321",
            competencias_imparte="Bases de datos",
        )
        self.programa = ProgramaFormacion.objects.create(
            codigo_programa="TIC",
            nombre_programa="Tecnologías de la Información",
            jornada=ProgramaFormacion.Jornada.TARDE,
            numero_ficha="77777",
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=45),
        )
        self.ambiente = Ambiente.objects.create(
            codigo_ambiente="B2",
            nombre_ambiente="Aula TIC",
            sede=Ambiente.Sede.ALTERNATIVA,
        )
        self.competencia = Competencia.objects.create(
            nombre="SQL",
            codigo_norma=5678,
            unidad_competencia="Diseño de consultas",
            duracion_estimada="20",
            resultado_aprendizaje="Construir consultas optimizadas",
        )

    def test_serializer_exposes_dias_recurrencia(self):
        calendar = Calendar.objects.create(
            instructor=self.instructor,
            programa=self.programa,
            ambiente=self.ambiente,
            competencia=self.competencia,
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=2),
            dias_recurrencia=["lunes", "viernes"],
        )

        data = CalendarSerializer(calendar).data

        self.assertIn("dias_recurrencia", data)
        self.assertEqual(data["dias_recurrencia"], ["lunes", "viernes"])
