from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Administrador, Instructor, ProgramaFormacion, Ambiente, Competencia
from calendarios.models import Calendar
from django.contrib.auth.forms import UserCreationForm
from django import forms

class AdministradorForm(UserCreationForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="La contraseña debe tener al menos 8 caracteres."
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Repita la contraseña para verificar."
    )

    class Meta:
        model = Administrador
        fields = ['nombres', 'apellidos', 'numero_cedula', 'numero_celular', 'correo_institucional', 'password1', 'password2']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_cedula': forms.NumberInput(attrs={'class': 'form-control'}),
            'numero_celular': forms.NumberInput(attrs={'class': 'form-control'}),
            'correo_institucional': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = [
            'nombres',
            'apellidos',
            'correo_institucional',
            'numero_celular',
            'numero_cedula'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese los nombres'
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese los apellidos'
            }),
            'correo_institucional': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@sena.edu.co'
            }),
            'numero_celular': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el número de celular'
            }),
            'numero_cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el número de cédula'
            })
        }
        error_messages = {
            'nombres': {'required': 'Este campo es obligatorio.'},
            'apellidos': {'required': 'Este campo es obligatorio.'},
            'correo_institucional': {'required': 'Este campo es obligatorio.'},
            'numero_celular': {'required': 'Este campo es obligatorio.'},
            'numero_cedula': {'required': 'Este campo es obligatorio.'},
        }
        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'correo_institucional': 'Correo Institucional',
            'numero_celular': 'Número de Celular',
            'numero_cedula': 'Número de Cédula'
        }

class ProgramaFormacionForm(forms.ModelForm):
    class Meta:
        model = ProgramaFormacion
        fields = ['codigo_programa', 'nombre_programa', 'jornada', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'codigo_programa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el código del programa'
            }),
            'nombre_programa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre del programa'
            }),
            'jornada': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'type': 'date',
                'placeholder': 'Seleccione la fecha de inicio'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'type': 'date',
                'placeholder': 'Seleccione la fecha de fin'
            })
        }
        error_messages = {
            'codigo_programa': {'required': 'Este campo es obligatorio.'},
            'nombre_programa': {'required': 'Este campo es obligatorio.'},
            'jornada': {'required': 'Este campo es obligatorio.'},
            'fecha_inicio': {'required': 'Este campo es obligatorio.'},
            'fecha_fin': {'required': 'Este campo es obligatorio.'},
        }
        labels = {
            'codigo_programa': 'Código del Programa',
            'nombre_programa': 'Nombre del Programa',
            'jornada': 'Jornada',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin'
        }

class AmbienteForm(forms.ModelForm):
    class Meta:
        model = Ambiente
        fields = ['codigo_ambiente', 'nombre_ambiente', 'sede']
        widgets = {
            'codigo_ambiente': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_ambiente': forms.TextInput(attrs={'class': 'form-control'}),
            'sede': forms.Select(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'codigo_ambiente': {'required': 'Este campo es obligatorio.'},
            'nombre_ambiente': {'required': 'Este campo es obligatorio.'},
            'sede': {'required': 'Este campo es obligatorio.'},
        }

class CompetenciaForm(forms.ModelForm):
    class Meta:
        model = Competencia
        fields = ['nombre', 'codigo_norma', 'unidad_competencia', 'duracion_estimada', 'resultado_aprendizaje']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la competencia'
            }),
            'codigo_norma': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el código de la norma'
            }),
            'unidad_competencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese la unidad de competencia'
            }),
            'duracion_estimada': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese la duración estimada en horas'
            }),
            'resultado_aprendizaje': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describa el resultado de aprendizaje',
                'rows': 4
            })
        }
        error_messages = {
            'nombre': {'required': 'Este campo es obligatorio.'},
            'codigo_norma': {'required': 'Este campo es obligatorio.'},
            'unidad_competencia': {'required': 'Este campo es obligatorio.'},
            'duracion_estimada': {'required': 'Este campo es obligatorio.'},
            'resultado_aprendizaje': {'required': 'Este campo es obligatorio.'},
        }
        labels = {
            'nombre': 'Nombre de la Competencia',
            'codigo_norma': 'Código de la Norma',
            'unidad_competencia': 'Unidad de Competencia',
            'duracion_estimada': 'Duración Estimada',
            'resultado_aprendizaje': 'Resultado de Aprendizaje'
        }

class CalendarForm(forms.ModelForm):
    DIAS_SEMANA = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miércoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sábado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]

    dias_recurrencia = forms.MultipleChoiceField(
        choices=DIAS_SEMANA,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Días de Recurrencia',
    )

    class Meta:
        model = Calendar
        fields = ['instructor', 'programa', 'ambiente', 'competencia', 'start', 'end', 'dias_recurrencia']
        widgets = {
            'instructor': forms.Select(attrs={'class': 'form-control', 'required': 'true'}),
            'programa': forms.Select(attrs={'class': 'form-control', 'required': 'true'}),
            'ambiente': forms.Select(attrs={'class': 'form-control', 'required': 'true'}),
            'competencia': forms.Select(attrs={'class': 'form-control'}),
            'start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': 'true'}),
            'end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': 'true'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['programa'].queryset = ProgramaFormacion.objects.all()
        self.fields['programa'].widget.choices = [
            (programa.pk, f"{programa.nombre_programa} (Ficha: {programa.codigo_programa})")
            for programa in self.fields['programa'].queryset
        ]
        self.fields['ambiente'].queryset = Ambiente.objects.all()
        self.fields['ambiente'].widget.choices = [
            (ambiente.pk, f"{ambiente.nombre_ambiente} (Código: {ambiente.codigo_ambiente})")
            for ambiente in self.fields['ambiente'].queryset
        ]

class CalInstForm(CalendarForm):
    class Meta(CalendarForm.Meta):
        widgets = {
            **CalendarForm.Meta.widgets,
            'instructor': forms.Select(attrs={'class': 'form-control', 'disabled': 'true', 'required': 'true'}),
        }

class CalAmbForm(CalendarForm):
    class Meta(CalendarForm.Meta):
        widgets = {
            **CalendarForm.Meta.widgets,
            'ambiente': forms.Select(attrs={'class': 'form-control', 'disabled': 'true', 'required': 'true'}),
        }

class CalPFForm(CalendarForm):
    class Meta(CalendarForm.Meta):
        widgets = {
            **CalendarForm.Meta.widgets,
            'programa': forms.Select(attrs={'class': 'form-control', 'disabled': 'true', 'required': 'true'}),
        }
        
