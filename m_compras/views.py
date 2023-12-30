from django.shortcuts import render, redirect, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import PayType, Providers, Invoice, InvoiceDetail
from django.db import connection
from .forms import EditProviderForm, ProviderForm
from django.contrib import messages
# Create your views here.


def consultar_pago(request):
    resultados = PayType.objects.raw('SELECT pay_id, pay_name FROM public."Pay_type"')
    return render(request, 'consultar_pagos.html', {'resultados': resultados})

#def consultar_proveedores(request):
 #   query = 'SELECT * FROM public.providers_select_all();'
  #  proveedores = Providers.objects.raw(query)
   # return render(request, 'consultar_proveedores.html', {'proveedores': proveedores})

def consultar_proveedores(request):
    # Consulta SQL personalizada
    search_query = request.GET.get('search', '')
    base_query = 'SELECT * FROM public.providers_select_all()'
    if search_query:
        query = f'{base_query} WHERE prov_name ILIKE %s;'
        proveedores = Providers.objects.raw(query, [f'%{search_query}%'])
    else:
        query = base_query
        proveedores = Providers.objects.raw(query)

    # Configurar el paginador
    paginator = Paginator(list(proveedores), 8)  # Muestra 8 proveedores por página

    # Obtener el número de página de la solicitud GET
    page = request.GET.get('page')

    try:
        proveedores_paginados = paginator.page(page)
    except PageNotAnInteger:
        # Si la página no es un número entero, mostrar la primera página
        proveedores_paginados = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango (por encima del número total de páginas),
        # mostrar la última página
        proveedores_paginados = paginator.page(paginator.num_pages)

    return render(request, 'consultar_proveedores.html', {'proveedores': proveedores_paginados, 'search_query': search_query})


from django.http import JsonResponse

def editar_proveedor(request, prov_id):
    provider = get_object_or_404(Providers, prov_id=prov_id)

    if request.method == 'POST':
        form = EditProviderForm(request.POST, instance=provider)
        try:
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True})
            else:
                raise Exception("Formulario no válido. Corrige los errores.")
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

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


