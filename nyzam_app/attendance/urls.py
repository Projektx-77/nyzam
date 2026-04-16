from django.urls import path
from .views import mark_attendance

urlpatterns = [
    path('mark/<int:event_id>/', mark_attendance, name='mark_attendance'),
]
