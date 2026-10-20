from django.urls import path
from . import views

urlpatterns = [
    path('', views.device_list, name='device_list'),
    path('add/', views.add_device, name='add_device'),
    path('control/<int:device_id>/', views.control_command_device, name='control_command_device'),
    path('edit/<int:device_id>/', views.edit_device, name='edit_device'),
    path('delete/<int:device_id>/', views.delete_device, name='delete_device'),
    path('update_sensor/<int:sensor_id>/', views.update_sensor_value, name='update_sensor_value'),
    path('get_sensor_values/', views.get_sensor_values, name='get_sensor_values'),  # Rota update valor sensor com polling com JavaScript e AJAX
]