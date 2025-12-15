from django import forms
from .models import (
    Pqrs, PqrsAdjunto, PqrsCalificacion, 
    PqrsPlantillaRespuesta, PqrsVistaGuardada
)
from django.conf import settings


class PqrsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar opción vacía con texto personalizado
        self.fields['tipo'].empty_label = "Seleccione el tipo..."
        self.fields['categoria'].empty_label = "Seleccione categoría..."
        self.fields['prioridad'].empty_label = "Seleccione prioridad..."
        self.fields['canal_origen'].empty_label = "Seleccione canal..."
    
    class Meta:
        model = Pqrs
        fields = ['tipo', 'categoria', 'prioridad', 'canal_origen', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'categoria': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'prioridad': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'canal_origen': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 6, 
                'placeholder': 'Describa detalladamente el caso, incluyendo todos los detalles relevantes...',
                'required': True
            }),
        }
        labels = {
            'tipo': 'Tipo de PQRS',
            'categoria': 'Categoría',
            'prioridad': 'Prioridad',
            'canal_origen': 'Canal de Origen',
            'descripcion': 'Descripción del Caso',
        }


class PqrsUpdateForm(forms.ModelForm):
    respuesta = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 5, 
            'placeholder': '✍️ Escriba aquí la respuesta que se enviará por correo al cliente...\n\nEjemplo:\nEstimado cliente, hemos recibido su solicitud y estamos trabajando en una solución. Le mantendremos informado sobre el progreso.',
            'required': True
        }),
        label="Respuesta para el Cliente",
        required=False
    )
    observacion_estado = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Explique el motivo del cambio de estado...'}),
        label="Observación para el cambio de estado",
        required=False
    )
    nota_interna = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Nota interna (no visible para el cliente)...'}),
        label="Añadir nota interna",
        required=False
    )

    class Meta:
        model = Pqrs
        fields = []


class PqrsAsignarForm(forms.ModelForm):
    class Meta:
        model = Pqrs
        fields = ['asignado_a']
        widgets = {
            'asignado_a': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'asignado_a': 'Asignar a',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar usuarios (Vendedor y Administrador)
        from users.models import Usuario
        self.fields['asignado_a'].queryset = Usuario.objects.all().order_by('username')


class PqrsCalificacionForm(forms.ModelForm):
    class Meta:
        model = PqrsCalificacion
        fields = ['puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comentarios adicionales (opcional)...'}),
        }
        labels = {
            'puntuacion': '¿Cómo calificarías la atención recibida?',
            'comentario': 'Comentarios',
        }


class PqrsAdjuntoForm(forms.ModelForm):
    class Meta:
        model = PqrsAdjunto
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción del archivo (opcional)'}),
        }


class PqrsPlantillaForm(forms.ModelForm):
    """Formulario para crear/editar plantillas de respuesta"""
    class Meta:
        model = PqrsPlantillaRespuesta
        fields = ['nombre', 'tipo', 'categoria', 'contenido', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la plantilla'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 10,
                'placeholder': 'Contenido de la plantilla. Usa {{cliente_nombre}}, {{numero_caso}}, {{sla_horas}} para variables dinámicas'
            }),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre de la Plantilla',
            'tipo': 'Tipo de PQRS (opcional)',
            'categoria': 'Categoría (opcional)',
            'contenido': 'Contenido',
            'activa': 'Activa',
        }
        help_texts = {
            'contenido': 'Variables disponibles: {{cliente_nombre}}, {{numero_caso}}, {{sla_horas}}, {{solucion}}, {{informacion_requerida}}'
        }


class PqrsVistaGuardadaForm(forms.ModelForm):
    """Formulario para guardar vistas personalizadas"""
    class Meta:
        model = PqrsVistaGuardada
        fields = ['nombre', 'es_publica']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la vista'}),
            'es_publica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre de la Vista',
            'es_publica': 'Compartir con otros usuarios',
        }


class PqrsRespuestaConPlantillaForm(forms.Form):
    """Formulario mejorado para responder con plantillas"""
    plantilla = forms.ModelChoiceField(
        queryset=PqrsPlantillaRespuesta.objects.filter(activa=True),
        required=False,
        empty_label="-- Seleccionar plantilla --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'plantilla-select'}),
        label="Usar Plantilla"
    )
    respuesta = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 8,
            'id': 'respuesta-textarea',
            'placeholder': 'Escriba la respuesta que se enviará al cliente...'
        }),
        label="Respuesta para el Cliente",
        required=True
    )
    enviar_correo = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Enviar correo al cliente"
    )
