from io import StringIO
from urllib import request
from django.shortcuts import render, redirect, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import PayType, Providers, Invoice, InvoiceDetail
from django.db import connection
from .forms import EditProviderForm, ProviderForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from .models import Personal
from django.http.response import JsonResponse
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
import requests
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


from django.http import HttpResponse, JsonResponse

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
        try:
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True, 'message': 'Proveedor guardado exitosamente'})
            else:
                raise Exception("Formulario no válido. Corrige los errores.")
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
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

            if result and result[2] == password:
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

                return JsonResponse({'success': True, 'redirect_url': '/dashboard'})
            else:
                # Usuario no encontrado o contraseña incorrecta, mostrar error
                return JsonResponse({'success': False, 'error': 'Usuario o contraseña incorrectos.'})

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



    
def vista_factura(request):
    products = load_products()
    context = {'products': products}
    return render(request, 'detalle_factura.html', context)


def load_products():
    url = 'https://inventario-phue.onrender.com/inventario/products/'
    
    try:
        # Usa requests.get en lugar de urllib.request.get
        response = requests.get(url)
        
        if response.status_code == 200:
            response_buffer = StringIO(response.text)
            products = json.load(response_buffer)
            return products
        else:
            return f"Error en la solicitud: Código de estado {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {e}"

from django.http import JsonResponse


from .forms import ProviderSearchForm

def detalle(request):
    context = {'products': load_products()}  # Asegúrate de cargar los productos aquí también
    if request.method == 'GET':
        dni = request.GET.get('dni', '')
        provider = Providers.objects.filter(prov_dni=dni).first()

        if provider:
            context['provider'] = provider
        else:
            context['error'] = 'Proveedor no encontrado.'

    return render(request, 'detalle.html', context)



def consultar_facturas(request):
    # Obtener parámetros de fecha y tipo de pago de la URL
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")
    tipo_pago = request.GET.get("tipo_pago", "")

    # Mapear los valores de tipo de pago a los nuevos valores
    if tipo_pago == "credito":
        tipo_pago_valor = 1
    elif tipo_pago == "contado":
        tipo_pago_valor = 2
    else:
        tipo_pago_valor = None  # Puedes manejar otros casos según sea necesario

    # Construir la consulta ORM basada en los parámetros
    query = Q()
    if fecha_inicio:
        query &= Q(invo_date__gte=fecha_inicio)
        if fecha_fin:
            query &= Q(invo_date__lte=fecha_fin)
    if tipo_pago_valor is not None:
        query &= Q(invo_pay_type=tipo_pago_valor)

    # Imprimir la consulta SQL generada
    print(str(Invoice.objects.filter(query).query))

    # Ejecutar la consulta ORM
    facturas = Invoice.objects.filter(query)

    return render(request, "invoice_read.html", {"facturas": facturas})

def listarDetalleFactura(request, factura_id):
    # Obtener la instancia de Invoice
    factura = get_object_or_404(Invoice, invo_id=factura_id)

    # Obtener detalles de factura relacionados con la instancia de Invoice
    detalles = InvoiceDetail.objects.filter(invo_det_invo_id=factura)

    # Verificar que haya detalles disponibles
    if detalles.exists():
        # Obtener el primer detalle para obtener información de la factura
        primer_detalle = detalles.first()

        # Crear un diccionario con la información de la factura
        info_factura = {
            "cliente_nombre": primer_detalle.invo_det_invo_id.invo_prov_id.prov_name,
            "fecha": primer_detalle.invo_det_invo_id.invo_date,
            "tipo_pago": primer_detalle.invo_det_invo_id.invo_pay_type.pay_name,
            "fecha_expiracion": primer_detalle.invo_det_invo_id.expedition_date,
        }

        # Hacer una solicitud a la API para obtener los detalles de los productos
        api_url = "https://inventario-phue.onrender.com/inventario/products/"
        response = requests.get(api_url)

        # Verificar si la solicitud fue exitosa (código de estado 200)
        if response.status_code == 200:
            productos_api = response.json()  # Convertir la respuesta a formato JSON
        else:
            productos_api = []  # Manejar el caso en que la solicitud no fue exitosa

        # Combinar detalles de factura con datos de productos para la vista
        detalleFactura = [
            {
                "ivo_det_id": detalle.ivo_det_id,
                "prod_id": detalle.prod_id,  # Suponiendo que prod_id es la clave foránea a Product
                "quantity_invo_det": detalle.quantity_invo_det,
                "invo_det_invo_id": detalle.invo_det_invo_id.invo_id,
                "producto_nombre": get_producto_nombre(productos_api, detalle.prod_id),
                "precio_unidad": get_producto_precio(productos_api, detalle.prod_id),  # Modificar según la lógica de tu aplicación
                "precio_total": detalle.quantity_invo_det * get_producto_precio(productos_api, detalle.prod_id),  # Corregir aquí
            }
            for detalle in detalles
        ]

        # Agregar la información de la factura y los productos al contexto
        return render(
            request,
            "listarDetalleFactura.html",
            {"detalles": detalleFactura, "info_factura": info_factura, "productos_api": productos_api},
        )

    else:
        # Manejar el caso en que no haya detalles disponibles
        return render(
            request, "listarDetalleFactura.html", {"detalles": [], "info_factura": {}, "productos_api": []}
        )

# Funciones auxiliares para obtener nombre y precio del producto por ID
def get_producto_nombre(productos_api, prod_id):
    producto = next((p for p in productos_api if p["pro_id"] == prod_id), None)
    return producto["pro_name"] if producto else ""

def get_producto_precio(productos_api, prod_id):
    producto = next((p for p in productos_api if p["pro_id"] == prod_id), None)
    precio_str = producto["pro_cost"] if producto else "0"  # Considera un valor por defecto
    return float(precio_str)