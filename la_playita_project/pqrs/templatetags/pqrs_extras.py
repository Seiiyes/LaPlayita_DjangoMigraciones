from django import template

register = template.Library()

@register.filter(name='status_badge')
def status_badge(status):
    status_lower = status.lower()
    if status_lower == 'nuevo':
        return 'bg-primary'
    elif status_lower == 'en_proceso':
        return 'bg-orange text-white'
    elif status_lower == 'resuelto':
        return 'bg-success'
    elif status_lower == 'cerrado':
        return 'bg-secondary'
    else:
        return 'bg-info'
