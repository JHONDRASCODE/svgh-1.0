from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from . import views
from .forms import CustomPasswordResetForm
from .views import (
    login_view, admin_dashboard, manual_view, instructor_search,
    CustomPasswordChangeView, set_password_change_return,
    AdministradorListView, AdministradorCreateView, AdministradorUpdateView, AdministradorDeleteView,
    InstructorListView, InstructorCreateView, InstructorUpdateView, InstructorDeleteView,
    ProgramaFormacionListView, ProgramaFormacionCreateView, ProgramaFormacionUpdateView, ProgramaFormacionDeleteView,
    AmbienteListView, AmbienteCreateView, AmbienteUpdateView, AmbienteDeleteView,
    CompetenciaListView, CompetenciaCreateView, CompetenciaUpdateView, CompetenciaDeleteView,
    CalInstListView, CalInstCreateView, CalInstUpdateView, CalInstDeleteView,
    CalAmbListView, CalAmbCreateView, CalAmbUpdateView, CalAmbDeleteView,
    CalPFListView, CalPFCreateView, CalPFUpdateView, CalPFDeleteView,
    CalendarListView, CalendarCreateView, CalendarUpdateView, CalendarDeleteView,
    get_all_events,
    upload_instructors_excel, download_instructor_template, delete_all_instructors,
    obtener_notificaciones, marcar_notificacion_leida, marcar_todas_leidas, eliminar_todas_notificaciones
)

urlpatterns = [

    # -------------------- AUTENTICACIÓN --------------------
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    path('password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='horarios/password_change_done.html'), name='password_change_done'),
    path('set-password-return/', set_password_change_return, name='set_password_return'),

    # -------------------- DASHBOARD --------------------
    path('dashboard/', login_required(admin_dashboard), name='admin_dashboard'),

    # -------------------- ADMINISTRADORES --------------------
    path('administradores/', login_required(AdministradorListView.as_view()), name='administrador_list'),
    path('administradores/create/', login_required(AdministradorCreateView.as_view()), name='administrador_create'),
    path('administradores/<int:pk>/edit/', login_required(AdministradorUpdateView.as_view()), name='administrador_edit'),
    path('administradores/<int:pk>/delete/', login_required(AdministradorDeleteView.as_view()), name='administrador_delete'),

    # -------------------- INSTRUCTORES --------------------
    path('instructores/', login_required(InstructorListView.as_view()), name='instructor_list'),
    path('instructores/create/', login_required(InstructorCreateView.as_view()), name='instructor_create'),
    path('instructores/<int:pk>/edit/', login_required(InstructorUpdateView.as_view()), name='instructor_edit'),
    path('instructores/<int:pk>/delete/', login_required(InstructorDeleteView.as_view()), name='instructor_delete'),
    path('instructores/search/', login_required(instructor_search), name='instructor_search'),

    # Importar / Exportar instructores
    path('instructores/upload/', views.upload_instructors_excel, name='upload_instructors_excel'),
    path('instructores/download-template/', views.download_instructor_template, name='download_instructor_template'),
    path('instructores/delete-all/', views.delete_all_instructors, name='delete_all_instructors'),

    # -------------------- PROGRAMAS DE FORMACIÓN --------------------
    path('programas/', login_required(ProgramaFormacionListView.as_view()), name='programa_formacion_list'),
    path('programas/create/', login_required(ProgramaFormacionCreateView.as_view()), name='programa_formacion_create'),
    path('programas/<int:pk>/edit/', login_required(ProgramaFormacionUpdateView.as_view()), name='programa_formacion_edit'),
    path('programas/<int:pk>/delete/', login_required(ProgramaFormacionDeleteView.as_view()), name='programa_formacion_delete'),

    # -------------------- AMBIENTES --------------------
    path('ambientes/', login_required(AmbienteListView.as_view()), name='ambiente_list'),
    path('ambientes/create/', login_required(AmbienteCreateView.as_view()), name='ambiente_create'),
    path('ambientes/<int:pk>/edit/', login_required(AmbienteUpdateView.as_view()), name='ambiente_edit'),
    path('ambientes/<int:pk>/delete/', login_required(AmbienteDeleteView.as_view()), name='ambiente_delete'),

    # -------------------- COMPETENCIAS --------------------
    path('competencias/', login_required(CompetenciaListView.as_view()), name='competencia_list'),
    path('competencias/create/', login_required(CompetenciaCreateView.as_view()), name='competencia_create'),
    path('competencias/<int:pk>/edit/', login_required(CompetenciaUpdateView.as_view()), name='competencia_edit'),
    path('competencias/<int:pk>/delete/', login_required(CompetenciaDeleteView.as_view()), name='competencia_delete'),

    # -------------------- CALENDARIOS --------------------
    path('calinsts/', login_required(CalInstListView.as_view()), name='calinst_list'),
    path('calinsts/create/', login_required(CalInstCreateView.as_view()), name='calinst_create'),
    path('calinsts/<int:pk>/edit/', login_required(CalInstUpdateView.as_view()), name='calinst_edit'),
    path('calinsts/<int:pk>/delete/', login_required(CalInstDeleteView.as_view()), name='calinst_delete'),

    path('calambs/', login_required(CalAmbListView.as_view()), name='calamb_list'),
    path('calambs/create/', login_required(CalAmbCreateView.as_view()), name='calamb_create'),
    path('calambs/<int:pk>/edit/', login_required(CalAmbUpdateView.as_view()), name='calamb_edit'),
    path('calambs/<int:pk>/delete/', login_required(CalAmbDeleteView.as_view()), name='calamb_delete'),

    path('calpfs/', login_required(CalPFListView.as_view()), name='calpf_list'),
    path('calpfs/create/', login_required(CalPFCreateView.as_view()), name='calpf_create'),
    path('calpfs/<int:pk>/edit/', login_required(CalPFUpdateView.as_view()), name='calpf_edit'),
    path('calpfs/<int:pk>/delete/', login_required(CalPFDeleteView.as_view()), name='calpf_delete'),

    path('calendars/', login_required(CalendarListView.as_view()), name='calendar_list'),
    path('calendars/create/', login_required(CalendarCreateView.as_view()), name='calendar_create'),
    path('calendars/<int:pk>/edit/', login_required(CalendarUpdateView.as_view()), name='calendar_edit'),
    path('calendars/<int:pk>/delete/', login_required(CalendarDeleteView.as_view()), name='calendar_delete'),

    # Horario desde botón "Generar"
    path('horario/generar/', login_required(CalendarCreateView.as_view()), name='generar_horario'),

    # Eventos del calendario
    path('eventos/', get_all_events, name='get_all_events'),

    # -------------------- ACCIONES RÁPIDAS --------------------
    path('instructor/crear/', views.instructor_form, name='crear_instructor'),
    path('programa/crear/', views.programa_form, name='crear_programa'),
    path('competencia/crear/', views.competencia_form, name='crear_competencia'),

    # -------------------- SISTEMA DE NOTIFICACIONES --------------------
    path('notificaciones/', login_required(obtener_notificaciones), name='obtener_notificaciones'),
    path('notificaciones/marcar-leida/<int:notificacion_id>/', login_required(marcar_notificacion_leida), name='marcar_notificacion_leida'),
    path('notificaciones/marcar-todas-leidas/', login_required(marcar_todas_leidas), name='marcar_todas_leidas'),
    path('notificaciones/eliminar-todas/', login_required(eliminar_todas_notificaciones), name='eliminar_todas_notificaciones'),
    path('notification-panel/', views.notification_panel, name='notification_panel'),

    # -------------------- MANUAL --------------------
    path('manual/', manual_view, name='manual'),

    # -------------------- RESET DE CONTRASEÑA --------------------
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='horarios/password_reset.html',
        email_template_name='horarios/password_reset_email.html',
        subject_template_name='horarios/password_reset_subject.txt',
        success_url='/password-reset/done/',
        form_class=CustomPasswordResetForm
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='horarios/password_reset_done.html'
    ), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='horarios/password_reset_confirm.html',
        success_url='/password-reset-complete/'
    ), name='password_reset_confirm'),

    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='horarios/password_reset_complete.html'
    ), name='password_reset_complete'),
]
