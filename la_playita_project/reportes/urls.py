from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.panel_reportes, name='panel_reportes'),
    path('ventas/', views.reporte_ventas, name='reporte_ventas'),
    path('inventario/', views.reporte_inventario, name='reporte_inventario'),
    path('clientes/', views.reporte_clientes, name='reporte_clientes'),
]
