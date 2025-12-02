from django.urls import path
from . import views

app_name = 'pqrs'

urlpatterns = [
    path('crear/', views.pqrs_create, name='pqrs_create'),
    path('', views.pqrs_list, name='pqrs_list'),
    path('<int:pk>/', views.pqrs_detail, name='pqrs_detail'),
    path('<int:pk>/update/', views.pqrs_update, name='pqrs_update'),
    path('<int:pk>/adjunto/', views.pqrs_upload_adjunto, name='pqrs_upload_adjunto'),
    path('<int:pk>/eliminar/', views.pqrs_delete, name='pqrs_delete'),
]