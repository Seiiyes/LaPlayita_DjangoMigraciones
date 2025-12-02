from django import forms
from .models import Pqrs, PqrsAdjunto


class PqrsForm(forms.ModelForm):
    class Meta:
        model = Pqrs
        fields = ['tipo', 'categoria', 'prioridad', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describa detalladamente el caso...'}),
        }
        labels = {
            'tipo': 'Tipo de PQRS',
            'categoria': 'Categoría',
            'prioridad': 'Prioridad',
            'descripcion': 'Descripción del caso',
        }


class PqrsUpdateForm(forms.ModelForm):
    respuesta = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Escriba la respuesta que se enviará al cliente...'}),
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


class PqrsAdjuntoForm(forms.ModelForm):
    class Meta:
        model = PqrsAdjunto
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción del archivo (opcional)'}),
        }