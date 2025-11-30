from django import template
from django.utils.safestring import mark_safe

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

@register.filter
def subtract(value, arg):
    """
    Resta el argumento (arg) del valor (value).
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return ''

@register.simple_tag
def get_estado_reabastecimiento_display(estado):
    """
    Retorna un badge HTML con el estado del reabastecimiento.
    """
    estado_map = {
        'solicitado': ('warning', 'Solicitado'),
        'recibido': ('success', 'Recibido'),
        'cancelado': ('danger', 'Cancelado'),
    }
    
    color, label = estado_map.get(estado, ('secondary', estado))
    html = f'<span class="badge bg-{color}">{label}</span>'
    return mark_safe(html)