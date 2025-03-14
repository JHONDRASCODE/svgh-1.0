from django.urls import path
from .api_views import CalendarListCreateView, CalendarRetrieveUpdateDestroyView

urlpatterns = [
    path('calendars/', CalendarListCreateView.as_view(), name='calendar-list-create'),
    path('calendars/<int:pk>/', CalendarRetrieveUpdateDestroyView.as_view(), name='calendar-detail'),
]
