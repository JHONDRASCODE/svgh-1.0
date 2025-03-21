

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.http import JsonResponse, FileResponse, HttpResponseRedirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta
import pandas as pd
import os
import csv
import json

from .models import Administrador, Instructor, ProgramaFormacion, Ambiente, Competencia, ActividadSistema
from calendarios.models import Calendar
from .forms import AdministradorForm, InstructorForm, ProgramaFormacionForm, AmbienteForm, CompetenciaForm, CalInstForm, CalAmbForm, CalPFForm, CalendarForm
from .utils import create_instructor_template


def manual_view(request):
    return render(request, 'horarios/manual.html')


def registrar_actividad(usuario, tipo, accion, descripcion, elemento_id=None, elemento_nombre=""):
    """
    Registra una actividad del sistema.
    
    Args:
        usuario: Usuario que realiza la acción
        tipo: Tipo de elemento ('instructor', 'competencia', 'programa', 'ambiente', 'horario')
        accion: Acción realizada ('crear', 'editar', 'eliminar', 'generar')
        descripcion: Descripción de la actividad
        elemento_id: ID del elemento afectado (opcional)
        elemento_nombre: Nombre del elemento afectado (opcional)
    
    Returns:
        bool: True si se registró correctamente, False en caso contrario
    """
    try:
        # Validar valores de tipo
        tipos_validos = ['instructor', 'competencia', 'programa', 'ambiente', 'horario']
        if tipo.lower() not in tipos_validos:
            tipo = 'instructor'  # Valor por defecto
        
        # Validar valores de acción
        acciones_validas = ['crear', 'editar', 'eliminar', 'generar']
        if accion.lower() not in acciones_validas:
            accion = 'crear'  # Valor por defecto
        
        # Crear el registro de actividad CON el campo leido (importante)
        actividad = ActividadSistema.objects.create(
            usuario=usuario,
            tipo=tipo.lower(),
            accion=accion.lower(),
            descripcion=descripcion,
            elemento_id=elemento_id,
            elemento_nombre=elemento_nombre,
            leido=False  # Establecer explícitamente como no leída
        )
        
        print(f"✅ Actividad registrada: {actividad}")
        return True
    except Exception as e:
        print(f"❌ Error al registrar actividad: {str(e)}")
        return False


def calcular_tiempo_transcurrido(fecha_hora):
    """
    Calcula el tiempo transcurrido en formato legible (hace X minutos, horas, etc.)
    """
    ahora = timezone.now()
    diferencia = ahora - fecha_hora
    
    if diferencia < timedelta(minutes=1):
        return "Hace un momento"
    elif diferencia < timedelta(hours=1):
        minutos = int(diferencia.total_seconds() / 60)
        return f"Hace {minutos} {'minuto' if minutos == 1 else 'minutos'}"
    elif diferencia < timedelta(days=1):
        horas = int(diferencia.total_seconds() / 3600)
        return f"Hace {horas} {'hora' if horas == 1 else 'horas'}"
    elif diferencia < timedelta(days=7):
        dias = diferencia.days
        return f"Hace {dias} {'día' if dias == 1 else 'días'}"
    else:
        return fecha_hora.strftime('%d/%m/%Y')
    
    
@login_required
def notification_panel(request):
    """Vista dedicada para el panel de notificaciones que se cargará en un iframe"""
    return render(request, 'horarios/notification_panel.html')


# Vistas para el sistema de notificaciones
@login_required
def obtener_notificaciones(request):
    """
    Vista mejorada para obtener las notificaciones recientes en formato JSON
    con mejor manejo de errores y mensajes de depuración
    """
    try:
        print("📢 Ejecutando obtener_notificaciones")
        
        # Obtener las 10 notificaciones más recientes
        notificaciones = ActividadSistema.objects.all().order_by('-fecha_hora')[:10]
        print(f"📢 Se encontraron {notificaciones.count() if hasattr(notificaciones, 'count') else len(notificaciones)} notificaciones")
        
        # Contar notificaciones no leídas
        try:
            # Primero intentamos usar el manager personalizado
            try:
                no_leidas = ActividadSistema.objects.get_no_leidas_count()
                print(f"📢 Conteo con manager personalizado: {no_leidas} no leídas")
            except:
                # Si falla, usamos el filtro directo
                no_leidas = ActividadSistema.objects.filter(leido=False).count()
                print(f"📢 Conteo con filtro directo: {no_leidas} no leídas")
        except Exception as e:
            # Si hay error con el campo leido, contamos todas como no leídas
            print(f"❌ Error al contar no leídas: {str(e)}")
            no_leidas = len(notificaciones)
            print(f"📢 Contando todas ({no_leidas}) como no leídas")
        
        # Formatear las notificaciones para JSON
        notificaciones_formateadas = []
        for notif in notificaciones:
            try:
                # Determinar el icono según el tipo de elemento
                icono = "bi-clock-history"  # Icono predeterminado
                
                try:
                    # Primero intentamos usar el método del modelo
                    icono = notif.obtener_icono()
                    print(f"📢 Icono obtenido de método: {icono}")
                except:
                    # Si falla, usamos la lógica original
                    if notif.tipo == 'instructor':
                        icono = "bi-person-fill"
                    elif notif.tipo == 'programa':
                        icono = "bi-folder-fill"
                    elif notif.tipo == 'competencia':
                        icono = "bi-journal-fill"
                    elif notif.tipo == 'ambiente':
                        icono = "bi-building"
                    elif notif.tipo == 'horario':
                        icono = "bi-calendar-week"
                    print(f"📢 Icono determinado manualmente: {icono}")
                    
                # Determinar la URL de destino según el tipo y la acción
                url_destino = reverse('admin_dashboard')  # URL por defecto
                
                if notif.elemento_id:
                    try:
                        if notif.tipo == 'instructor':
                            url_destino = reverse('instructor_edit', args=[notif.elemento_id])
                        elif notif.tipo == 'programa':
                            url_destino = reverse('programa_formacion_edit', args=[notif.elemento_id])
                        elif notif.tipo == 'competencia':
                            url_destino = reverse('competencia_edit', args=[notif.elemento_id])
                        elif notif.tipo == 'ambiente':
                            url_destino = reverse('ambiente_edit', args=[notif.elemento_id])
                        elif notif.tipo == 'horario':
                            url_destino = reverse('calendar_edit', args=[notif.elemento_id])
                    except Exception as e:
                        print(f"❌ Error al determinar URL para {notif.tipo} id={notif.elemento_id}: {str(e)}")
                        # Mantenemos la URL por defecto
                
                # Verificar si tiene el atributo leido, si no, asumimos false
                try:
                    leido = notif.leido
                except Exception as e:
                    print(f"❌ Error al acceder a 'leido': {str(e)}")
                    leido = False
                
                # Obtener el tiempo transcurrido
                try:
                    # Primero intentamos usar el método del modelo
                    tiempo = notif.tiempo_transcurrido()
                    print(f"📢 Tiempo calculado por método: {tiempo}")
                except:
                    # Si falla, usamos la función original
                    tiempo = calcular_tiempo_transcurrido(notif.fecha_hora)
                    print(f"📢 Tiempo calculado manualmente: {tiempo}")
                    
                # Formatear para el front-end
                notificaciones_formateadas.append({
                    'id': notif.id,
                    'descripcion': notif.descripcion,
                    'usuario': notif.usuario.nombre_completo(),
                    'fecha_hora': notif.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                    'tiempo_transcurrido': tiempo,
                    'icono': icono,
                    'leido': leido,
                    'tipo': notif.tipo,
                    'accion': notif.accion,
                    'url': url_destino
                })
                print(f"📢 Notificación formateada ID {notif.id}: {notif.descripcion[:30]}...")
            except Exception as e:
                print(f"❌ Error al formatear notificación {notif.id}: {str(e)}")
                # Omitimos esta notificación
        
        print(f"📢 Total de notificaciones formateadas: {len(notificaciones_formateadas)}")
        return JsonResponse({
            'notificaciones': notificaciones_formateadas,
            'no_leidas': no_leidas
        })
    except Exception as e:
        print(f"❌ Error general al obtener notificaciones: {str(e)}")
        return JsonResponse({
            'notificaciones': [],
            'no_leidas': 0,
            'error': str(e)
        }, status=200)  # Devolvemos 200 en lugar de 500 para manejar el error en el cliente


@login_required
@require_POST
def marcar_notificacion_leida(request, notificacion_id):
    """
    Vista para marcar una notificación como leída
    """
    try:
        print(f"📢 Intentando marcar como leída la notificación {notificacion_id}")
        # Verificar que la notificación exista e intentar marcarla como leída
        notificacion = ActividadSistema.objects.get(id=notificacion_id)
        try:
            # Intentar usar el método del modelo
            try:
                exito = notificacion.marcar_como_leida()
                print(f"📢 Notificación marcada como leída usando método del modelo: {exito}")
            except:
                # Si falla, usar el enfoque directo
                notificacion.leido = True
                notificacion.save(update_fields=['leido'])
                print(f"📢 Notificación marcada como leída usando enfoque directo")
        except Exception as e:
            # Si hay un error con el campo leido, registramos el error pero devolvemos éxito
            print(f"⚠️ Error al marcar como leída: {str(e)}")
        
        return JsonResponse({'success': True})
    except ActividadSistema.DoesNotExist:
        print(f"❌ Notificación {notificacion_id} no encontrada")
        return JsonResponse({'success': False, 'error': 'Notificación no encontrada'}, status=404)
    except Exception as e:
        print(f"❌ Error al marcar notificación como leída: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def marcar_todas_leidas(request):
    """
    Vista para marcar todas las notificaciones como leídas
    """
    try:
        print(f"📢 Intentando marcar todas las notificaciones como leídas")
        # Marcar todas las notificaciones como leídas
        try:
            # Intentar usar el método del manager
            try:
                ActividadSistema.objects.marcar_todas_como_leidas()
                print(f"📢 Todas las notificaciones marcadas como leídas usando método del manager")
            except:
                # Si falla, usar el enfoque directo
                count = ActividadSistema.objects.filter(leido=False).update(leido=True)
                print(f"📢 {count} notificaciones marcadas como leídas usando enfoque directo")
        except Exception as e:
            # Si hay un error con el campo leido, registramos el error pero devolvemos éxito
            print(f"⚠️ Error al marcar todas como leídas: {str(e)}")
        
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"❌ Error al marcar todas como leídas: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def eliminar_todas_notificaciones(request):
    """
    Vista para eliminar todas las notificaciones
    """
    try:
        print(f"📢 Intentando eliminar todas las notificaciones")
        # Obtener conteo antes de eliminar para el log
        count = ActividadSistema.objects.count()
        
        # Eliminar todas las notificaciones
        ActividadSistema.objects.all().delete()
        
        print(f"📢 Se eliminaron {count} notificaciones")
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"❌ Error al eliminar notificaciones: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Vistas para gestionar el cambio de contraseña con "Volver"
def set_password_change_return(request):
    """
    Guarda la URL actual en la sesión y redirige a la vista de cambio de contraseña.
    Permite que el botón "Volver" regrese a la página desde donde se solicitó el cambio.
    """
    # Guardar la URL de referencia o la URL actual en la sesión
    referer = request.META.get('HTTP_REFERER')
    
    # Si no hay referencia, usar el dashboard como valor predeterminado
    if not referer:
        request.session['password_change_return_url'] = reverse('admin_dashboard')
    else:
        request.session['password_change_return_url'] = referer
    
    return redirect('password_change')


class CustomPasswordChangeView(PasswordChangeView):
    """
    Vista personalizada para cambio de contraseña que incluye la URL de retorno
    para el botón "Volver".
    """
    template_name = 'horarios/password_change.html'  
    success_url = reverse_lazy('password_change_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener la URL guardada, o usar una URL predeterminada
        return_url = self.request.session.get('password_change_return_url')
        if not return_url:
            return_url = reverse('admin_dashboard')
        context['return_url'] = return_url
        return context


# Vistas para Administrador
class AdministradorListView(LoginRequiredMixin, ListView):
    model = Administrador
    template_name = 'horarios/administradores/administrador_list.html'
    context_object_name = 'administradores'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AdministradorForm()
        return context


class AdministradorCreateView(LoginRequiredMixin, CreateView):
    model = Administrador
    form_class = AdministradorForm
    template_name = 'horarios/administradores/administrador_form.html'
    success_url = reverse_lazy('administrador_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        administrador = self.object
        
        # No registramos la actividad para administradores para evitar mostrarlos en el dashboard
        messages.success(self.request, f'¡Éxito! El administrador {administrador.nombres} {administrador.apellidos} ha sido creado correctamente.')
        return response


class AdministradorUpdateView(LoginRequiredMixin, UpdateView):
    model = Administrador
    form_class = AdministradorForm
    template_name = 'horarios/administradores/administrador_form.html'
    success_url = reverse_lazy('administrador_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        administrador = self.object
        
        # No registramos la actividad para administradores para evitar mostrarlos en el dashboard
        messages.success(self.request, f'¡Éxito! El administrador {administrador.nombres} {administrador.apellidos} ha sido actualizado correctamente.')
        return response


class AdministradorDeleteView(LoginRequiredMixin, DeleteView):
    model = Administrador
    template_name = 'horarios/administradores/administrador_confirm_delete.html'
    success_url = reverse_lazy('administrador_list')

    def delete(self, request, *args, **kwargs):
        administrador = self.get_object()
        nombre_completo = f"{administrador.nombres} {administrador.apellidos}"
        
        response = super().delete(request, *args, **kwargs)
        
        # No registramos la actividad para administradores para evitar mostrarlos en el dashboard
        messages.success(self.request, f'¡Éxito! El administrador {nombre_completo} ha sido eliminado correctamente.')
        return response
    
    # Método POST para soportar solicitudes AJAX
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                administrador = self.get_object()
                nombre_completo = f"{administrador.nombres} {administrador.apellidos}"
                
                administrador.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': f'El administrador {nombre_completo} ha sido eliminado correctamente.',
                    'redirect': self.success_url
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
        else:
            return super().post(request, *args, **kwargs)


# Vistas para Instructor
class InstructorListView(LoginRequiredMixin, ListView):
    model = Instructor
    template_name = 'horarios/instructores/instructor_list.html'
    context_object_name = 'object_list'
    paginate_by = 10  # Limitar a 10 registros por página

    def get_queryset(self):
        queryset = Instructor.objects.all()
        search_query = self.request.GET.get('search', '').strip()

        if search_query:
            queryset = queryset.filter(
                Q(nombres__icontains=search_query) |
                Q(apellidos__icontains=search_query) |
                Q(correo_institucional__icontains=search_query) |
                Q(numero_celular__icontains=search_query) |
                Q(numero_cedula__icontains=search_query)
            ).distinct()

        return queryset.order_by('nombres', 'apellidos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        
        # Información adicional para el paginador
        if context['page_obj'].has_other_pages():
            context['paginator_range'] = self.get_paginator_range(context['page_obj'])
            
        return context
    
    def get_paginator_range(self, page_obj):
        """
        Método para obtener un rango de páginas personalizado alrededor de la página actual
        para evitar mostrar demasiadas páginas en el paginador.
        """
        paginator = page_obj.paginator
        current_page = page_obj.number
        
        # Número de páginas a mostrar antes y después de la página actual
        show_adjacent = 2
        
        # Determinar el rango de páginas a mostrar
        start_page = max(current_page - show_adjacent, 1)
        end_page = min(current_page + show_adjacent, paginator.num_pages)
        
        return range(start_page, end_page + 1)


class InstructorCreateView(LoginRequiredMixin, CreateView):
    model = Instructor
    form_class = InstructorForm
    template_name = 'horarios/instructores/instructor_form.html'
    success_url = reverse_lazy('instructor_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        instructor = self.object
        
        # Registrar la actividad de creación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='instructor',
            accion='crear',
            descripcion=f'Se creó el instructor {instructor.nombres} {instructor.apellidos}',
            elemento_id=instructor.id,
            elemento_nombre=f'{instructor.nombres} {instructor.apellidos}'
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El instructor {instructor.nombres} {instructor.apellidos} ha sido creado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El instructor {instructor.nombres} {instructor.apellidos} ha sido creado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear el instructor. Por favor, verifica los datos.')
        return super().form_invalid(form)


class InstructorUpdateView(LoginRequiredMixin, UpdateView):
    model = Instructor
    form_class = InstructorForm
    template_name = 'horarios/instructores/instructor_form.html'
    success_url = reverse_lazy('instructor_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        instructor = self.object
        
        # Registrar la actividad de actualización con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='instructor',
            accion='editar',
            descripcion=f'Se actualizó el instructor {instructor.nombres} {instructor.apellidos}',
            elemento_id=instructor.id,
            elemento_nombre=f'{instructor.nombres} {instructor.apellidos}'
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El instructor {instructor.nombres} {instructor.apellidos} ha sido actualizado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El instructor {instructor.nombres} {instructor.apellidos} ha sido actualizado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class InstructorDeleteView(LoginRequiredMixin, DeleteView):
    model = Instructor
    template_name = 'horarios/instructores/instructor_confirm_delete.html'
    success_url = reverse_lazy('instructor_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            instructor = self.get_object()
            nombre_completo = f"{instructor.nombres} {instructor.apellidos}"
            id_temp = instructor.id
            
            instructor.delete()
            
            # Registrar la actividad de eliminación con la versión mejorada
            exito = registrar_actividad(
                usuario=self.request.user,
                tipo='instructor',
                accion='eliminar',
                descripcion=f'Se eliminó el instructor {nombre_completo}',
                elemento_id=id_temp,
                elemento_nombre=nombre_completo
            )
            
            if exito:
                messages.success(self.request, f'¡Éxito! El instructor {nombre_completo} ha sido eliminado correctamente.')
            else:
                messages.warning(self.request, f'El instructor {nombre_completo} ha sido eliminado, pero hubo un problema al registrar la actividad.')
                
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            messages.error(self.request, 'No se pudo eliminar el instructor. Puede que tenga registros asociados.')
            return HttpResponseRedirect(self.success_url)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
        
    # Soporte para AJAX
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                instructor = self.get_object()
                nombre_completo = f"{instructor.nombres} {instructor.apellidos}"
                id_temp = instructor.id
                
                instructor.delete()
                
                # Registrar la actividad de eliminación
                exito = registrar_actividad(
                    usuario=request.user,
                    tipo='instructor',
                    accion='eliminar',
                    descripcion=f'Se eliminó el instructor {nombre_completo}',
                    elemento_id=id_temp,
                    elemento_nombre=nombre_completo
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'El instructor {nombre_completo} ha sido eliminado correctamente.',
                    'reload': True
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'No se pudo eliminar el instructor: {str(e)}'
                }, status=400)
        else:
            return self.delete(request, *args, **kwargs)


# Vistas para ProgramaFormacion
class ProgramaFormacionListView(LoginRequiredMixin, ListView):
    model = ProgramaFormacion
    template_name = 'horarios/programasformacion/programa_formacion_list.html'
    context_object_name = 'programas'

    def get_queryset(self):
        queryset = super().get_queryset()
        nombre_programa = self.request.GET.get('nombre_programa', None)
        jornada = self.request.GET.get('jornada', None)
        search_query = self.request.GET.get('search', '').strip()

        if nombre_programa:
            queryset = queryset.filter(nombre_programa__icontains=nombre_programa)
        if jornada:
            queryset = queryset.filter(jornada__icontains=jornada)
        if search_query:
            queryset = queryset.filter(
                Q(nombre_programa__icontains=search_query) |
                Q(codigo_programa__icontains=search_query)
            )

        return queryset.order_by('codigo_programa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_jornada'] = self.request.GET.get('jornada', '')
        return context


class ProgramaFormacionCreateView(LoginRequiredMixin, CreateView):
    model = ProgramaFormacion
    form_class = ProgramaFormacionForm
    template_name = 'horarios/programasformacion/programa_formacion_form.html'
    success_url = reverse_lazy('programa_formacion_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        programa = self.object
        
        # Registrar la actividad de creación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='programa',
            accion='crear',
            descripcion=f'Se creó el programa de formación {programa.nombre_programa}',
            elemento_id=programa.id,
            elemento_nombre=programa.nombre_programa
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El programa {programa.nombre_programa} ha sido creado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El programa {programa.nombre_programa} ha sido creado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class ProgramaFormacionUpdateView(LoginRequiredMixin, UpdateView):
    model = ProgramaFormacion
    form_class = ProgramaFormacionForm
    template_name = 'horarios/programasformacion/programa_formacion_form.html'
    success_url = reverse_lazy('programa_formacion_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        programa = self.object
        
        # Registrar la actividad de actualización con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='programa',
            accion='editar',
            descripcion=f'Se actualizó el programa de formación {programa.nombre_programa}',
            elemento_id=programa.id,
            elemento_nombre=programa.nombre_programa
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El programa {programa.nombre_programa} ha sido actualizado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El programa {programa.nombre_programa} ha sido actualizado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class ProgramaFormacionDeleteView(LoginRequiredMixin, DeleteView):
    model = ProgramaFormacion
    template_name = 'horarios/programasformacion/programa_formacion_confirm_delete.html'
    success_url = reverse_lazy('programa_formacion_list')
    
    def delete(self, request, *args, **kwargs):
        programa = self.get_object()
        nombre = programa.nombre_programa
        id_temp = programa.id
        
        response = super().delete(request, *args, **kwargs)
        
        # Registrar la actividad de eliminación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='programa',
            accion='eliminar',
            descripcion=f'Se eliminó el programa de formación {nombre}',
            elemento_id=id_temp,
            elemento_nombre=nombre
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El programa {nombre} ha sido eliminado correctamente.')
        else:
            messages.warning(self.request, f'El programa {nombre} ha sido eliminado, pero hubo un problema al registrar la actividad.')
        
        return response
    
    # Soporte para AJAX
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                programa = self.get_object()
                nombre = programa.nombre_programa
                id_temp = programa.id
                
                programa.delete()
                
                # Registrar la actividad de eliminación
                exito = registrar_actividad(
                    usuario=request.user,
                    tipo='programa',
                    accion='eliminar',
                    descripcion=f'Se eliminó el programa de formación {nombre}',
                    elemento_id=id_temp,
                    elemento_nombre=nombre
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'El programa {nombre} ha sido eliminado correctamente.',
                    'reload': True
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'No se pudo eliminar el programa: {str(e)}'
                }, status=400)
        else:
            return super().post(request, *args, **kwargs)


# Vistas para Ambiente
class AmbienteListView(LoginRequiredMixin, ListView):
    model = Ambiente
    template_name = 'horarios/ambientes/ambiente_list.html'
    context_object_name = 'ambientes'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        sede = self.request.GET.get('sede')

        if query:
            queryset = queryset.filter(
                Q(codigo_ambiente__icontains=query) |
                Q(nombre_ambiente__icontains=query)
            )

        if sede:
            queryset = queryset.filter(sede=sede)

        return queryset.order_by('codigo_ambiente')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_sede'] = self.request.GET.get('sede', '')
        return context


class AmbienteCreateView(LoginRequiredMixin, CreateView):
    model = Ambiente
    form_class = AmbienteForm
    template_name = 'horarios/ambientes/ambiente_form.html'
    success_url = reverse_lazy('ambiente_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        ambiente = self.object
        
        # Registrar la actividad de creación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='ambiente',
            accion='crear',
            descripcion=f'Se creó el ambiente {ambiente.nombre_ambiente}',
            elemento_id=ambiente.id,
            elemento_nombre=ambiente.nombre_ambiente
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El ambiente {ambiente.nombre_ambiente} ha sido creado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El ambiente {ambiente.nombre_ambiente} ha sido creado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class AmbienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Ambiente
    form_class = AmbienteForm
    template_name = 'horarios/ambientes/ambiente_form.html'
    success_url = reverse_lazy('ambiente_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        ambiente = self.object
        
        # Registrar la actividad de actualización con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='ambiente',
            accion='editar',
            descripcion=f'Se actualizó el ambiente {ambiente.nombre_ambiente}',
            elemento_id=ambiente.id,
            elemento_nombre=ambiente.nombre_ambiente
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El ambiente {ambiente.nombre_ambiente} ha sido actualizado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El ambiente {ambiente.nombre_ambiente} ha sido actualizado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class AmbienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Ambiente
    template_name = 'horarios/ambientes/ambiente_confirm_delete.html'
    success_url = reverse_lazy('ambiente_list')
    
    def delete(self, request, *args, **kwargs):
        ambiente = self.get_object()
        nombre = ambiente.nombre_ambiente
        id_temp = ambiente.id
        
        response = super().delete(request, *args, **kwargs)
        
        # Registrar la actividad de eliminación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='ambiente',
            accion='eliminar',
            descripcion=f'Se eliminó el ambiente {nombre}',
            elemento_id=id_temp,
            elemento_nombre=nombre
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El ambiente {nombre} ha sido eliminado correctamente.')
        else:
            messages.warning(self.request, f'El ambiente {nombre} ha sido eliminado, pero hubo un problema al registrar la actividad.')
        
        return response
    
    # Soporte para AJAX
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                ambiente = self.get_object()
                nombre = ambiente.nombre_ambiente
                id_temp = ambiente.id
                
                ambiente.delete()
                
                # Registrar la actividad de eliminación
                exito = registrar_actividad(
                    usuario=request.user,
                    tipo='ambiente',
                    accion='eliminar',
                    descripcion=f'Se eliminó el ambiente {nombre}',
                    elemento_id=id_temp,
                    elemento_nombre=nombre
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'El ambiente {nombre} ha sido eliminado correctamente.',
                    'reload': True
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'No se pudo eliminar el ambiente: {str(e)}'
                }, status=400)
        else:
            return super().post(request, *args, **kwargs)


# Vistas para Competencia
class CompetenciaListView(LoginRequiredMixin, ListView):
    model = Competencia
    template_name = 'horarios/competencias/competencia_list.html'
    context_object_name = 'competencias'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        # Filtrar por código de norma si se ingresó un valor
        if query:
            queryset = queryset.filter(codigo_norma__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CompetenciaForm()
        return context


class CompetenciaCreateView(LoginRequiredMixin, CreateView):
    model = Competencia
    form_class = CompetenciaForm
    template_name = 'horarios/competencias/competencia_form.html'
    success_url = reverse_lazy('competencia_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        competencia = self.object
        
        # Registrar la actividad de creación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='competencia',
            accion='crear',
            descripcion=f'Se creó la competencia {competencia.nombre}',
            elemento_id=competencia.id,
            elemento_nombre=competencia.nombre
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! La competencia {competencia.nombre} ha sido creada correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! La competencia {competencia.nombre} ha sido creada correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CompetenciaUpdateView(LoginRequiredMixin, UpdateView):
    model = Competencia
    form_class = CompetenciaForm
    template_name = 'horarios/competencias/competencia_form.html'
    success_url = reverse_lazy('competencia_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        competencia = self.object
        
        # Registrar la actividad de actualización con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='competencia',
            accion='editar',
            descripcion=f'Se actualizó la competencia {competencia.nombre}',
            elemento_id=competencia.id,
            elemento_nombre=competencia.nombre
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! La competencia {competencia.nombre} ha sido actualizada correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! La competencia {competencia.nombre} ha sido actualizada correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CompetenciaDeleteView(LoginRequiredMixin, DeleteView):
    model = Competencia
    template_name = 'horarios/competencias/competencia_confirm_delete.html'
    success_url = reverse_lazy('competencia_list')
    
    def delete(self, request, *args, **kwargs):
        competencia = self.get_object()
        nombre = competencia.nombre
        id_temp = competencia.id
        
        response = super().delete(request, *args, **kwargs)
        
        # Registrar la actividad de eliminación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='competencia',
            accion='eliminar',
            descripcion=f'Se eliminó la competencia {nombre}',
            elemento_id=id_temp,
            elemento_nombre=nombre
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! La competencia {nombre} ha sido eliminada correctamente.')
        else:
            messages.warning(self.request, f'La competencia {nombre} ha sido eliminada, pero hubo un problema al registrar la actividad.')
        
        return response
    
    # Soporte para AJAX
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                competencia = self.get_object()
                nombre = competencia.nombre
                id_temp = competencia.id
                
                competencia.delete()
                
                # Registrar la actividad de eliminación
                exito = registrar_actividad(
                    usuario=request.user,
                    tipo='competencia',
                    accion='eliminar',
                    descripcion=f'Se eliminó la competencia {nombre}',
                    elemento_id=id_temp,
                    elemento_nombre=nombre
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'La competencia {nombre} ha sido eliminada correctamente.',
                    'reload': True
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'No se pudo eliminar la competencia: {str(e)}'
                }, status=400)
        else:
            return super().post(request, *args, **kwargs)


# VISTAS PARA LOS CALENDARIOS
# Vistas para crear calendarios desde cero
class CalendarListView(LoginRequiredMixin, ListView):
    model = Calendar
    template_name = 'horarios/calendar/calendar_list.html'
    context_object_name = 'calendar'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CalendarForm()
        return context


class CalendarCreateView(LoginRequiredMixin, CreateView):
    model = Calendar
    form_class = CalendarForm
    template_name = 'horarios/calendar/calendar_form.html'
    success_url = reverse_lazy('calendar_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        calendario = self.object
        
        # Obtener el nombre del calendario usando el atributo correcto
        # Determinar el nombre del campo según el modelo Calendar
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
            
        # Registrar la actividad de creación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='crear',
            descripcion=f'Se creó el calendario {nombre_calendario}',
            elemento_id=calendario.id,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario {nombre_calendario} ha sido creado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El calendario {nombre_calendario} ha sido creado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CalendarUpdateView(LoginRequiredMixin, UpdateView):
    model = Calendar
    form_class = CalendarForm
    template_name = 'horarios/calendar/calendar_form.html'
    success_url = reverse_lazy('calendar_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        calendario = self.object
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
        
        # Registrar la actividad de actualización con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='editar',
            descripcion=f'Se actualizó el calendario {nombre_calendario}',
            elemento_id=calendario.id,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario {nombre_calendario} ha sido actualizado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El calendario {nombre_calendario} ha sido actualizado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CalendarDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    template_name = 'horarios/calendar/calendar_confirm_delete.html'
    success_url = reverse_lazy('calendar_list')
    
    def delete(self, request, *args, **kwargs):
        calendario = self.get_object()
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
            
        id_temp = calendario.id
        
        response = super().delete(request, *args, **kwargs)
        
        # Registrar la actividad de eliminación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='eliminar',
            descripcion=f'Se eliminó el calendario {nombre_calendario}',
            elemento_id=id_temp,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario {nombre_calendario} ha sido eliminado correctamente.')
        else:
            messages.warning(self.request, f'El calendario {nombre_calendario} ha sido eliminado, pero hubo un problema al registrar la actividad.')
        
        return response
    
    # Soporte para AJAX
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                calendario = self.get_object()
                
                # Obtener el nombre del calendario
                nombre_calendario = getattr(calendario, 'title', None)
                
                if nombre_calendario is None:
                    posibles_campos = ['name', 'nombre', 'title', 'title']
                    for campo in posibles_campos:
                        if hasattr(calendario, campo):
                            nombre_calendario = getattr(calendario, campo)
                            break
                
                if nombre_calendario is None:
                    nombre_calendario = f'Calendario ID:{calendario.id}'
                    
                id_temp = calendario.id
                
                calendario.delete()
                
                # Registrar la actividad de eliminación
                exito = registrar_actividad(
                    usuario=request.user,
                    tipo='horario',
                    accion='eliminar',
                    descripcion=f'Se eliminó el calendario {nombre_calendario}',
                    elemento_id=id_temp,
                    elemento_nombre=nombre_calendario
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'El calendario {nombre_calendario} ha sido eliminado correctamente.',
                    'reload': True
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'No se pudo eliminar el calendario: {str(e)}'
                }, status=400)
        else:
            return super().post(request, *args, **kwargs)


# Vistas para el calendario de los instructores
class CalInstListView(LoginRequiredMixin, ListView):
    model = Calendar
    template_name = 'horarios/calinst/calinst_list.html'
    context_object_name = 'calinsts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CalInstForm()
        return context


class CalInstCreateView(LoginRequiredMixin, CreateView):
    model = Calendar
    form_class = CalInstForm
    template_name = 'horarios/calinst/calinst_form.html'
    success_url = reverse_lazy('calinst_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        calendario = self.object
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
        
        # Registrar la actividad de creación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='crear',
            descripcion=f'Se creó el calendario para instructor: {nombre_calendario}',
            elemento_id=calendario.id,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario para instructor {nombre_calendario} ha sido creado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El calendario para instructor {nombre_calendario} ha sido creado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CalInstUpdateView(LoginRequiredMixin, UpdateView):
    model = Calendar
    form_class = CalInstForm
    template_name = 'horarios/calinst/calinst_form.html'
    success_url = reverse_lazy('calinst_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        calendario = self.object
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
        
        # Registrar la actividad de actualización con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='editar',
            descripcion=f'Se actualizó el calendario para instructor: {nombre_calendario}',
            elemento_id=calendario.id,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario para instructor {nombre_calendario} ha sido actualizado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El calendario para instructor {nombre_calendario} ha sido actualizado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CalInstDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    template_name = 'horarios/calinst/calinst_confirm_delete.html'
    success_url = reverse_lazy('calinst_list')
    
    def delete(self, request, *args, **kwargs):
        calendario = self.get_object()
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
            
        id_temp = calendario.id
        
        response = super().delete(request, *args, **kwargs)
        
        # Registrar la actividad de eliminación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='eliminar',
            descripcion=f'Se eliminó el calendario para instructor: {nombre_calendario}',
            elemento_id=id_temp,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario para instructor {nombre_calendario} ha sido eliminado correctamente.')
        else:
            messages.warning(self.request, f'El calendario para instructor {nombre_calendario} ha sido eliminado, pero hubo un problema al registrar la actividad.')
        
        return response
    
    # Soporte para AJAX
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                calendario = self.get_object()
                
                # Obtener el nombre del calendario
                nombre_calendario = getattr(calendario, 'title', None)
                
                if nombre_calendario is None:
                    posibles_campos = ['name', 'nombre', 'title', 'title']
                    for campo in posibles_campos:
                        if hasattr(calendario, campo):
                            nombre_calendario = getattr(calendario, campo)
                            break
                
                if nombre_calendario is None:
                    nombre_calendario = f'Calendario ID:{calendario.id}'
                    
                id_temp = calendario.id
                
                calendario.delete()
                
                # Registrar la actividad de eliminación
                exito = registrar_actividad(
                    usuario=request.user,
                    tipo='horario',
                    accion='eliminar',
                    descripcion=f'Se eliminó el calendario para instructor: {nombre_calendario}',
                    elemento_id=id_temp,
                    elemento_nombre=nombre_calendario
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'El calendario para instructor {nombre_calendario} ha sido eliminado correctamente.',
                    'reload': True
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'No se pudo eliminar el calendario para instructor: {str(e)}'
                }, status=400)
        else:
            return super().post(request, *args, **kwargs)


# Vistas para el calendario de los ambientes
class CalAmbListView(LoginRequiredMixin, ListView):
    model = Calendar
    template_name = 'horarios/calamb/calamb_list.html'
    context_object_name = 'calambs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CalAmbForm()
        return context


class CalAmbCreateView(LoginRequiredMixin, CreateView):
    model = Calendar
    form_class = CalAmbForm
    template_name = 'horarios/calamb/calamb_form.html'
    success_url = reverse_lazy('calamb_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        calendario = self.object
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
        
        # Registrar la actividad de creación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='crear',
            descripcion=f'Se creó el calendario para ambiente: {nombre_calendario}',
            elemento_id=calendario.id,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario para ambiente {nombre_calendario} ha sido creado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El calendario para ambiente {nombre_calendario} ha sido creado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CalAmbUpdateView(LoginRequiredMixin, UpdateView):
    model = Calendar
    form_class = CalAmbForm
    template_name = 'horarios/calamb/calamb_form.html'
    success_url = reverse_lazy('calamb_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        calendario = self.object
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
        
        # Registrar la actividad de actualización con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='editar',
            descripcion=f'Se actualizó el calendario para ambiente: {nombre_calendario}',
            elemento_id=calendario.id,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario para ambiente {nombre_calendario} ha sido actualizado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El calendario para ambiente {nombre_calendario} ha sido actualizado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CalAmbDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    template_name = 'horarios/calamb/calamb_confirm_delete.html'
    success_url = reverse_lazy('calamb_list')
    
    def delete(self, request, *args, **kwargs):
        calendario = self.get_object()
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
            
        id_temp = calendario.id
        
        response = super().delete(request, *args, **kwargs)
        
        # Registrar la actividad de eliminación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='eliminar',
            descripcion=f'Se eliminó el calendario para ambiente: {nombre_calendario}',
            elemento_id=id_temp,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario para ambiente {nombre_calendario} ha sido eliminado correctamente.')
        else:
            messages.warning(self.request, f'El calendario para ambiente {nombre_calendario} ha sido eliminado, pero hubo un problema al registrar la actividad.')
        
        return response
    
    # Soporte para AJAX
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                calendario = self.get_object()
                
                # Obtener el nombre del calendario
                nombre_calendario = getattr(calendario, 'title', None)
                
                if nombre_calendario is None:
                    posibles_campos = ['name', 'nombre', 'title', 'title']
                    for campo in posibles_campos:
                        if hasattr(calendario, campo):
                            nombre_calendario = getattr(calendario, campo)
                            break
                
                if nombre_calendario is None:
                    nombre_calendario = f'Calendario ID:{calendario.id}'
                    
                id_temp = calendario.id
                
                calendario.delete()
                
                # Registrar la actividad de eliminación
                exito = registrar_actividad(
                    usuario=request.user,
                    tipo='horario',
                    accion='eliminar',
                    descripcion=f'Se eliminó el calendario para ambiente: {nombre_calendario}',
                    elemento_id=id_temp,
                    elemento_nombre=nombre_calendario
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'El calendario para ambiente {nombre_calendario} ha sido eliminado correctamente.',
                    'reload': True
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'No se pudo eliminar el calendario para ambiente: {str(e)}'
                }, status=400)
        else:
            return super().post(request, *args, **kwargs)


# Vistas para el calendario de los programas de formacion
class CalPFListView(LoginRequiredMixin, ListView):
    model = Calendar
    template_name = 'horarios/calpf/calpf_list.html'
    context_object_name = 'calpfs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CalAmbForm()
        return context


class CalPFCreateView(LoginRequiredMixin, CreateView):
    model = Calendar
    form_class = CalPFForm
    template_name = 'horarios/calpf/calpf_form.html'
    success_url = reverse_lazy('calpf_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        calendario = self.object
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
        
        # Registrar la actividad de creación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='crear',
            descripcion=f'Se creó el calendario para programa de formación: {nombre_calendario}',
            elemento_id=calendario.id,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario para programa {nombre_calendario} ha sido creado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El calendario para programa {nombre_calendario} ha sido creado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CalPFUpdateView(LoginRequiredMixin, UpdateView):
    model = Calendar
    form_class = CalPFForm
    template_name = 'horarios/calpf/calpf_form.html'
    success_url = reverse_lazy('calpf_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        calendario = self.object
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
        
        # Registrar la actividad de actualización con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='editar',
            descripcion=f'Se actualizó el calendario para programa de formación: {nombre_calendario}',
            elemento_id=calendario.id,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario para programa {nombre_calendario} ha sido actualizado correctamente.')
        else:
            messages.success(self.request, f'¡Éxito! El calendario para programa {nombre_calendario} ha sido actualizado correctamente, pero hubo un problema al registrar la actividad.')
        
        return response


class CalPFDeleteView(LoginRequiredMixin, DeleteView):
    model = Calendar
    template_name = 'horarios/calpf/calpf_confirm_delete.html'
    success_url = reverse_lazy('calpf_list')
    
    def delete(self, request, *args, **kwargs):
        calendario = self.get_object()
        
        # Obtener el nombre del calendario usando el atributo correcto
        nombre_calendario = getattr(calendario, 'title', None)
        
        # Si 'title' no existe, intentar otros posibles nombres de campo
        if nombre_calendario is None:
            posibles_campos = ['name', 'nombre', 'title', 'title']
            for campo in posibles_campos:
                if hasattr(calendario, campo):
                    nombre_calendario = getattr(calendario, campo)
                    break
        
        # Si no se encuentra ningún campo, usar un nombre genérico
        if nombre_calendario is None:
            nombre_calendario = f'Calendario ID:{calendario.id}'
            
        id_temp = calendario.id
        
        response = super().delete(request, *args, **kwargs)
        
        # Registrar la actividad de eliminación con la versión mejorada
        exito = registrar_actividad(
            usuario=self.request.user,
            tipo='horario',
            accion='eliminar',
            descripcion=f'Se eliminó el calendario para programa de formación: {nombre_calendario}',
            elemento_id=id_temp,
            elemento_nombre=nombre_calendario
        )
        
        if exito:
            messages.success(self.request, f'¡Éxito! El calendario para programa {nombre_calendario} ha sido eliminado correctamente.')
        else:
            messages.warning(self.request, f'El calendario para programa {nombre_calendario} ha sido eliminado, pero hubo un problema al registrar la actividad.')
        
        return response
    
    # Soporte para AJAX
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                calendario = self.get_object()
                
                # Obtener el nombre del calendario
                nombre_calendario = getattr(calendario, 'title', None)
                
                if nombre_calendario is None:
                    posibles_campos = ['name', 'nombre', 'title', 'title']
                    for campo in posibles_campos:
                        if hasattr(calendario, campo):
                            nombre_calendario = getattr(calendario, campo)
                            break
                
                if nombre_calendario is None:
                    nombre_calendario = f'Calendario ID:{calendario.id}'
                    
                id_temp = calendario.id
                
                calendario.delete()
                
                # Registrar la actividad de eliminación
                exito = registrar_actividad(
                    usuario=request.user,
                    tipo='horario',
                    accion='eliminar',
                    descripcion=f'Se eliminó el calendario para programa de formación: {nombre_calendario}',
                    elemento_id=id_temp,
                    elemento_nombre=nombre_calendario
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'El calendario para programa {nombre_calendario} ha sido eliminado correctamente.',
                    'reload': True
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'No se pudo eliminar el calendario para programa: {str(e)}'
                }, status=400)
        else:
            return super().post(request, *args, **kwargs)


# Vista para el Login
def login_view(request):
    """
    Vista para manejar el inicio de sesión de usuarios.
    Verifica credenciales y redirige al dashboard si son correctas.
    """
    # Si el usuario ya está autenticado, redirigirlo al dashboard
    if request.user.is_authenticated:
        # Usar correo_institucional en lugar de username
        print(f"Usuario ya autenticado: {request.user.correo_institucional}. Redirigiendo al dashboard.")
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')  # Mantener nombre del campo como 'username' en el formulario
        password = request.POST.get('password')
        
        # Mensaje de depuración para verificar las credenciales recibidas
        print(f"Intento de login - Usuario: {username}")
        
        # Django usará el backend de autenticación para encontrar al usuario
        # El USERNAME_FIELD en tu modelo Administrador está configurado como 'correo_institucional'
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            print(f"✅ Login exitoso para el usuario: {username}")
            return redirect('admin_dashboard')
        else:
            error_message = "Credenciales inválidas o usuario no es administrador."
            print(f"❌ Login fallido para el usuario: {username}")
            
            # Depuración adicional
            if user is None:
                print("   - Usuario no encontrado o contraseña incorrecta")
            elif not user.is_staff:
                print("   - Usuario existe pero no tiene permisos de staff")
            
            return render(request, 'horarios/login.html', {'error_message': error_message})
    
    print("Mostrando formulario de login")
    return render(request, 'horarios/login.html')


@login_required
def admin_dashboard(request):
    administrador = request.user
    nombre_completo = f"{administrador.nombres} {administrador.apellidos}"

    # Contar el número de registros en cada modelo
    total_administradores = Administrador.objects.count()
    total_instructores = Instructor.objects.count()
    total_programas = ProgramaFormacion.objects.count()
    total_competencias = Competencia.objects.count()

    current_date = date.today()
    
    # Obtener las actividades recientes para mostrar en el dashboard si es necesario
    try:
        actividades_recientes = ActividadSistema.objects.all().order_by('-fecha_hora')[:10]
    except:
        actividades_recientes = []  # Lista vacía si la tabla no existe o hay error
    
    # Pasar los datos al template
    return render(request, 'horarios/admin_dashboard.html', {
        'admin_name': nombre_completo,
        'total_administradores': total_administradores,
        'total_instructores': total_instructores,
        'total_programas': total_programas,
        'total_competencias': total_competencias,
        'current_date': current_date,
        'actividades_recientes': actividades_recientes
    })


# Vista para obtener todos los eventos
def get_all_events(request):
    events = []

    # Obtener eventos de Instructores
    instructors = Instructor.objects.all()
    for instructor in instructors:
        events.append({
            'id_instructor': instructor.id,
            'instructor': instructor.nombres + ' ' + instructor.apellidos,
        })

    # Obtener eventos de Programas de Formación
    programas = ProgramaFormacion.objects.all()
    for programa in programas:
        events.append({
            'id_programa': programa.id,
            'programa': programa.codigo_programa + ' - ' + programa.nombre_programa,
        })

    # Obtener eventos de Ambientes
    ambientes = Ambiente.objects.all()
    for ambiente in ambientes:
        events.append({
            'id_ambiente': ambiente.id,
            'ambiente': ambiente.codigo_ambiente + ' - ' + ambiente.nombre_ambiente,
        })

    return JsonResponse(events, safe=False)


# Para que se puedan cargar instructores con un archivo csv
@login_required
def upload_instructors_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES['file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'El archivo debe ser en formato CSV.')
            return redirect('instructor_list')

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        next(reader)  # Ignora el encabezado
        
        instructores_creados = 0

        for row in reader:
            if len(row) < 6:
                messages.error(request, 'Faltan datos en una de las filas.')
                continue

            try:
                # Crea el instructor
                instructor = Instructor.objects.create(
                    nombres=row[0],
                    apellidos=row[1],
                    correo_institucional=row[2],
                    numero_celular=row[3],
                    numero_cedula=row[4],
                    competencias_imparte=row[5],
                )
                
                # Registrar la actividad de creación con la versión mejorada
                exito = registrar_actividad(
                    usuario=request.user,
                    tipo='instructor',
                    accion='crear',
                    descripcion=f'Se creó el instructor {instructor.nombres} {instructor.apellidos} mediante carga CSV',
                    elemento_id=instructor.id,
                    elemento_nombre=f'{instructor.nombres} {instructor.apellidos}'
                )
                
                instructores_creados += 1
            except Exception as e:
                messages.error(request, f'Error al crear instructor: {str(e)}')

        if instructores_creados > 0:
            messages.success(request, f'Se han cargado {instructores_creados} instructores correctamente.')
            
            # Registrar actividad general si se cargaron varios instructores
            if instructores_creados > 1:
                registrar_actividad(
                    usuario=request.user,
                    tipo='instructor',
                    accion='crear',
                    descripcion=f'Importación masiva de {instructores_creados} instructores desde archivo CSV',
                    elemento_id=None,
                    elemento_nombre='Importación CSV'
                )
                
        return redirect('instructor_list')

    return redirect('instructor_list')  # En caso de que no sea un POST


@login_required
def upload_instructors_excel(request):
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'Por favor, selecciona un archivo Excel.')
            return redirect('instructor_list')
            
        excel_file = request.FILES['file']
        
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'El archivo debe ser Excel (.xlsx o .xls)')
            return redirect('instructor_list')
            
        try:
            df = pd.read_excel(excel_file)
            required_columns = ['nombres', 'apellidos', 'correo_institucional', 
                              'numero_celular', 'numero_cedula']
            
            df.columns = df.columns.str.lower()
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messages.error(request, 
                    f'El archivo no contiene las siguientes columnas requeridas: {", ".join(missing_columns)}')
                return redirect('instructor_list')
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Validaciones mejoradas
                    nombres = str(row['nombres']).strip()
                    apellidos = str(row['apellidos']).strip()
                    correo = str(row['correo_institucional']).strip()
                    celular = str(row['numero_celular']).strip()
                    cedula = str(row['numero_cedula']).strip()
                    
                    if not all([nombres, apellidos, correo, celular, cedula]):
                        raise ValidationError('Todos los campos son obligatorios')
                    
                    if not correo.endswith('@sena.edu.co'):
                        raise ValidationError('El correo debe ser institucional (@sena.edu.co)')
                    
                    if len(str(celular)) != 10:
                        raise ValidationError('El número de celular debe tener 10 dígitos')
                    
                    instructor = Instructor.objects.create(
                        nombres=nombres,
                        apellidos=apellidos,
                        correo_institucional=correo,
                        numero_celular=celular,
                        numero_cedula=cedula
                    )
                    
                    # Registrar la actividad de creación con la versión mejorada
                    exito = registrar_actividad(
                        usuario=request.user,
                        tipo='instructor',
                        accion='crear',
                        descripcion=f'Se creó el instructor {nombres} {apellidos} mediante carga Excel',
                        elemento_id=instructor.id,
                        elemento_nombre=f'{nombres} {apellidos}'
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    if "Duplicate entry" in error_msg:
                        error_msg = f"La cédula '{cedula}' ya está registrada"
                    messages.error(request, f"Fila {index + 2}: {error_msg}")
                    continue
            
            if success_count > 0:
                messages.success(request, 
                    f'¡Éxito! Se importaron {success_count} instructores correctamente.')
                
                # Registrar actividad general de importación
                if success_count > 1:
                    registrar_actividad(
                        usuario=request.user,
                        tipo='instructor',
                        accion='crear',
                        descripcion=f'Importación masiva de {success_count} instructores desde archivo Excel',
                        elemento_id=None,
                        elemento_nombre='Importación Excel'
                    )
                    
            if error_count > 0:
                messages.warning(request, 
                    f'No se pudieron importar {error_count} registros. Revisa los errores mostrados.')
                
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            
        return redirect('instructor_list')
    
    return redirect('instructor_list')


@login_required
def download_instructor_template(request):
    # Crear la plantilla
    template_path = create_instructor_template()
    
    # Abrir el archivo
    file = open(template_path, 'rb')
    
    # Crear la respuesta
    response = FileResponse(
        file,
        as_attachment=True,
        filename='plantilla_instructores.xlsx'
    )
    
    return response


@login_required
@require_POST
def delete_all_instructors(request):
    try:
        # Obtener el número total de instructores antes de eliminar
        total_instructores = Instructor.objects.count()
        
        if total_instructores > 0:
            # Registrar la actividad de eliminación masiva con la versión mejorada
            exito = registrar_actividad(
                usuario=request.user,
                tipo='instructor',
                accion='eliminar',
                descripcion=f'Se eliminaron {total_instructores} instructores de forma masiva',
                elemento_id=None,
                elemento_nombre='Eliminación masiva'
            )
            
            # Eliminar todos los instructores
            Instructor.objects.all().delete()
            
            # Devolver respuesta exitosa
            mensaje = f'Se eliminaron {total_instructores} instructores exitosamente'
            if not exito:
                mensaje += ', pero hubo un problema al registrar la actividad'
                
            return JsonResponse({
                'status': 'success',
                'message': mensaje
            })
        else:
            return JsonResponse({
                'status': 'warning',
                'message': 'No hay instructores para eliminar'
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def crear_instructor(request):
    # Aquí irá la lógica para crear un instructor
    return render(request, 'horarios/crear_instructor.html')


@login_required
def programa_form(request):
    if request.method == 'POST':
        form = ProgramaFormacionForm(request.POST)
        if form.is_valid():
            programa = form.save()
            
            # Registrar la actividad de creación con la versión mejorada
            exito = registrar_actividad(
                usuario=request.user,
                tipo='programa',
                accion='crear',
                descripcion=f'Se creó el programa de formación {programa.nombre_programa}',
                elemento_id=programa.id,
                elemento_nombre=programa.nombre_programa
            )
            
            if exito:
                messages.success(request, 'Programa de formación creado exitosamente.')
            else:
                messages.success(request, 'Programa de formación creado exitosamente, pero hubo un problema al registrar la actividad.')
                
            return redirect('programa_formacion_list')
    else:
        form = ProgramaFormacionForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Programa de Formación'
    }
    return render(request, 'horarios/programasformacion/programa_formacion_form.html', context)


@login_required
def crear_competencia(request):
    # Aquí irá la lógica para crear una competencia
    return render(request, 'horarios/crear_competencia.html')


@login_required
def generar_horario(request):
    """
    Redirecciona a la vista para crear un calendario de ambiente.
    """
    # Registrar la actividad y luego redirigir
    if request.method == 'POST':
        exito = registrar_actividad(
            usuario=request.user,
            tipo='horario',
            accion='generar',
            descripcion='Se accedió al formulario de generación de horario',
            elemento_id=None,
            elemento_nombre='Generación de horario'
        )
        
        if not exito:
            messages.warning(request, 'Hubo un problema al registrar la actividad.')
    
    # Redirigir a la vista de crear calendario de ambiente
    return redirect('calamb_create')


@login_required
def instructor_form(request):
    if request.method == 'POST':
        form = InstructorForm(request.POST)
        if form.is_valid():
            instructor = form.save()
            
            # Registrar la actividad de creación con la versión mejorada
            exito = registrar_actividad(
                usuario=request.user,
                tipo='instructor',
                accion='crear',
                descripcion=f'Se creó el instructor {instructor.nombres} {instructor.apellidos}',
                elemento_id=instructor.id,
                elemento_nombre=f'{instructor.nombres} {instructor.apellidos}'
            )
            
            if exito:
                messages.success(request, 'Instructor creado exitosamente.')
            else:
                messages.success(request, 'Instructor creado exitosamente, pero hubo un problema al registrar la actividad.')
                
            return redirect('instructor_list')
    else:
        form = InstructorForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Instructor'
    }
    return render(request, 'horarios/instructores/instructor_form.html', context)

@login_required
def competencia_form(request):
    if request.method == 'POST':
        form = CompetenciaForm(request.POST)
        if form.is_valid():
            competencia = form.save()
            
            # Registrar la actividad de creación con la versión mejorada
            exito = registrar_actividad(
                usuario=request.user,
                tipo='competencia',
                accion='crear',
                descripcion=f'Se creó la competencia {competencia.nombre}',
                elemento_id=competencia.id,
                elemento_nombre=competencia.nombre
            )
            
            if exito:
                messages.success(request, 'Competencia creada exitosamente.')
            else:
                messages.success(request, 'Competencia creada exitosamente, pero hubo un problema al registrar la actividad.')
                
            return redirect('competencia_list')
    else:
        form = CompetenciaForm()
    
    context = {
        'form': form,
        'title': 'Crear Nueva Competencia'
    }
    return render(request, 'horarios/competencias/competencia_form.html', context)


@login_required
def horario_form(request):
    """
    Vista para el formulario de generación de horarios.
    Utiliza el template calendar_form.html
    """
    if request.method == 'POST':
        form = CalendarForm(request.POST)
        if form.is_valid():
            calendario = form.save()
            
            # Registrar la actividad de creación
            exito = registrar_actividad(
                usuario=request.user,
                tipo='horario',
                accion='crear',
                descripcion=f'Se creó un nuevo horario',
                elemento_id=calendario.id,
                elemento_nombre=getattr(calendario, 'title', f'Calendario ID:{calendario.id}')
            )
            
            if exito:
                messages.success(request, '¡Horario creado exitosamente!')
            else:
                messages.success(request, '¡Horario creado exitosamente, pero hubo un problema al registrar la actividad!')
            
            return redirect('calendar_list')
    else:
        form = CalendarForm()
    
    # Preparar el contexto para la plantilla
    context = {
        'form': form,
        'object': None  # Para indicar que es una creación, no una edición
    }
    
    # Usar el template calendar_form.html
    return redirect('calendar_create')