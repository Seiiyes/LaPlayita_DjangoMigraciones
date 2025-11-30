from django import forms
from django.core.validators import MinValueValidator
from .models import Producto, Lote, Categoria
from suppliers.models import Reabastecimiento, ReabastecimientoDetalle # Ensure Reabastecimiento is imported
from datetime import date
from django.forms import inlineformset_factory


class ProductoForm(forms.ModelForm):
    precio_unitario = forms.DecimalField(
        max_digits=12, 
        decimal_places=0,
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'})
    )
    stock_minimo = forms.IntegerField(
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'tasa_iva', 'precio_unitario', 'descripcion', 'stock_minimo', 'categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'tasa_iva': forms.Select(attrs={'class': 'form-select'}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }

class LoteForm(forms.ModelForm):
    cantidad_disponible = forms.IntegerField(
        label="Cantidad",
        validators=[MinValueValidator(1)],
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    costo_unitario_lote = forms.DecimalField(
        label="Costo por Unidad",
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'})
    )

    class Meta:
        model = Lote
        fields = [
            'producto', 'numero_lote', 'cantidad_disponible', 'costo_unitario_lote', 
            'fecha_caducidad'
        ]
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'numero_lote': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_caducidad': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_fecha_caducidad(self):
        fecha_caducidad = self.cleaned_data.get('fecha_caducidad')
        if fecha_caducidad and fecha_caducidad < date.today():
            raise forms.ValidationError("La fecha de caducidad no puede ser anterior a la fecha actual.")
        return fecha_caducidad


class ReabastecimientoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        initial_creation = kwargs.pop('initial_creation', False)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Reabastecimiento
        fields = ['proveedor', 'forma_pago', 'observaciones']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'forma_pago': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ReabastecimientoDetalleForm(forms.ModelForm):
    # Campo para seleccionar el porcentaje de IVA
    iva_porcentaje = forms.ChoiceField(
        choices=[('0', '0%'), ('5', '5%'), ('8', '8%'), ('19', '19%')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='IVA (%)',
        required=False,
        initial='0'
    )

    class Meta:
        model = ReabastecimientoDetalle
        fields = ['producto', 'cantidad', 'costo_unitario', 'fecha_caducidad']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'fecha_caducidad': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# Un formset para múltiples líneas de detalle en el formulario de reabastecimiento
ReabastecimientoDetalleFormSet = inlineformset_factory(
    Reabastecimiento,
    ReabastecimientoDetalle,
    form=ReabastecimientoDetalleForm,
    extra=1,
    can_delete=True,
    validate_min=False
)


class DescartarLoteForm(forms.Form):
    """Formulario para descartar productos de un lote"""
    
    MOTIVOS_DESCARTE = [
        ('daño', 'Producto dañado'),
        ('vencimiento', 'Producto vencido'),
        ('accidente', 'Accidente / Rotura'),
        ('calidad', 'Problema de calidad'),
        ('robo', 'Robo / Pérdida'),
        ('otro', 'Otro motivo'),
    ]
    
    cantidad = forms.IntegerField(
        label='Cantidad a descartar',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la cantidad'
        }),
        help_text='Cantidad de unidades a descartar de este lote'
    )
    
    motivo = forms.ChoiceField(
        label='Motivo del descarte',
        choices=MOTIVOS_DESCARTE,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Seleccione el motivo del descarte'
    )
    
    observaciones = forms.CharField(
        label='Observaciones',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Detalles adicionales sobre el descarte (opcional)'
        }),
        help_text='Información adicional sobre el descarte'
    )
    
    def __init__(self, *args, **kwargs):
        self.lote = kwargs.pop('lote', None)
        super().__init__(*args, **kwargs)
        
        if self.lote:
            # Actualizar el help_text con la cantidad disponible
            self.fields['cantidad'].help_text = (
                f'Cantidad disponible en el lote: {self.lote.cantidad_disponible} unidades'
            )
            self.fields['cantidad'].widget.attrs['max'] = self.lote.cantidad_disponible
    
    def clean_cantidad(self):
        """Validar que la cantidad no exceda la disponible en el lote"""
        cantidad = self.cleaned_data.get('cantidad')
        
        if not cantidad:
            raise forms.ValidationError('Debe ingresar una cantidad válida.')
        
        if cantidad <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor a cero.')
        
        if self.lote and cantidad > self.lote.cantidad_disponible:
            raise forms.ValidationError(
                f'La cantidad a descartar ({cantidad}) no puede ser mayor a la cantidad disponible '
                f'en el lote ({self.lote.cantidad_disponible}).'
            )
        
        return cantidad