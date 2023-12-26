from django.shortcuts import render, redirect, get_object_or_404, redirect
from django.views import View
from .models import PayType, Providers, Invoice, InvoiceDetail
from django.db import connection
from .forms import EditProviderForm, ProviderForm
from django.contrib import messages
# Create your views here.


def consultar_pago(request):
    resultados = PayType.objects.raw('SELECT pay_id, pay_name FROM public."Pay_type"')
    return render(request, 'consultar_pagos.html', {'resultados': resultados})

def consultar_proveedores(request):
    query = 'SELECT * FROM public.providers_select_all();'
    proveedores = Providers.objects.raw(query)
    return render(request, 'consultar_proveedores.html', {'proveedores': proveedores})

def editar_proveedor(request, prov_id):
    provider = get_object_or_404(Providers, prov_id=prov_id)

    if request.method == 'POST':
        form = EditProviderForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            print("Proveedor guardado exitosamente")  # Añade este print para verificar
            return redirect('consultar_proveedores')  # Cambiado a 'consultar_proveedores'
        else:
            print("Formulario no válido. Corrige los errores.")
    else:
        form = EditProviderForm(instance=provider)

    return render(request, 'editar_proveedor.html', {'form': form, 'provider': provider})

def insertar_proveedor(request):
    if request.method == 'POST':
        form = ProviderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('consultar_proveedores')  # Puedes redirigir a la página de consulta después de la inserción
    else:
        form = ProviderForm()

    return render(request, 'insertar_proveedor.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        # Lógica de autenticación aquí (por ahora, simplemente redireccionamos)
        return redirect('dashboard')
    else:
        return render(request, 'login.html')
    
def menu_view(request):
    return render(request, 'menu.html')

def dashboard_view(request):
    num_providers = Providers.objects.count()
    num_invoices = Invoice.objects.count()
    num_invoice_details = InvoiceDetail.objects.count()

    return render(request, 'dashboard.html', {
        'num_providers': num_providers,
        'num_invoices': num_invoices,
        'num_invoice_details': num_invoice_details,
    })


from rest_framework import generics
from .models import Providers
from .serializers import ProvidersSerializer

class ProvidersListCreateView(generics.ListCreateAPIView):
    queryset = Providers.objects.all()
    serializer_class = ProvidersSerializer


