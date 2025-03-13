from django.db import models
from horarios.models import Instructor, ProgramaFormacion, Ambiente, Competencia

# Create your models here.
class HorarioI(models.Model):
    programa = models.ForeignKey(ProgramaFormacion, on_delete=models.CASCADE)
    ambiente = models.ForeignKey(Ambiente, on_delete=models.CASCADE)
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    
class HorarioA(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    programa = models.ForeignKey(ProgramaFormacion, on_delete=models.CASCADE)
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    
class HorarioPF(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    ambiente = models.ForeignKey(Ambiente, on_delete=models.CASCADE)
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    
class HorarioCC(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    ambiente = models.ForeignKey(Ambiente, on_delete=models.CASCADE)
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)