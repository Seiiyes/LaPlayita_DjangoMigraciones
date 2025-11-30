from django import template

register = template.Library()

@register.filter
def calculate_total_pending_value(reabastecimiento):
    """
    Calcula el valor total pendiente de un reabastecimiento.
    """
    total_pending = 0
    for detalle in reabastecimiento.reabastecimientodetalle_set.all():
        total_pending += (detalle.cantidad - detalle.cantidad_recibida) * detalle.costo_unitario
    return total_pending

@register.simple_tag
def get_estado_reabastecimiento_display(estado):
    """
    Retorna un badge HTML con el estado del reabastecimiento.
    """
    estado_map = {
        'solicitado': ('bg-warning text-dark', 'Solicitado'),
        'recibido': ('bg-success', 'Recibido'),
        'cancelado': ('bg-danger', 'Cancelado'),
    }
    
    color_class, display_text = estado_map.get(estado, ('bg-info text-dark', estado))
    return f'<span class="badge {color_class}">{display_text}</span>'

@register.filter
def count_received(detalles_queryset):
    """
    Cuenta cuántos detalles tienen cantidad_recibida > 0
    """
    if not detalles_queryset:
        return 0
    return sum(1 for d in detalles_queryset if d.cantidad_recibida > 0)

@register.filter
def multiply(value, arg):
    """
    Multiplica dos números
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """
    Divide dos números
    """
    try:
        result = float(value) / float(arg)
        return int(result)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def subtract(value, arg):
    """
    Resta dos números
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0
