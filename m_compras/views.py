from io import StringIO
from urllib import request
from django.shortcuts import render, redirect, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import PayType, Providers, Invoice, InvoiceDetail
from django.db import connection
from .forms import EditProviderForm, InvoiceForm, ProviderForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from .models import Personal
from django.http.response import JsonResponse
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
import requests
from django.http import JsonResponse
from .forms import InvoiceForm


# Create your views here.


def consultar_pago(request):
    resultados = PayType.objects.raw('SELECT pay_id, pay_name FROM public."Pay_type"')
    return render(request, "consultar_pagos.html", {"resultados": resultados})


# def consultar_proveedores(request):
#   query = 'SELECT * FROM public.providers_select_all();'
#  proveedores = Providers.objects.raw(query)
# return render(request, 'consultar_proveedores.html', {'proveedores': proveedores})


def consultar_proveedores(request):
    search_query = request.GET.get("search", "")
    orden = request.GET.get("ordenar", "prov_name")  # Orden por defecto

    # Mapeo de los campos para el ordenamiento
    campos_ordenamiento = {
        'nombre': 'prov_name',
        'dni': 'prov_dni',
        'telefono': 'prov_phone',
        'email': 'prov_email',
        'ciudad': 'prov_city',
        'estado': 'prov_status',
        'tipo': 'prov_type',
        'direccion': 'prov_address'
    }

    campo_orden_base = orden.replace('-', '')
    campo_orden = campos_ordenamiento.get(campo_orden_base, 'prov_name')
    direccion_orden = "DESC" if orden.startswith('-') else "ASC"

    base_query = "SELECT * FROM public.providers_select_all()"
    if search_query:
        query = f"{base_query} WHERE prov_name ILIKE %s ORDER BY {campo_orden} {direccion_orden};"
        proveedores = Providers.objects.raw(query, [f"%{search_query}%"])
    else:
        query = f"{base_query} ORDER BY {campo_orden} {direccion_orden};"
        proveedores = Providers.objects.raw(query)

    # Configurar el paginador
    paginator = Paginator(list(proveedores), 8)  # Muestra 8 proveedores por página

    # Obtener el número de página de la solicitud GET
    page = request.GET.get("page")

    try:
        proveedores_paginados = paginator.page(page)
    except PageNotAnInteger:
        proveedores_paginados = paginator.page(1)
    except EmptyPage:
        proveedores_paginados = paginator.page(paginator.num_pages)

    return render(
        request,
        "consultar_proveedores.html",
        {"proveedores": proveedores_paginados, "search_query": search_query},
    )

from django.http import HttpResponse, JsonResponse


def editar_proveedor(request, prov_id):
    provider = get_object_or_404(Providers, prov_id=prov_id)

    if request.method == "POST":
        form = EditProviderForm(request.POST, instance=provider)
        try:
            with transaction.atomic():
                if form.is_valid():
                    form.save()
                    return JsonResponse({"success": True, "message": "Proveedor actualizado exitosamente"})
                else:
                    error_message = "Error al validar el formulario. Corrige los errores."
                    return JsonResponse({"success": False, "error": error_message})
        except Exception as e:
            # Captura la excepción y devuelve solo el mensaje personalizado
            error_message = str(e)
            return JsonResponse({"success": False, "error": error_message})

    else:
        form = EditProviderForm(instance=provider)

    return render(
        request, "editar_proveedor.html", {"form": form, "provider": provider}
    )

from django.db import IntegrityError
from django.db import transaction

def insertar_proveedor(request):
    if request.method == "POST":
        form = ProviderForm(request.POST)
        try:
            with transaction.atomic():
                if form.is_valid():
                    form.save()
                    return JsonResponse(
                        {"success": True, "message": "Proveedor guardado exitosamente"}
                    )
                else:
                    error_message = "Error al validar el formulario. Corrige los errores."
                    return JsonResponse({"success": False, "error": error_message})
        except Exception as e:
            # Captura la excepción y devuelve solo el mensaje personalizado
            error_message = str(e)
            return JsonResponse({"success": False, "error": error_message})

    else:
        form = ProviderForm()

    return render(request, "insertar_proveedor.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password FROM public.personal WHERE username=%s",
                [username],
            )
            result = cursor.fetchone()

            if result and result[2] == password:
                # Usuario encontrado, iniciar sesión
                personal_id = result[0]

                # Registrar en el audit log al iniciar sesión
                action_type = "LOGIN"
                user_id = personal_id
                ip_address = request.META.get("REMOTE_ADDR", None)
                table_name = "personal"
                description = f"{action_type} - Usuario: {username}"
                function_name = "function-1"  # Ajustar según sea necesario
                observation = "Nada"

                cursor.execute(
                    "INSERT INTO audit_log (action_type, table_name, row_id, user_id, ip_address, description, function_name, observation) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    [
                        action_type,
                        table_name,
                        user_id,
                        user_id,
                        ip_address,
                        description,
                        function_name,
                        observation,
                    ],
                )

                request.session[
                    "personal_id"
                ] = user_id  # Almacenar el ID del usuario en la sesión

                return JsonResponse({"success": True, "redirect_url": "/dashboard"})
            else:
                # Usuario no encontrado o contraseña incorrecta, mostrar error
                return JsonResponse(
                    {"success": False, "error": "Usuario o contraseña incorrectos."}
                )

    # Si no es un POST, renderizar el formulario de inicio de sesión
    return render(request, "login.html")


def logout_view(request):
    # Obtener el ID de personal de la sesión
    user_id = request.session.get("personal_id")

    # Registrar en el audit log antes de cerrar sesión
    action_type = "LOGOUT"
    ip_address = request.META.get("REMOTE_ADDR", None)
    table_name = "personal"
    description = (
        f"{action_type} - Usuario ID: {user_id}" if user_id else f"{action_type}"
    )
    function_name = "function-2"  # Puedes ajustar según tus necesidades
    observation = "Nada"

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO audit_log (action_type, table_name, row_id, user_id, ip_address, description, function_name, observation) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [
                action_type,
                table_name,
                user_id,
                user_id,
                ip_address,
                description,
                function_name,
                observation,
            ],
        )

    # Limpiar el ID de personal de la sesión al cerrar sesión
    del request.session["personal_id"]

    return redirect("login")  # A


def menu_view(request):
    return render(request, "menu.html")


def dashboard_view(request):
    num_providers = Providers.objects.count()
    num_invoices = Invoice.objects.count()
    num_invoice_details = InvoiceDetail.objects.count()

    return render(
        request,
        "dashboard.html",
        {
            "num_providers": num_providers,
            "num_invoices": num_invoices,
            "num_invoice_details": num_invoice_details,
        },
    )


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
    template_name = "provider_form.html"
    fields = [
        "prov_name",
        "prov_dni",
        "prov_phone",
        "prov_email",
        "prov_city",
        "prov_status",
        "prov_type",
        "prov_address",
    ]

    def form_valid(self, form):
        form.instance.save(
            user_id=self.request.user.id
        )  # Asegúrate de tener el usuario disponible en tu vista
        return super().form_valid(form)


def vista_factura(request):
    products = load_products()
    context = {"products": products}
    return render(request, "detalle_factura.html", context)


def load_products():
    url = "https://inventario-phue.onrender.com/inventario/products/"

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


def consultar_facturas(request):
    search_query = request.GET.get("search", "")
    orden = request.GET.get("ordenar", "invo_date")  # Orden por defecto

    # Mapeo de los campos para el ordenamiento
    campos_ordenamiento = {
        'fecha': 'invo_date',
        'proveedor': 'invo_prov_id__prov_name',  # Asumiendo que prov_name es un campo de Providers
        'expiracion': 'expedition_date',
        'tipo': 'invo_pay_type',
    }

    campo_orden_base = orden.replace('-', '')
    campo_orden = campos_ordenamiento.get(campo_orden_base, 'invo_date')
    direccion_orden = "-" if orden.startswith('-') else ""

    # Construir la consulta
    if search_query:
        facturas_list = Invoice.objects.filter(
            # Asegúrate de ajustar los criterios de búsqueda según tus necesidades
            Q(invo_prov_id__prov_name__icontains=search_query) 
            #|  Q(otros_criterios_de_busqueda__icontains=search_query)
        ).order_by(direccion_orden + campo_orden)
    else:
        facturas_list = Invoice.objects.all().order_by(direccion_orden + campo_orden)

    # Configurar el paginador
    paginator = Paginator(facturas_list, 8)  # Cambia 10 por el número de elementos por página que prefieras

    # Obtener el número de página de la solicitud GET
    page = request.GET.get("page")

    try:
        facturas = paginator.page(page)
    except PageNotAnInteger:
        facturas = paginator.page(1)
    except EmptyPage:
        facturas = paginator.page(paginator.num_pages)

    return render(
        request,
        "invoice_read.html",
        {"facturas": facturas, "search_query": search_query, "orden_actual": orden},
    )


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
                "precio_unidad": get_producto_precio(
                    productos_api, detalle.prod_id
                ),  # Modificar según la lógica de tu aplicación
                "precio_total": detalle.quantity_invo_det
                * get_producto_precio(productos_api, detalle.prod_id),  # Corregir aquí
            }
            for detalle in detalles
        ]

        # Agregar la información de la factura y los productos al contexto
        return render(
            request,
            "listarDetalleFactura.html",
            {
                "detalles": detalleFactura,
                "info_factura": info_factura,
                "productos_api": productos_api,
            },
        )

    else:
        # Manejar el caso en que no haya detalles disponibles
        return render(
            request,
            "listarDetalleFactura.html",
            {"detalles": [], "info_factura": {}, "productos_api": []},
        )


# Funciones auxiliares para obtener nombre y precio del producto por ID
def get_producto_nombre(productos_api, prod_id):
    producto = next((p for p in productos_api if p["pro_id"] == prod_id), None)
    return producto["pro_name"] if producto else ""


def get_producto_precio(productos_api, prod_id):
    producto = next((p for p in productos_api if p["pro_id"] == prod_id), None)
    precio_str = (
        producto["pro_cost"] if producto else "0"
    )  # Considera un valor por defecto
    return float(precio_str)


def verificar_proveedor(request):
    dni = request.GET.get("dni", None)

    try:
        provider = Providers.objects.get(prov_dni=dni)
        data = {"prov_id": provider.prov_id}
        return JsonResponse(data)
    except Providers.DoesNotExist:
        error = {"error": "Proveedor no encontrado."}
        return JsonResponse(error)


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Invoice


def obtener_detalle_proveedor(request):
    if request.method == "GET":
        dni = request.GET.get("dni", None)

        if dni:
            try:
                # Buscar el proveedor por el DNI
                proveedor = Providers.objects.get(prov_dni=dni)
                # Aquí puedes agregar más campos según tu modelo Proveedor
                data = {
                    "prov_id": proveedor.prov_id,
                    "prov_pay_type": proveedor.prov_pay_type,
                    # Agrega más campos según sea necesario
                }
                return JsonResponse(data)
            except Providers.DoesNotExist:
                # Agrega un mensaje de registro para el caso de error
                print(f"Proveedor con DNI {dni} no encontrado")
                return JsonResponse({"error": "Proveedor no encontrado"}, status=404)

        # Agrega un mensaje de registro para el caso de parámetro DNI no proporcionado
        print("Parámetro DNI no proporcionado")
        return JsonResponse({"error": "Parámetro DNI no proporcionado"}, status=400)

    # Agrega un mensaje de registro para el caso de método no permitido
    print("Método no permitido")
    return JsonResponse({"error": "Método no permitido"}, status=405)


def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = request.POST.get("quantity", 1)

        # Lógica para agregar el producto al carrito
        # (Asegúrate de implementar esta lógica según tu modelo y requisitos)

        return redirect(
            "detalle"
        )  # Redirige a la página de detalle después de agregar al carrito
    else:
        return redirect(
            "detalle"
        )  # Manejar cualquier acceso GET de manera adecuada (puedes personalizar según tus necesidades)


# modulocompras/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import InvoiceForm
from .models import Providers


from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from .forms import InvoiceForm
from .models import Invoice, Providers


class Invoice_Insert(View):
    template_name = "invoice_insert.html"

    def get(self, request, *args, **kwargs):
        context = {"products": load_products()}
        dni = request.GET.get("dni", "")
        provider = Providers.objects.filter(prov_dni=dni).first()

        if provider:
            context["provider"] = provider
        else:
            context["error"] = "Proveedor no encontrado."

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {"products": load_products()}
        try:
            # Procesar el formulario de la factura
            form = InvoiceForm(request.POST)
            if form.is_valid():
                # Guardar la factura en la base de datos
                invoice = form.save()

                # Obtener el último ID de la factura recién creada
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT invo_id FROM public.invoice ORDER BY invo_id DESC LIMIT 1;"
                    )
                    last_invoice_id = cursor.fetchone()[0]

                # Imprimir el ID en la consola
                print(f"ID de la factura recién creada: {last_invoice_id}")

                # Verificar que el ID de la factura no sea None o una cadena vacía antes de redirigir

                if last_invoice_id:
                    # Agregar invo_id al contexto para que esté disponible en la plantilla
                    context["invo_id"] = last_invoice_id

                    # Redirigir a la página de detalles de la factura
                    return JsonResponse({"success": True, "invo_id": last_invoice_id})

                else:
                    context[
                        "error"
                    ] = "Error: el ID de la factura no está disponible o es None."
                    return JsonResponse({"success": False, "error": context["error"]})
            else:
                # Devolver errores de validación al cliente
                errors = form.errors.as_json()
                context["errors"] = errors
        except Exception as e:
            # Manejar cualquier error durante el proceso de guardado
            print(f"Error al guardar la factura: {e}")
            context["error"] = f"Error al guardar la factura: {e}"

        # Imprimir el contexto en la consola para obtener más información sobre el error
        print(context)

        # Agregar invo_id al contexto incluso si hay errores para asegurarse de que esté presente
        context["invo_id"] = None

        return render(request, self.template_name, context)


from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import Invoice, InvoiceDetail
import requests

# Importa el módulo logging
import logging

# Configura el logger
logger = logging.getLogger(__name__)


class Invoice_Detail_Insert_View(View):
    template_name = "invoice_detail_insert.html"

    def get(self, request, invo_det_invo_id=None, *args, **kwargs):
        # Aqui los campos para verificar
        # Imprimir o registrar el invo_det_invo_id para verificar
        logger.info(f"GET request received. invo_det_invo_id: {invo_det_invo_id}")

        # Obtener la factura recién creada
        invoice = get_object_or_404(Invoice, invo_id=invo_det_invo_id)
        # obtenemos los productos de la API
        try:
            response = requests.get(
                "https://inventario-phue.onrender.com/inventario/products/"
            )
            products = response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error al obtener productos desde la API: {e}")
            products = []

        # Asegurarse de que el contexto esté configurado según tus necesidades
        context = {
            "invo_det_invo_id": invo_det_invo_id,
            "products": products,
            "invoice": invoice,
        }

        return render(
            request, self.template_name, {"products": products, "error": None}
        )

    def post(self, request, *args, **kwargs):
        # Obtener el ID de la factura de la URL
        invo_det_invo_id = kwargs.get("invo_det_invo_id")
        invoice = get_object_or_404(Invoice, invo_id=invo_det_invo_id)
        print("Invoice ID:", invo_det_invo_id)  # Imprimir el valor para verificar
        print("Invoice:", invoice)  # Imprimir el valor para verificar



        try:
            # Intentar cargar los datos JSON
            data = json.loads(request.body)
            print("data",data)
        except json.JSONDecodeError as e:
            # Imprimir información detallada del error en la consola del servidor Django
            print(f"Error al procesar la solicitud: {e}")
            return JsonResponse({"error": "Error al procesar la solicitud"}, status=500)


        # Asegúrate de que 'products' esté presente en los datos
        if "products" not in data:
            return JsonResponse({"error": "No se proporcionaron productos"}, status=400)

        products_data = data["products"]

        print("Impresion de productos", products_data)  # Imprimir datos para verificar

        for product_info in products_data:
            product_id = product_info.get("prod_id")
            quantity = product_info.get(
                "prod_quantity"
            )  # Asegúrate de obtener la cantidad correcta

            # Crear un objeto InvoiceDetail y guardarlo en la base de datos
            invoice_detail = InvoiceDetail(
                prod_id=product_id,
                quantity_invo_det=quantity,
                invo_det_invo_id=invoice,
            )
            print(invoice_detail)
            invoice_detail.save()

        # Redirige a la misma vista después de procesar la solicitud POST
        return JsonResponse({"success": True})