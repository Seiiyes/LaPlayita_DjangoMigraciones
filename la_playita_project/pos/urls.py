from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    # Vistas principales
    path('', views.pos_view, name='pos_view'),
    
    # APIs para el POS
    path('api/buscar-productos/', views.buscar_productos, name='buscar_productos'),
    path('api/producto/<int:producto_id>/', views.obtener_producto, name='obtener_producto'),
    path('api/obtener-clientes/', views.obtener_clientes, name='obtener_clientes'),
    path('api/procesar-venta/', views.procesar_venta, name='procesar_venta'),
    
    # Vistas de ventas
    path('venta/<int:venta_id>/', views.venta_detalle, name='venta_detalle'),
    path('ventas/', views.listar_ventas, name='listar_ventas'),
    path('venta/<int:venta_id>/descargar/', views.descargar_factura, name='descargar_factura'),
    path('venta/<int:venta_id>/enviar-factura/', views.enviar_factura, name='enviar_factura'),
    path('test-email/', views.test_email_config, name='test_email_config'),
    path('emails-pendientes/', views.emails_pendientes, name='emails_pendientes'),
    path('api/crear-cliente/', views.crear_cliente, name='crear_cliente'),
    
    # Dashboard de Reportes
    path('dashboard/', views.dashboard_reportes, name='dashboard_reportes'),
    path('api/ventas-por-fecha/', views.api_ventas_por_fecha, name='api_ventas_por_fecha'),
    path('api/comparativa-metodos-pago/', views.api_comparativa_metodos_pago, name='api_comparativa_metodos_pago'),
    path('api/ventas-por-hora/', views.api_ventas_por_hora, name='api_ventas_por_hora'),
    
    # APIs de Mesas
    path('api/mesas/', views.api_listar_mesas, name='api_listar_mesas'),

    path('api/mesa/crear/', views.api_crear_mesa, name='api_crear_mesa'),
    path('api/mesa/<int:mesa_id>/editar/', views.api_editar_mesa, name='api_editar_mesa'),
    path('api/mesa/<int:mesa_id>/eliminar/', views.api_eliminar_mesa, name='api_eliminar_mesa'),
    path('api/mesa/<int:mesa_id>/abrir/', views.api_abrir_mesa, name='api_abrir_mesa'),
    path('api/mesa/<int:mesa_id>/agregar-item/', views.api_agregar_item_mesa, name='api_agregar_item_mesa'),
    path('api/mesa/<int:mesa_id>/items/', views.api_items_mesa, name='api_items_mesa'),
    path('api/mesa/<int:mesa_id>/item/<int:item_id>/editar/', views.api_editar_item_mesa, name='api_editar_item_mesa'),
    path('api/mesa/<int:mesa_id>/item/<int:item_id>/eliminar/', views.api_eliminar_item_mesa, name='api_eliminar_item_mesa'),
    path('api/mesa/<int:mesa_id>/cerrar/', views.api_cerrar_mesa, name='api_cerrar_mesa'),
]