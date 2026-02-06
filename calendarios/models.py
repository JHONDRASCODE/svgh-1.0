from django.core.exceptions import ValidationError
from django.db import models

from horarios.models import Ambiente, Competencia, Instructor, ProgramaFormacion


class Calendar(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    programa = models.ForeignKey(ProgramaFormacion, on_delete=models.CASCADE)
    ambiente = models.ForeignKey(Ambiente, on_delete=models.CASCADE)
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    start = models.DateTimeField(null=True, blank=True, verbose_name="Inicio de la formación")
    end = models.DateTimeField(null=True, blank=True, verbose_name="Fin de la formación")
    dias_recurrencia = models.JSONField()

    class Meta:
        db_table = "calendar"

    def clean(self):
        if self.start and self.end and self.end <= self.start:
            raise ValidationError(
                "La fecha y hora de finalización de la formación debe ser mayor que la fecha y hora de inicio."
            )

    def __str__(self):
        return (
            f"{self.instructor.nombres} - {self.programa.nombre_programa} - "
            f"{self.ambiente.nombre_ambiente} - {self.competencia.nombre}"
        )

    @property
    def nombres_instructor(self):
        return self.instructor.nombres

    @property
    def apellidos_instructor(self):
        return self.instructor.apellidos

    @property
    def codigo_programa(self):
        return self.programa.codigo_programa

    @property
    def nombre_programa(self):
        return self.programa.nombre_programa

    @property
    def codigo_ambiente(self):
        return self.ambiente.codigo_ambiente

    @property
    def nombre_ambiente(self):
        return self.ambiente.nombre_ambiente

    @property
    def norma_competencia(self):
        return self.competencia.codigo_norma

    @property
    def nombre_competencia(self):
        return self.competencia.nombre
