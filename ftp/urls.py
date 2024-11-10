from django.urls import path
from home import views

urlpatterns = [
    path('start_server/', views.start_server, name='start_server'),
    path('start_client/', views.start_client, name='start_client'),
]
