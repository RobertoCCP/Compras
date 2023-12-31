from django.shortcuts import render, redirect, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import PayType, Providers, Invoice, InvoiceDetail
from django.db import connection
from .forms import EditProviderForm, ProviderForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .models import Personal
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
        username = request.POST.get('username')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, password FROM public.personal WHERE username=%s", [username])
            result = cursor.fetchone()

            if result and result[2] == password:  # Comparar contraseñas directamente
                # Usuario encontrado, iniciar sesión
                personal_id = result[0]

                # Registrar en el audit log al iniciar sesión
                action_type = 'LOGIN'
                user_id = personal_id
                ip_address = request.META.get('REMOTE_ADDR', None)
                table_name = 'personal'
                description = f"{action_type} - Usuario: {username}"
                function_name = 'function-1'  # Ajustar según sea necesario
                observation = 'Nada'

                cursor.execute(
                    "INSERT INTO audit_log (action_type, table_name, row_id, user_id, ip_address, description, function_name, observation) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    [action_type, table_name, user_id, user_id, ip_address, description, function_name, observation]
                )

                request.session['personal_id'] = user_id  # Almacenar el ID del usuario en la sesión

                return redirect('dashboard')
            else:
                # Usuario no encontrado o contraseña incorrecta, mostrar error
                return render(request, 'login.html', {'error': 'Usuario o contraseña incorrectos.'})

    # Si no es un POST, renderizar el formulario de inicio de sesión
    return render(request, 'login.html')


def logout_view(request):
    # Obtener el ID de personal de la sesión
    user_id = request.session.get('personal_id')

    # Registrar en el audit log antes de cerrar sesión
    action_type = 'LOGOUT'
    ip_address = request.META.get('REMOTE_ADDR', None)
    table_name = 'personal'
    description = f"{action_type} - Usuario ID: {user_id}" if user_id else f"{action_type}"
    function_name = 'function-2'  # Puedes ajustar según tus necesidades
    observation = 'Nada'

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO audit_log (action_type, table_name, row_id, user_id, ip_address, description, function_name, observation) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [action_type, table_name, user_id, user_id, ip_address, description, function_name, observation]
        )

    # Limpiar el ID de personal de la sesión al cerrar sesión
    del request.session['personal_id']

    return redirect('login')  # A
    
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


from django.views.generic.edit import CreateView
from .models import Providers

class ProviderCreateView(CreateView):
    model = Providers
    template_name = 'provider_form.html'
    fields = ['prov_name', 'prov_dni', 'prov_phone', 'prov_email', 'prov_city', 'prov_status', 'prov_type', 'prov_address']

    def form_valid(self, form):
        form.instance.save(user_id=self.request.user.id)  # Asegúrate de tener el usuario disponible en tu vista
        return super().form_valid(form)