from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.doctor_login, name='doctor_login'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('logout/', views.doctor_logout, name='doctor_logout'),
    path('appointment/<int:id>/approve/', views.approve_appointment, name='approve_appointment'),
    path('appointment/<int:id>/reject/', views.reject_appointment, name='reject_appointment'),
]
