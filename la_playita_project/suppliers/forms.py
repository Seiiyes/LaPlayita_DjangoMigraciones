from django import forms
from .models import Reabastecimiento, ReabastecimientoDetalle, Proveedor
from inventory.models import Producto

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['tipo_documento', 'documento_identificacion', 'nombre_empresa', 'telefono', 'correo', 'direccion']
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'documento_identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ReabastecimientoForm(forms.ModelForm):
    producto = forms.ModelChoiceField(queryset=Producto.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = Reabastecimiento
        fields = ['proveedor', 'forma_pago', 'estado', 'observaciones', 'producto']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'forma_pago': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ReabastecimientoDetalleForm(forms.ModelForm):
    class Meta:
        model = ReabastecimientoDetalle
        fields = ['producto', 'cantidad', 'costo_unitario', 'iva', 'fecha_caducidad']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control'}),
            'iva': forms.NumberInput(attrs={'class': 'form-control iva-field', 'style': 'display:none;'}),
            'fecha_caducidad': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date', 'format': '%Y-%m-%d'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_caducidad'].required = False
        self.fields['fecha_caducidad'].input_formats = ['%Y-%m-%d']

ReabastecimientoDetalleFormSet = forms.inlineformset_factory(
    Reabastecimiento,
    ReabastecimientoDetalle,
    form=ReabastecimientoDetalleForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    validate_min=False
)

# Formset para edición sin filas extras
ReabastecimientoDetalleFormSetEdit = forms.inlineformset_factory(
    Reabastecimiento,
    ReabastecimientoDetalle,
    form=ReabastecimientoDetalleForm,
    extra=0,
    can_delete=True,
    validate_min=False
)

class ProductoAjaxForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'precio_unitario', 'stock_minimo', 'descripcion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})