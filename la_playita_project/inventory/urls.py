from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventario_list, name='inventario_list'),
    path('alertas/', views.alertas_stock_list, name='alertas_stock'),
    path('producto/crear/', views.producto_create, name='producto_create'),
    path('producto/crear/ajax/', views.producto_create_ajax, name='producto_create_ajax'),
    path('producto/<int:pk>/json/', views.producto_detail_json, name='producto_detail_json'),
    path('producto/<int:pk>/editar/', views.producto_update, name='producto_update'),
    path('producto/<int:pk>/eliminar/', views.producto_delete, name='producto_delete'),
    path('producto/<int:pk>/lotes/', views.producto_lotes_json, name='producto_lotes_json'),
    path('producto/<int:producto_pk>/lotes/list/', views.lote_list, name='lote_list'),
    path('categoria/crear/', views.categoria_create, name='categoria_create'),
    path('lote/<int:lote_id>/descartar/', views.descartar_lote, name='descartar_lote'),
]