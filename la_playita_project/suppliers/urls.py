from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.proveedor_list, name='proveedor_list'),
    path('proveedor/crear_ajax/', views.proveedor_create_ajax, name='proveedor_create_ajax'),

    path('reabastecimientos/', views.reabastecimiento_list, name='reabastecimiento_list'),
    path('reabastecimientos/crear/', views.reabastecimiento_create, name='reabastecimiento_create'),
    path('reabastecimientos/<int:pk>/editar/', views.reabastecimiento_editar, name='reabastecimiento_editar'),
    path('reabastecimientos/<int:pk>/actualizar/', views.reabastecimiento_update, name='reabastecimiento_update'),
    path('reabastecimientos/<int:pk>/recibir/', views.reabastecimiento_recibir, name='reabastecimiento_recibir'),
    path('reabastecimientos/<int:pk>/actualizar-recibido/', views.reabastecimiento_update_received, name='reabastecimiento_update_received'),
    path('reabastecimientos/<int:pk>/eliminar/', views.reabastecimiento_eliminar, name='reabastecimiento_eliminar'),
    path('reabastecimientos/<int:pk>/enviar-borrador/', views.reabastecimiento_enviar_borrador, name='reabastecimiento_enviar_borrador'),
    path('categoria/crear_ajax/', views.categoria_create_ajax, name='categoria_create_ajax'),
    path('producto/crear_ajax/', views.producto_create_ajax, name='producto_create_ajax'),
    path('api/search-suppliers/', views.search_suppliers_ajax, name='search_suppliers_ajax'), # New API endpoint
    path('api/search-products/', views.search_products_ajax, name='search_products_ajax'), # New API endpoint

    # New API endpoints for dynamic content loading
    path('reabastecimientos/<int:pk>/row_api/', views.reabastecimiento_row_api, name='reabastecimiento_row_api'),
    path('reabastecimientos/<int:pk>/details_api/', views.reabastecimiento_detail_api, name='reabastecimiento_detail_api'),
    path('reabastecimientos/<int:pk>/audit_history/', views.reabastecimiento_audit_history, name='reabastecimiento_audit_history'),
    path('reabastecimientos/<int:pk>/get_reception_form_api/', views.get_reception_form_api, name='get_reception_form_api'),
    path('reabastecimientos/<int:pk>/get_edit_form_api/', views.get_edit_form_api, name='get_edit_form_api'),

    # API endpoints for Select2 search
    path('api/search_proveedores/', views.api_search_proveedores, name='api_search_proveedores'),
    path('api/search_productos/', views.api_search_productos, name='api_search_productos'),
    
    # Export endpoints
    path('reabastecimientos/<int:pk>/download/pdf/', views.reabastecimiento_download_pdf, name='reabastecimiento_download_pdf'),
    path('reabastecimientos/<int:pk>/download/excel/', views.reabastecimiento_download_excel, name='reabastecimiento_download_excel'),
    
    # Import endpoints
    path('reabastecimientos/template/download/', views.download_template_excel, name='download_template_excel'),
    path('reabastecimientos/import/excel/', views.import_excel_reabastecimiento, name='import_excel_reabastecimiento'),
]