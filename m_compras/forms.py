from django import forms
from .models import Providers, Invoice

class ProviderForm(forms.ModelForm):
    class Meta:
        model = Providers
        fields = '__all__'

class EditProviderForm(forms.ModelForm):
    class Meta:
        model = Providers
        prov_status = forms.ChoiceField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])
        fields = '__all__'

class ProviderSearchForm(forms.Form):
    dni = forms.CharField(label='DNI del proveedor')

class ProviderForm(forms.ModelForm):
    class Meta:
        model = Providers
        fields = '__all__'

class EditProviderForm(forms.ModelForm):
    class Meta:
        model = Providers
        prov_status = forms.ChoiceField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])
        fields = '__all__'

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = '__all__'

class ProveedorSearchForm(forms.Form):
    dni = forms.CharField(max_length=20, required=True, label='DNI del proveedor')

class EditInvoiceForm(forms.ModelForm):
    prov_status = forms.ChoiceField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])

    class Meta:
        model = Invoice
        fields = '__all__'

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invo_date', 'user_id', 'expedition_date', 'invo_prov_id', 'invo_pay_type']