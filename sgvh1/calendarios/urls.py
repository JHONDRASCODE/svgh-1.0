# calendarios/urls.py

from django.urls import path
from .views import cal_eventos, get_all_events

urlpatterns = [
    path('cal_eventos/', cal_eventos, name='cal_eventos'),
    
    # Ruta para obtener todos los eventos
    path('get_all_events/', get_all_events, name='get_all_events'),
]
