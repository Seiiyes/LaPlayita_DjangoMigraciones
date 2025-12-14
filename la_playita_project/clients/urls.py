from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Clientes - CRUD básico
    path('', views.cliente_list, name='cliente_list'),
    path('create-ajax/', views.cliente_create_ajax, name='cliente_create_ajax'),
    path('api/crear/', views.cliente_create_ajax, name='cliente_create_api'),  # Alias para PQRS
    path('api/cliente/<int:cliente_id>/', views.cliente_get_ajax, name='cliente_get_ajax'),
    path('api/cliente/<int:cliente_id>/editar/', views.cliente_update_ajax, name='cliente_update_ajax'),

    # Panel de puntos - Cliente específico
    path('panel-puntos/<int:cliente_id>/', views.panel_puntos, name='panel_puntos'),
    path('historial-puntos/<int:cliente_id>/', views.historial_puntos, name='historial_puntos'),
    path('canjes/<int:cliente_id>/', views.canjes_cliente, name='canjes_cliente'),

    # Mi panel de puntos (usuario logueado)
    path('mi-panel-puntos/', views.mi_panel_puntos, name='mi_panel_puntos'),

    # Productos canjeables (para usuario final; vista lista)
    path('productos-canjeables/', views.productos_canjebles, name='productos_canjebles'),

    # Canje de productos (AJAX POST)
    path('canjear-producto/<int:producto_id>/', views.canjear_producto, name='canjear_producto'),

    # Administración de productos canjeables (solo admin)
    path('admin/productos-canjebles/', views.administrar_productos_canjebles, name='admin_productos_canjebles'),
    path('admin/crear-producto-canjeble/', views.crear_producto_canjeble, name='crear_producto_canjeble'),
    path('admin/editar-producto-canjeble/<int:producto_id>/', views.editar_producto_canjeble, name='editar_producto_canjeble'),
    path('admin/eliminar-producto-canjeble/<int:producto_id>/', views.eliminar_producto_canjeble, name='eliminar_producto_canjeble'),

    # Administración de canjes (solo admin)
    path('admin/marcar-canje-entregado/<int:canje_id>/', views.marcar_canje_entregado, name='marcar_canje_entregado'),

    # Detalle de canje y envío de correo
    path('canje/<int:canje_id>/', views.detalle_canje, name='detalle_canje'),
    path('canje/<int:canje_id>/enviar-correo/', views.enviar_correo_canje, name='enviar_correo_canje'),

    # Opcional - Vistas adicionales de flujo tradicional web (sin AJAX)
    # Confirma y procesa canje por web (si usas el flujo HTML tradicional)
    path('confirmar-canje/<int:producto_id>/', views.canjearproducto_web, name='confirmar_canje'),

    # ----- FIN -----
]
