# calendarios/urls.py

from django.urls import path
from .views import cal_eventos, get_all_events, get_filter_options

urlpatterns = [
    path('cal_eventos/', cal_eventos, name='cal_eventos'),
    
    # Ruta para obtener todos los eventos (mejorada pero con misma URL)
    path('get_all_events/', get_all_events, name='get_all_events'),
    
    # Ruta opcional para obtener opciones de filtros (puedes añadirla si la implementas)
    path('get_filter_options/', get_filter_options, name='get_filter_options'),
]