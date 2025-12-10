from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # === VISTAS PRINCIPALES (NUEVAS) ===
    path('', views.dashboard_inventario, name='dashboard'),
    path('productos/', views.productos_list_modern, name='productos_list'),
    path('alertas/', views.alertas_stock_list, name='alertas_stock'),
    
    # === GESTIÓN DE PRODUCTOS ===
    path('producto/crear/', views.producto_create_form, name='producto_create'),

    path('producto/<int:pk>/', views.producto_detalle, name='producto_detalle'),
    path('producto/<int:pk>/kardex/', views.kardex_producto, name='kardex_producto'),  # Legacy redirect
    path('producto/<int:pk>/editar/', views.producto_edit_form, name='producto_update'),
    path('producto/<int:pk>/eliminar/', views.producto_delete, name='producto_delete'),
    
    # === GESTIÓN DE CATEGORÍAS Y LOTES ===
    path('categoria/crear/', views.categoria_create, name='categoria_create'),
    path('lote/<int:lote_id>/descartar/', views.descartar_lote, name='descartar_lote'),
    
    # === REABASTECIMIENTOS ===
    path('reabastecimientos/', views.reabastecimientos_list, name='reabastecimientos_list'),
    
    # === AJUSTES DE INVENTARIO ===
    path('ajustes/', views.ajustes_list, name='ajustes_list'),
    
    # === REPORTES ===
    path('reportes/', views.reportes, name='reportes'),
    
    # === EXPORTAR ===
    path('productos/exportar/', views.exportar_productos_excel, name='exportar_productos'),
]