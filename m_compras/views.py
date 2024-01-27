from io import StringIO
from turtle import color
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
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from .models import (
    Personal,
)  # Asegúrate de importar el modelo Personal desde tu aplicación


def reporte_proveedores(request):
    # Obtén los datos de la base de datos (supongamos que tienes un modelo llamado Proveedor)
    proveedores = Providers.objects.all()

    # Crea el objeto BytesIO para almacenar el PDF
    buffer = BytesIO()

    # Crea el objeto PDF usando reportlab
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Configuración del estilo del documento
    styles = getSampleStyleSheet()
    style_heading = styles["Heading1"]
    style_body = styles["BodyText"]

    # Agrega contenido al PDF
    contenido = []

    # Agrega el encabezado con el título y la fecha
    titulo = "Reporte de Proveedores"
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    contenido.append(Paragraph(titulo, style_heading))
    contenido.append(Paragraph(f"Fecha de impresión: {fecha_actual}", style_body))

    # Datos de la empresa y usuario que imprime (basados en el nombre de usuario)
    # Asegúrate de ajustar los nombres de los campos según tu modelo de Personal
    contenido.append(Paragraph(f"Empresa: COMPRAS", style_body))

    # Agrega espacio en blanco
    contenido.append(Spacer(1, 12))

    # Crea una lista de datos para la tabla
    data = [
        ["Nombre", "DNI", "Teléfono", "Email", "Ciudad", "Estado", "Tipo", "Dirección"]
    ]

    for proveedor in proveedores:
        data.append(
            [
                proveedor.prov_name,
                proveedor.prov_dni,
                proveedor.prov_phone,
                proveedor.prov_email,
                proveedor.prov_city,
                proveedor.prov_status,
                proveedor.get_prov_type_display(),
                proveedor.prov_address,
            ]
        )

        # Crea la tabla y aplica estilos
        tabla = Table(data)
        tabla.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.orange,
                    ),  # Color de fondo para la fila de encabezado
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, 0),
                        6,
                    ),  # Reducir el espacio entre el texto y la celda superior
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),  # Establecer el tamaño de la letra en 8 puntos
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),  # Añadir un margen izquierdo de 12 puntos
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),  # Añadir un margen derecho de 12 puntos
                ]
            )
        )

    # Agrega la tabla al contenido
    contenido.append(tabla)

    # Agrega espacio en blanco
    contenido.append(Spacer(1, 12))

    # Agrega espacio para firmas
    contenido.append(Paragraph("Firmas:", style_body))

    # Construye el documento
    doc.build(contenido)

    # Establece el puntero del búfer al principio
    buffer.seek(0)

    # Crea una respuesta HTTP con el contenido del PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=reporte_proveedores.pdf"
    response.write(buffer.getvalue())

    return response


from django.shortcuts import render
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import Invoice, InvoiceDetail
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

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

    # Contenido del PDF
    story = []
    subtotal_sin_impuestos, iva12, valor_total = calcular_totales(detalles, products)
    # Encabezado
    story.append(Paragraph("LOGO DE LA EMPRESA", getSampleStyleSheet()['Heading1']))
    story.append(Paragraph("Nombre de la Empresa", getSampleStyleSheet()['Heading2']))
    story.append(Paragraph("Dirección de la Empresa", getSampleStyleSheet()['BodyText']))

    # Información del cliente
    story.append(Spacer(1, 12))  # Espacio en blanco
    story.append(Paragraph("Información del Cliente", getSampleStyleSheet()['Heading2']))
    story.append(Paragraph(f"Nombre del Cliente: {factura.invo_prov_id.prov_name}", getSampleStyleSheet()['BodyText']))
    story.append(Paragraph(f"Dirección del Cliente: {factura.invo_prov_id.prov_address}", getSampleStyleSheet()['BodyText']))
    story.append(Paragraph(f"Número de Teléfono: {factura.invo_prov_id.prov_phone}", getSampleStyleSheet()['BodyText']))

    # Información de la compra (tabla)
    story.append(Spacer(1, 12))  # Espacio en blanco
    story.append(Paragraph("Información de la Compra", getSampleStyleSheet()['Heading2']))

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
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)])

    # Construir la tabla y aplicar el estilo
    compra_table = Table(data)
    compra_table.setStyle(style)

    story.append(compra_table)

    # Detalles adicionales de la factura
    story.append(Spacer(1, 12))  # Espacio en blanco
    story.append(Paragraph("Detalles Adicionales", getSampleStyleSheet()['Heading2']))
    story.append(Paragraph(f"Tipo de Pago: {factura.invo_pay_type.pay_name}", getSampleStyleSheet()['BodyText']))


    if factura.invo_pay_type.pay_name == 'Contado':
        story.append(Paragraph(f"Fecha de Expiración: {factura.expedition_date or 'Desconocida'}", getSampleStyleSheet()['BodyText']))

    # Totales
    story.append(Spacer(1, 12))  # Espacio en blanco
    story.append(Paragraph("Totales", getSampleStyleSheet()['Heading2']))
    story.append(Paragraph(f"Subtotal sin impuestos: {subtotal_sin_impuestos:.2f}", getSampleStyleSheet()['BodyText']))
    story.append(Paragraph(f"IVA 12%: {iva12:.2f}", getSampleStyleSheet()['BodyText']))
    story.append(Paragraph(f"Valor Total: {valor_total:.2f}", getSampleStyleSheet()['BodyText']))

    # Pie de página
    story.append(Spacer(1, 12))  # Espacio en blanco
    story.append(Paragraph("Condiciones de Pago", getSampleStyleSheet()['Heading2']))
    story.append(Paragraph("El pago se efectuará en 15 días.", getSampleStyleSheet()['BodyText']))

    # Construir el PDF
    doc.build(story)

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

