from django import forms
from .models import Providers

class ProviderForm(forms.ModelForm):
    class Meta:
        model = Providers
        fields = '__all__'

class EditProviderForm(forms.ModelForm):
    class Meta:
        model = Providers
        prov_status = forms.ChoiceField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])
        fields = '__all__'

