from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Administrador, Instructor, ProgramaFormacion, Ambiente, Competencia
from calendario.models import HorarioI, HorarioA, HorarioPF, HorarioCC
from .forms import AdministradorForm, InstructorForm, ProgramaFormacionForm, AmbienteForm, CompetenciaForm

# Vistas para Administrado
class AdministradorListView(LoginRequiredMixin, ListView):
    model = Administrador
    template_name = 'horarios/administrador_list.html'
    context_object_name = 'administradores'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AdministradorForm()
        return context

class AdministradorCreateView(LoginRequiredMixin, CreateView):
    model = Administrador
    form_class = AdministradorForm
    template_name = 'horarios/administrador_form.html'
    success_url = reverse_lazy('administrador_list')


class AdministradorUpdateView(LoginRequiredMixin, UpdateView):
    model = Administrador
    form_class = AdministradorForm
    template_name = 'horarios/administrador_form.html'
    success_url = reverse_lazy('administrador_list')


class AdministradorDeleteView(LoginRequiredMixin, DeleteView):
    model = Administrador
    template_name = 'horarios/administrador_confirm_delete.html'
    success_url = reverse_lazy('administrador_list')


# Vistas para Instructor
class InstructorListView(LoginRequiredMixin, ListView):
    model = Instructor
    template_name = 'horarios/instructor_list.html'
    context_object_name = 'instructores'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = InstructorForm()
        return context

class InstructorCreateView(LoginRequiredMixin, CreateView):
    model = Instructor
    form_class = InstructorForm
    template_name = 'horarios/instructor_form.html'
    success_url = reverse_lazy('instructor_list')

class InstructorUpdateView(LoginRequiredMixin, UpdateView):
    model = Instructor
    form_class = InstructorForm
    template_name = 'horarios/instructor_form.html'
    success_url = reverse_lazy('instructor_list')

class InstructorDeleteView(LoginRequiredMixin, DeleteView):
    model = Instructor
    template_name = 'horarios/instructor_confirm_delete.html'
    success_url = reverse_lazy('instructor_list')

# Vistas para ProgramaFormacion
class ProgramaFormacionListView(LoginRequiredMixin, ListView):
    model = ProgramaFormacion
    template_name = 'horarios/programa_formacion_list.html'
    context_object_name = 'programas'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProgramaFormacionForm()
        return context

class ProgramaFormacionCreateView(LoginRequiredMixin, CreateView):
    model = ProgramaFormacion
    form_class = ProgramaFormacionForm
    template_name = 'horarios/programa_formacion_form.html'
    success_url = reverse_lazy('programa_formacion_list')

class ProgramaFormacionUpdateView(LoginRequiredMixin, UpdateView):
    model = ProgramaFormacion
    form_class = ProgramaFormacionForm
    template_name = 'horarios/programa_formacion_form.html'
    success_url = reverse_lazy('programa_formacion_list')

class ProgramaFormacionDeleteView(LoginRequiredMixin, DeleteView):
    model = ProgramaFormacion
    template_name = 'horarios/programa_formacion_confirm_delete.html'
    success_url = reverse_lazy('programa_formacion_list')

# Vistas para Ambiente
class AmbienteListView(LoginRequiredMixin, ListView):
    model = Ambiente
    template_name = 'horarios/ambiente_list.html'
    context_object_name = 'ambientes'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AmbienteForm()
        return context

class AmbienteCreateView(LoginRequiredMixin, CreateView):
    model = Ambiente
    form_class = AmbienteForm
    template_name = 'horarios/ambiente_form.html'
    success_url = reverse_lazy('ambiente_list')

class AmbienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Ambiente
    form_class = AmbienteForm
    template_name = 'horarios/ambiente_form.html'
    success_url = reverse_lazy('ambiente_list')

class AmbienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Ambiente
    template_name = 'horarios/ambiente_confirm_delete.html'
    success_url = reverse_lazy('ambiente_list')

# Vistas para Competencia
class CompetenciaListView(LoginRequiredMixin, ListView):
    model = Competencia
    template_name = 'horarios/competencia_list.html'
    context_object_name = 'competencias'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CompetenciaForm()
        return context

class CompetenciaCreateView(LoginRequiredMixin, CreateView):
    model = Competencia
    form_class = CompetenciaForm
    template_name = 'horarios/competencia_form.html'
    success_url = reverse_lazy('competencia_list')

class CompetenciaUpdateView(LoginRequiredMixin, UpdateView):
    model = Competencia
    form_class = CompetenciaForm
    template_name = 'horarios/competencia_form.html'
    success_url = reverse_lazy('competencia_list')

class CompetenciaDeleteView(LoginRequiredMixin, DeleteView):
    model = Competencia
    template_name = 'horarios/competencia_confirm_delete.html'
    success_url = reverse_lazy('competencia_list')

# Vista para el Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            error_message = "Credenciales inválidas o usuario no es administrador."
            return render(request, 'horarios/login.html', {'error_message': error_message})
    return render(request, 'horarios/login.html')

@login_required
def admin_dashboard(request):
    return render(request, 'horarios/admin_dashboard.html')
