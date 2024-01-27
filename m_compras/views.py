from io import StringIO
import locale
from turtle import color, left
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
        "nombre": "prov_name",
        "dni": "prov_dni",
        "telefono": "prov_phone",
        "email": "prov_email",
        "ciudad": "prov_city",
        "estado": "prov_status",
        "tipo": "prov_type",
        "direccion": "prov_address",
    }

    campo_orden_base = orden.replace("-", "")
    campo_orden = campos_ordenamiento.get(campo_orden_base, "prov_name")
    direccion_orden = "DESC" if orden.startswith("-") else "ASC"

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
    action = "Consultar Proveedores"
    function_name = "PRC-PROVIDERS-READ"  # Ajustar según sea necesario
    observation = ""
    auditar_modulo_compras(request,action,function_name,observation)
    return render(
        request,
        "consultar_proveedores.html",
        {"proveedores": proveedores_paginados, "search_query": search_query},
    )


from django.http import HttpResponse, JsonResponse


def editar_proveedor(request, prov_id):
    login_result = request.session.get('login_result', None)
    funciones  =login_result.get("data", {}).get("token")
    funcion= 'PRC-PROVIDERS-UPDATE'
    provider = get_object_or_404(Providers, prov_id=prov_id)
    if request.method == "POST":
        form = EditProviderForm(request.POST, instance=provider)
        if not permisos(request,'PRC-PROVIDERS-UPDATE'):
           return HttpResponseForbidden("No tienes permiso para acceder a esta función.")
        try:
            with transaction.atomic():
                if form.is_valid():
                    form.save()
                    action = "Editar Proveedores"
                    function_name = "PRC-PROVIDERS-UPDATE"  # Ajustar según sea necesario
                    observation =  f"Proveedor editado : {prov_id}"
                    auditar_modulo_compras(request,action,function_name,observation)
                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Proveedor actualizado exitosamente",
                        }
                    )
                else:
                    error_message = (
                        "Error al validar el formulario. Corrige los errores."
                    )
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
from django.http import HttpResponseForbidden
import urllib.request

def permisos(request, permisoRequerido):
    login_result = request.session.get('login_result', None)
    funciones = login_result.get("data", {}).get("functions", [])
    for permiso in funciones:
        if permiso == permisoRequerido:
            return True
    return False
def insertar_proveedor(request):
    if request.method == "POST":
        form = ProviderForm(request.POST)
        if not permisos(request,'PRC-PROVIDERS-CREATE'):
           return HttpResponseForbidden("No tienes permiso para acceder a esta función.")
        try:
            with transaction.atomic():
                if form.is_valid():
                    form.save()
                    action = "Crear Proveedores"
                    function_name = "PRC-PROVIDERS-CREATE"  # Ajustar según sea necesario
                    observation =  f"Proveedor creado "
                    auditar_modulo_compras(request,action,function_name,observation)
                    return JsonResponse(
                        {"success": True, "message": "Proveedor guardado exitosamente"}
                    )
                else:
                    error_message = (
                        "Error al validar el formulario. Corrige los errores."
                    )
                    return JsonResponse({"success": False, "error": error_message})
        except Exception as e:
            # Captura la excepción y devuelve solo el mensaje personalizado
            error_message = str(e)
            return JsonResponse({"success": False, "error": error_message})

    else:
        form = ProviderForm()

    return render(request, "insertar_proveedor.html", {"form": form})
def login2(request):
    if request.method == "POST":
        # Obtener las credenciales del formulario
        username = request.POST.get("username")
        password = request.POST.get("password")
        # Llamar a la función de inicio de sesión
        action = "LOGIN"
        function_name = "PRC-LOGIN"  # Ajustar según sea necesario
        observation = ""
        result = perform_login(username, password)
        if  result.get("success"):
            # Usuario autenticado con éxito, realizar acciones adicionales si es necesario
            request.session['login_result'] = result
            auditar_modulo_compras(request,action,function_name,observation)
            return JsonResponse({"success": True, "redirect_url": "/dashboard"})
        else:
            # Usuario no autenticado, devolver un mensaje de error
            return JsonResponse({"success": False, "error":'Credenciales incorrectas'})

    # Si no es un POST, renderizar el formulario de inicio de sesión
    return render(request, "login.html")

def perform_login(username, password):
    url = "https://security-module-utn.azurewebsites.net/api/auth"
    data = {
        "username": username,
        "password": password
    }
  
    try:
        # Usa requests.get en lugar de urllib.request.get
        response = requests.post(url, json=data)
        if response.status_code == 200 or response.status_code == 201:
            response_buffer = StringIO(response.text)
            result = json.load(response_buffer)
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": f"Error en la solicitud: Código de estado {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Error en la solicitud: {e}"}
def logout2(request):
    # Eliminar todas las variables de sesión relacionadas con el usuario
    request.session.clear()
    return redirect('login')
def auditar_modulo_compras( request,action ,functionName, observation):
    url = 'https://security-module-utn.azurewebsites.net/api/audit'
    login_result = request.session.get('login_result', None)
    token =login_result.get("data", {}).get("token")
    username= login_result.get("data", {}).get("username")
    description = f"{action} - Usuario: {username}"
    ip_address =  request.META.get("REMOTE_ADDR", None)
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json'
    }
    data = {
        'action': action,
        'description': description,
        'ip': ip_address,
        'functionName': functionName,
        'observation': observation
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(data)
            print('Datos de auditoría guardados correctamente:', result)
            return {"success": True, "data": result}
        else:
            print(f"Error en la solicitud: Código de estado {response.status_code}")
            return {"success": False, "error": f"Error en la solicitud: Código de estado {response.status_code}"}
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")
        return {"success": False, "error": f"Error en la solicitud: {e}"}

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



import requests
import json
from io import StringIO
# Variable global para almacenar la lista de productos
products_data = []

def load_products():
    global products_data

    url = "https://inventario-phue.onrender.com/inventario/products/"

    try:
        # Usa requests.get en lugar de urllib.request.get
        response = requests.get(url)

        if response.status_code == 200:
            response_buffer = StringIO(response.text)
            products_data = json.load(response_buffer)
            return products_data
        else:
            return f"Error en la solicitud: Código de estado {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {e}"


from django.http import JsonResponse

import json
from .forms import ProviderSearchForm
from datetime import datetime
from django.http import HttpResponse

from django.db import OperationalError, connections
from psycopg2 import OperationalError as Psycopg2OpError


def consultar_facturas(request):
    try:
        # Tu código que interactúa con la base de datos aquí
        search_query = request.GET.get("search", "")
        orden = request.GET.get("ordenar", "invo_date")  # Orden por defecto

        # Mapeo de los campos para el ordenamiento
        campos_ordenamiento = {
            "fecha": "invo_date",
            "proveedor": "invo_prov_id__prov_name",
            "expiracion": "expedition_date",
            "tipo": "invo_pay_type",
        }

        campo_orden_base = orden.replace("-", "")
        campo_orden = campos_ordenamiento.get(campo_orden_base, "invo_date")
        direccion_orden = "-" if orden.startswith("-") else ""

        # Obtener fechas del formulario
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")

        # Obtener tipo de pago del formulario
        tipo_pago = request.GET.get("type_pay")

        # Construir la consulta
        facturas_list = Invoice.objects.all()

        if fecha_inicio and fecha_fin:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            facturas_list = facturas_list.filter(
                invo_date__range=(fecha_inicio, fecha_fin)
            )

        if tipo_pago:
            tipo_pago_valor = 1 if tipo_pago == "credito" else 2
            facturas_list = facturas_list.filter(invo_pay_type=tipo_pago_valor)

        if search_query:
            facturas_list = facturas_list.filter(
                Q(invo_prov_id__prov_name__icontains=search_query)
                # Agrega otros criterios de búsqueda según tus necesidades
            )

        facturas_list = facturas_list.order_by(direccion_orden + campo_orden)

        # Configurar el paginador
        paginator = Paginator(facturas_list, 8)

        # Obtener el número de página de la solicitud GET
        page = request.GET.get("page")

        try:
            facturas = paginator.page(page)
        except PageNotAnInteger:
            facturas = paginator.page(1)
        except EmptyPage:
            facturas = paginator.page(paginator.num_pages)

        if not facturas_list.exists():
            mensaje = "No hay facturas que coincidan con los criterios de búsqueda."

            if fecha_inicio and fecha_fin and tipo_pago:
                mensaje = f"No hay facturas con tipo de pago '{tipo_pago}' en el rango de fechas proporcionado."
            elif fecha_inicio and fecha_fin:
                mensaje = "No hay facturas en el rango de fechas proporcionado."
            elif tipo_pago:
                mensaje = f"No hay facturas con tipo de pago '{tipo_pago}'."

            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return HttpResponse(
                    json.dumps({"mensaje": mensaje}), content_type="application/json"
                )

            # Muestra el mensaje de alerta
            return render(request, "invoice_read.html", {"mensaje_alerta": mensaje})
        action = "Consultar Facturas"
        function_name = "PRC-INVOICE-READ"  # Ajustar según sea necesario
        observation = ""
        auditar_modulo_compras(request,action,function_name,observation)
        return render(
            request,
            "invoice_read.html",
            {"facturas": facturas, "search_query": search_query, "orden_actual": orden},
        )

    except (OperationalError, Psycopg2OpError) as e:
        # Manejar la desconexión de la base de datos
        connection = connections["default"]
        connection.close()
        connection.connect()


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from .models import Invoice, InvoiceDetail
import requests


def listarDetalleFactura(request, factura_id):
    # Obtener la instancia de Invoice
    factura = get_object_or_404(Invoice, invo_id=factura_id)

    # Obtener detalles de factura relacionados con la instancia de Invoice
    detalles = InvoiceDetail.objects.filter(invo_det_invo_id=factura)

    # Verificar que haya detalles disponibles
    if detalles.exists():
        # Obtener el primer detalle para obtener información de la factura
        primer_detalle = detalles.first()
        action = "Consultar detalle de facturas"
        function_name = "PRC-INVOICE-READ"  # Ajustar según sea necesario
        observation = ""
        auditar_modulo_compras(request,action,function_name,observation)
        # Crear un diccionario con la información de la factura
        info_factura = {
            "invo_id": factura.invo_id,
            "cliente_nombre": primer_detalle.invo_det_invo_id.invo_prov_id.prov_name,
            "fecha": primer_detalle.invo_det_invo_id.invo_date,
            "tipo_pago": primer_detalle.invo_det_invo_id.invo_pay_type.pay_name,
            "fecha_expiracion": primer_detalle.invo_det_invo_id.expedition_date,
        }
        print(f"Invoice ID: {factura.invo_id}")
        print(f"Invoice ID2: {primer_detalle.invo_det_invo_id}")

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
                "precio_unidad": get_producto_precio(productos_api, detalle.prod_id),
                "precio_total": detalle.quantity_invo_det
                * get_producto_precio(productos_api, detalle.prod_id),
                "producto_iva": get_producto_iva(productos_api, detalle.prod_id),
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
    precio_str = producto["pro_cost"] if producto else "0"
    return float(precio_str)


# Funciones auxiliares para obtener nombre y precio del producto por ID
def get_producto_iva(productos_api, prod_id):
    producto = next((p for p in productos_api if p["pro_id"] == prod_id), None)
    return producto["pro_iva"] if producto else ""


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
                action = "Crear Factura"
                function_name = "PRC-INVOICE-CREATE"  # Ajustar según sea necesario
                observation = ""
                auditar_modulo_compras(request, action,function_name,observation)
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
            print("data", data)
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
            action = "Crear Detalle Factura"
            function_name = "PRC-INVOICE_DETAIL-CREATE"  # Ajustar según sea necesario
            observation = ""
            auditar_modulo_compras(request, action,function_name,observation)
            invoice_detail.save()

        # Redirige a la misma vista después de procesar la solicitud POST
        return JsonResponse({"success": True})


from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from .models import Providers
from django.templatetags.static import static
from reportlab.lib.colors import orange

def split_text(text, max_length):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

class PDFWithCode128(SimpleDocTemplate):
    def __init__(self, buffer, **kwargs):
        super().__init__(buffer, **kwargs)
        self.styles = getSampleStyleSheet()

def reporte_proveedores(request):
    # Obtén los datos de la base de datos (supongamos que tienes un modelo llamado Providers)
    proveedores = Providers.objects.all()

    # Crear el objeto BytesIO para almacenar el PDF
    buffer = BytesIO()

    # Establecer el margen izquierdo y derecho en 1 cm
    margen_izquierdo = 35
    margen_derecho = 35

    # Crear el objeto PDF usando ReportLab con ajuste de margen izquierdo y derecho
    pdf = PDFWithCode128(buffer, pagesize=letter, rightMargin=margen_derecho, leftMargin=margen_izquierdo, topMargin=72, bottomMargin=18)

    # Configurar el estilo del documento
    styles = getSampleStyleSheet()

    # Agregar contenido al PDF
    contenido = []

    imagen_fondo = request.build_absolute_uri(static('images/f.jpg'))

    # Agregar la imagen como fondo en cada página
    def draw_background(canvas, doc):
        canvas.saveState()
        canvas.drawImage(imagen_fondo, 0, 0, width=doc.pagesize[0], height=doc.pagesize[1])
        canvas.restoreState()

        # Texto "Nombre de la Empresa" en el centro de la hoja
    nombre_empresa_texto = "Modulo de compras"  # Reemplaza con el nombre real de tu empresa
    nombre_empresa_style = ParagraphStyle(
        'NombreEmpresaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',  # Ajusta según la fuente "Poppins-Bold"
        fontSize=18,  # Ajusta el tamaño de la fuente según tu preferencia
        alignment=0,  # 0 representa la alineación a la izquierda
        textColor=orange,  # Color del texto (naranja en este caso)
        spaceAfter=6,  # Espacio después del párrafo (puedes ajustarlo según tu preferencia)
        spaceBefore=6,  # Espacio antes del párrafo (puedes ajustarlo según tu preferencia)
        bold=True,  # Texto en negrita # 1 representa la alineación al centro
    )
    contenido.append(Spacer(1, 10))
    contenido.append(Paragraph(nombre_empresa_texto, nombre_empresa_style))

    impreso_texto = "Impreso por administrador"
    impreso_style = ParagraphStyle(
        'ImpresoStyle',
        parent=styles['Normal'],
        fontName='Courier',  # Puedes ajustar el tipo de letra según tu preferencia
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        alignment=0,  # 0 representa la alineación a la izquierda
    )
    contenido.append(Spacer(1, 10))
    contenido.append(Paragraph(impreso_texto, impreso_style))

    # Configura el idioma para obtener la fecha en español
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    # Fecha y hora a la izquierda, debajo del texto "Impreso por el administrador"
    fecha = datetime.now().strftime('%d de %B de %Y')
    hora = datetime.now().strftime('%I:%M %p')
    fecha_hora_texto = f"{fecha}, {hora}"
    fecha_hora_style = ParagraphStyle(
        'FechaHoraStyle',
        parent=styles['Normal'],
        fontName='Courier',  # Puedes ajustar el tipo de letra según tu preferencia
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        alignment=0,  # 0 representa la alineación a la izquierda
    )
    contenido.append(Spacer(1, 5))  # Separación pequeña
    contenido.append(Paragraph(fecha_hora_texto, fecha_hora_style))

    # Número de factura en la parte superior izquierda
    numero_factura = obtener_numero_factura()  # Implementa la lógica para obtener el número de factura
    numero_factura_style = ParagraphStyle(
        'NumeroFacturaStyle',
        parent=styles['BodyText'],
        fontName='Courier',  # Puedes ajustar el tipo de letra según tu preferencia
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        alignment=0,  # 0 representa la alineación a la izquierda
        spaceBefore=5,  # Espacio antes del párrafo
    )
    contenido.append(Paragraph(f"<b>Número de factura:</b> {numero_factura}", numero_factura_style))

    # Texto "Reporte de Proveedores" en el centro
    reporte_texto = "Reporte de Proveedores"
    reporte_style = ParagraphStyle(
        'ReporteStyle',
        parent=styles['Heading1'],  # Puedes ajustar el estilo según tu preferencia
        fontName='Courier',  # Puedes ajustar el tipo de letra según tu preferencia
        fontSize=16,  # Ajusta el tamaño de la fuente según tu preferencia
        alignment=1,  # 1 representa la alineación al centro
        spaceBefore=20,  # Espacio antes del párrafo
        spaceAfter=20,  # Espacio después del párrafo
        textColor=orange,  # Puedes ajustar el color del texto
        BOLD = True,
    )
    contenido.append(Paragraph(reporte_texto, reporte_style))

    # Datos del cliente en una tabla adaptable
    datos_cliente = [["Nombre", "DNI", "Teléfono", "Email", "Ciudad", "Estado", "Tipo", "Dirección"]]
    max_length = 20  # Máximo de caracteres por línea

    for proveedor in proveedores:
        datos_cliente.append([
            "\n".join(split_text(proveedor.prov_name, max_length)),
            "\n".join(split_text(proveedor.prov_dni, max_length)),
            "\n".join(split_text(proveedor.prov_phone, max_length)),
            "\n".join(split_text(proveedor.prov_email, max_length)),
            "\n".join(split_text(proveedor.prov_city, max_length)),
            "\n".join(split_text("ACTIVO" if proveedor.prov_status else "INACTIVO", max_length)),
            proveedor.get_prov_type_display(),
            "\n".join(split_text(proveedor.prov_address, max_length)),
            ])

    # Estilo de la tabla de datos del cliente con letra más pequeña
    style_datos_cliente = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Centrar verticalmente
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Ajuste de línea automático
    ])

    tabla_cliente = Table(datos_cliente, style=style_datos_cliente)
    contenido.append(Spacer(1, 20))
    contenido.append(tabla_cliente)

    # Totales en la parte inferior derecha
    total_proveedores = len(proveedores)
    total_creditos = proveedores.filter(prov_type=1).count()
    total_contado = proveedores.filter(prov_type=2).count()

        # Estilo para los totales de proveedores
    total_proveedores_style = ParagraphStyle(
        'TotalProveedoresStyle',
        parent=styles['Heading2'],
        fontName='Courier-Bold',  # Ajusta el tipo de letra según tu preferencia
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        spaceBefore=20,  # Espacio antes del párrafo
        spaceAfter=1,   # Espacio después del párrafo (ajusta según sea necesario)
        textColor=colors.black,  # Ajusta el color del texto a negro
        alignment=2,  # Alineación a la derecha
    )

    # Párrafo para el total de proveedores
    total_proveedores_texto = f"Total de proveedores: {total_proveedores}"
    total_proveedores_paragraph = Paragraph(total_proveedores_texto, total_proveedores_style)
    contenido.append(Spacer(1, 1))  # Ajusta el espacio según sea necesario
    contenido.append(total_proveedores_paragraph)

    # Estilo para los totales de créditos de proveedores
    total_creditos_style = ParagraphStyle(
        'TotalCreditosStyle',
        parent=styles['Heading2'],
        fontName='Courier-Bold',  # Ajusta el tipo de letra según tu preferencia
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        spaceBefore=1,  # Espacio antes del párrafo
        spaceAfter=1,   # Espacio después del párrafo (ajusta según sea necesario)
        textColor=colors.black,  # Ajusta el color del texto a negro
        alignment=2,  # Alineación a la derecha
    )

    # Párrafo para el total de créditos de proveedores
    total_creditos_texto = f"Crédito de los proveedores: {total_creditos}"
    total_creditos_paragraph = Paragraph(total_creditos_texto, total_creditos_style)
    contenido.append(Spacer(1, 1))  # Ajusta el espacio según sea necesario
    contenido.append(total_creditos_paragraph)

    # Estilo para los totales de proveedores contado
    total_contado_style = ParagraphStyle(
        'TotalContadoStyle',
        parent=styles['Heading2'],
        fontName='Courier-Bold',  # Ajusta el tipo de letra según tu preferencia
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        spaceBefore=1,  # Espacio antes del párrafo
        spaceAfter=1,   # Espacio después del párrafo (ajusta según sea necesario)
        textColor=colors.black,  # Ajusta el color del texto a negro
        alignment=2,  # Alineación a la derecha
    )

    # Párrafo para el total de proveedores contado
    total_contado_texto = f"Contado de los proveedores: {total_contado}"
    total_contado_paragraph = Paragraph(total_contado_texto, total_contado_style)
    contenido.append(Spacer(1, 1))  # Ajusta el espacio según sea necesario
    contenido.append(total_contado_paragraph)

    # Agregar una línea de firma
    firma_texto = "Firma: ____________________________"
    firma_style = ParagraphStyle(
        'FirmaStyle',
        parent=styles['Italic'],
        fontName='Courier',  # Puedes ajustar el tipo de letra según tu preferencia
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        alignment=1,  # Alineación al centro
        spaceBefore=10,  # Espacio antes del párrafo
    )

    firma_paragraph = Paragraph(firma_texto, firma_style)
    contenido.append(firma_paragraph)

    # ...

    # Estilo para la nota en la parte inferior central
    nota_style = ParagraphStyle(
        'NotaStyle',
        parent=styles['Italic'],
        fontName='Courier',  # Puedes ajustar el tipo de letra según tu preferencia
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        alignment=1,  # Alineación al centro
        spaceBefore=5,  # Espacio antes del párrafo
    )

    # Párrafo para la nota
    nota_texto = "<i>Nota: Los proveedores existentes son aprobados por el administrador.</i>"
    contenido.append(Spacer(1, 5))
    contenido.append(Paragraph(nota_texto, nota_style))

    # Construye el documento
    pdf.build(contenido, onFirstPage=draw_background)

    # Establece el puntero del búfer al principio
    buffer.seek(0)

    # Crea una respuesta HTTP con el contenido del PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=reporte_proveedores.pdf"
    response.write(buffer.getvalue())

    return response


from .models import NumeroFactura
from django.db import transaction

def obtener_numero_factura():
    with transaction.atomic():
        # Utilizamos select_for_update para evitar problemas de concurrencia
        numero_factura_obj, creado = NumeroFactura.objects.select_for_update().get_or_create(id=1)

        if not creado:
            # Si no es la primera vez, incrementar el número de factura en 1
            numero_factura_obj.numero += 1
            numero_factura_obj.save()

        # Devolver el número de factura actualizado
        return numero_factura_obj.numero


from django.shortcuts import render
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import Invoice, InvoiceDetail
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime, timedelta

def generar_pdf(request, invoice_id):
    # Obtén los productos de la API
    try:
        response = requests.get("https://inventario-phue.onrender.com/inventario/products/")
        products = response.json() if response.status_code == 200 else []
    except Exception as e:
        print(f"Error al obtener productos desde la API: {e}")
        products = []

    try:
        factura = Invoice.objects.get(invo_id=invoice_id)
        detalles = InvoiceDetail.objects.filter(invo_det_invo_id=factura)
    except (Invoice.DoesNotExist, InvoiceDetail.DoesNotExist) as e:
        return HttpResponse("Error: La factura o los detalles no existen.")


       # Configuración del documento PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{invoice_id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
        # Configurar el estilo del documento
    styles = getSampleStyleSheet()

    # Contenido del PDF
    story = []
    subtotal_sin_impuestos, iva12, valor_total = calcular_totales(detalles, products)

    imagen_fondo = request.build_absolute_uri(static('images/f.jpg'))

    # Agregar la imagen como fondo en cada página
    def draw_background(canvas, doc):
        canvas.saveState()
        canvas.drawImage(imagen_fondo, 0, 0, width=doc.pagesize[0], height=doc.pagesize[1])
        canvas.restoreState()

    # Estilo personalizado para el título del documento
    titulo_documento_style = ParagraphStyle(
        'TituloDocumentoStyle',
        parent=styles['Heading1'],
        fontName='Courier',  # Ajusta según la fuente "Poppins-Bold"
        fontSize=20,  # Ajusta el tamaño de la fuente según tu preferencia
        textColor=orange,  # Color del texto (naranja en este caso)
        spaceAfter=12,  # Espacio después del párrafo (puedes ajustarlo según tu preferencia)
        bold=True,  # Texto en negrita
        alignment=0,
    )

    # Estilo personalizado para el subtítulo del documento
    subtitulo_documento_style = ParagraphStyle(
        'SubtituloDocumentoStyle',
        parent=styles['BodyText'],
        fontName='Courier',  # Ajusta según la fuente "Poppins-Bold"
        fontSize=16,  # Ajusta el tamaño de la fuente según tu preferencia
        textColor=orange,  # Color del texto (naranja en este caso)
        spaceAfter=12,  # Espacio después del párrafo (puedes ajustarlo según tu preferencia)
        bold=True,  # Texto en negrita
        alignment=0,
    )

    # Estilo personalizado para el texto del cuerpo del documento
    cuerpo_documento_style = ParagraphStyle(
        'CuerpoDocumentoStyle',
        parent=styles['BodyText'],
        fontName='Courier',  # Ajusta según la fuente "Poppins-Regular"
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        textColor=colors.black,  # Color del texto (ajusta según tu preferencia)
        spaceAfter=12,  # Espacio después del párrafo (puedes ajustarlo según tu preferencia)
        spaceBefore=6,  # Espacio antes del párrafo (puedes ajustarlo según tu preferencia)
        alignment=0,
    )

    # Ahora puedes usar estos estilos en tu código
    story.append(Paragraph("LOGO DE LA EMPRESA", titulo_documento_style))
    story.append(Paragraph("MÓDULO DE COMPRAS", subtitulo_documento_style))
    story.append(Paragraph("Av. 17 de julio, FICA", cuerpo_documento_style))

    # Configura el idioma para obtener la fecha en español
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    # Fecha y hora a la izquierda, debajo del texto "Impreso por el administrador"
    fecha = datetime.now().strftime('%d de %B de %Y')
    hora = datetime.now().strftime('%I:%M %p')
    fecha_hora_texto = f"Fecha de impresión: {fecha}, {hora}"
    fecha_hora_style = ParagraphStyle(
        'FechaHoraStyle',
        parent=styles['BodyText'],
        fontName='Courier',  # Puedes ajustar el tipo de letra según tu preferencia
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        alignment=0,  # 0 representa la alineación a la izquierda
        spaceBefore=-12,
    )
    story.append(Spacer(1, 5))  # Separación pequeña
    story.append(Paragraph(fecha_hora_texto, fecha_hora_style))


    # Información del cliente
    story.append(Spacer(1, 12))  # Espacio en blanco
    story.append(Paragraph("Información del Cliente", subtitulo_documento_style))
    story.append(Paragraph(f"Nombre del Cliente: {factura.invo_prov_id.prov_name}", cuerpo_documento_style))
    story.append(Paragraph(f"Dirección del Cliente: {factura.invo_prov_id.prov_address}", cuerpo_documento_style))
    story.append(Paragraph(f"Número de Teléfono: {factura.invo_prov_id.prov_phone}", cuerpo_documento_style))

        # Estilo personalizado para los detalles adicionales de la factura
    detalles_factura_style = ParagraphStyle(
        'DetallesFacturaStyle',
        parent=styles['BodyText'],
        fontName='Courier',  # Ajusta según la fuente "Poppins-Bold"
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        textColor=orange,  # Color del texto (naranja en este caso)
        spaceAfter=6,  # Espacio después del párrafo (puedes ajustarlo según tu preferencia)
        bold=True,  # Texto en negrita
        alignment=2,
    )

            # Estilo personalizado para los detalles adicionales de la factura
    tipo_style = ParagraphStyle(
        'TipoStyle',
        parent=styles['BodyText'],
        fontName='Courier',  # Ajusta según la fuente "Poppins-Regular"
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        textColor=colors.black,  # Color del texto (ajusta según tu preferencia)
        alignment=2,
    )

    # Detalles adicionales de la factura
    story.append(Spacer(1, -100))  # Espacio en blanco
    story.append(Paragraph("Detalles Adicionales", detalles_factura_style))
    story.append(Paragraph(f"Tipo de Pago: {factura.invo_pay_type.pay_name}",  tipo_style))

    if factura.invo_pay_type.pay_name == 'Contado':
        story.append(Paragraph(f"Fecha de Expiración: {factura.expedition_date or 'Desconocida'}",  tipo_style))

    # Información de la compra (tabla)
    story.append(Spacer(1, 50))  # Espacio en blanco
    story.append(Paragraph("Información de la Compra", subtitulo_documento_style))

    data = [['SL', 'Descripción del Producto', 'Precio', 'Cantidad', 'Impuesto', 'Total']]

    sl = 1
    for detalle in detalles:
        prod_name = get_producto_nombre(products, detalle.prod_id)
        prod_pvp = get_producto_precio(products, detalle.prod_id)
        prod_iva = get_producto_iva(products, detalle.prod_id)
        precio_total = detalle.quantity_invo_det * prod_pvp

        data.append([sl, prod_name, f"${prod_pvp:.2f}", detalle.quantity_invo_det, f"${prod_iva:.2f}", f"${precio_total:.2f}"])
        sl += 1

    # Estilo de la tabla
    style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Courier'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),  # Ajusta el relleno izquierdo
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),])

    # Construir la tabla y aplicar el estilo
    compra_table = Table(data)
    compra_table.setStyle(style)

    story.append(compra_table)

        # Estilo personalizado para los detalles adicionales de la factura
    totales_factura_style = ParagraphStyle(
        'DetallesFacturaStyle',
        parent=styles['Heading2'],
        fontName='Courier',  # Ajusta según la fuente "Poppins-Bold"
        fontSize=10,  # Ajusta el tamaño de la fuente según tu preferencia
        textColor=orange,  # Color del texto (naranja en este caso)
        spaceAfter=6,  # Espacio después del párrafo (puedes ajustarlo según tu preferencia)
        bold=True,  # Texto en negrita
        alignment=2,
    )
    # Totales
    story.append(Spacer(1, 12))  # Espacio en blanco
    story.append(Paragraph("Totales", totales_factura_style))

    # Ajustar el estilo para justificar a la derecha
    subtotal_sin_impuestos_style = ParagraphStyle(
        'SubtotalSinImpuestosStyle',
        parent=getSampleStyleSheet()['BodyText'],
        spaceAfter=8, 
        borderPadding=(5, 5, 5, 5),
        borderColor=colors.orange,
        borderWidth=1,
        alignment=2,  # Alinea a la derecha
        leftIndent=300,
        fontName='Courier', 
    )
    iva12_style = ParagraphStyle(
        'IVA12Style',
        borderPadding=(5, 5, 5, 5),
        spaceAfter=8, 
        borderColor=colors.orange,
        borderWidth=1,
        alignment=2,  # Alinea a la derecha
        leftIndent=300,
        fontName='Courier', 
    )
    valor_total_style = ParagraphStyle(
        'ValorTotalStyle',
        parent=getSampleStyleSheet()['BodyText'],
        spaceAfter=8, 
        borderPadding=(5, 5, 5, 5),
        borderColor=colors.orange,
        borderWidth=1,
        alignment=2,  # Alinea a la derecha
        leftIndent=300,
        fontName='Courier', 
    )

    story.append(Paragraph(f"Subtotal sin impuestos: {subtotal_sin_impuestos:.2f}", subtotal_sin_impuestos_style))
    story.append(Paragraph(f"IVA 12%: {iva12:.2f}", iva12_style))
    story.append(Paragraph(f"Valor Total: {valor_total:.2f}", valor_total_style))

    # Obtener la fecha de expiración desde tu objeto 'factura' (asegúrate de que sea un objeto de tipo datetime)
    fecha_expiracion = factura.expedition_date or None

    # Convertir la cadena 'fecha_hora_texto' a un objeto datetime
    fecha_hora_texto_datetime = datetime.strptime(fecha_hora_texto, "Fecha de impresión: %d de %B de %Y, %I:%M %p")

    # Convertir la fecha de expiración a datetime si no es None
    fecha_expiracion_datetime = datetime.combine(fecha_expiracion, datetime.min.time()) if fecha_expiracion else None

    # Calcular la diferencia en días entre la fecha de expiración y la fecha de impresión
    diferencia_dias = (fecha_expiracion_datetime - fecha_hora_texto_datetime).days if fecha_expiracion_datetime else None

    # Mensaje según la diferencia de días
    if diferencia_dias is not None and diferencia_dias > 0:
        mensaje_pago = f"El pago se efectuará en {diferencia_dias} días."
    elif diferencia_dias == 0:
        mensaje_pago = "Hoy es el último día para realizar el pago."
    else:
        mensaje_pago = "Plazo finalizado."

    story.append(Spacer(1, 12))  # Espacio en blanco
    story.append(Paragraph("Condiciones de Pago", detalles_factura_style))
    story.append(Paragraph(mensaje_pago, valor_total_style))

    # Construir el PDF
    doc.build(story, onFirstPage=draw_background)

    return response


def calcular_totales(detalles, products):
    subtotal_sin_impuestos = 0
    iva12 = 0

    for detalle in detalles:
        # Calcula el precio total directamente desde el detalle sin acceder a atributos no existentes
        precio_total = detalle.quantity_invo_det * get_producto_precio(products, detalle.prod_id)

        graba_iva = get_producto_iva(products, detalle.prod_id)

        if not isinstance(precio_total, (int, float)):
            continue

        subtotal_sin_impuestos += precio_total
        if graba_iva:
            iva12 += precio_total * 0.12

    valor_total = subtotal_sin_impuestos + iva12

    return subtotal_sin_impuestos, iva12, valor_total

