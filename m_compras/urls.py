# modulocompras/urls.py
from django.urls import path
from .views import (
    consultar_pago,
    generar_pdf,
    login_view,
    dashboard_view,
    logout_view,
    ProvidersListCreateView,
    consultar_proveedores,
    editar_proveedor,
    insertar_proveedor,
    reporte_proveedores,
    vista_factura,
    consultar_facturas,
    listarDetalleFactura,
    verificar_proveedor,
    obtener_detalle_proveedor,
    add_to_cart,
    Invoice_Insert,
    Invoice_Detail_Insert_View,
    login2,
    logout2
)

urlpatterns = [
    path("consultar_pago/", consultar_pago, name="consultar_pago"),
    path("login/", login_view, name="login"),
    path("login2/", login2, name="login2"),
    path("logout2/", logout2, name="logout2"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path(
        "api/tumodelo/", ProvidersListCreateView.as_view(), name="tumodelo-list-create"
    ),
    path("consultar_proveedores/", consultar_proveedores, name="consultar_proveedores"),
    path("editar_proveedor/<int:prov_id>/", editar_proveedor, name="editar_proveedor"),
    path("insertar_proveedor/", insertar_proveedor, name="insertar_proveedor"),
    path("detalle_factura/", vista_factura, name="detalle_factura"),
    path("consultar_facturas/", consultar_facturas, name="consultar_facturas"),
    path(
        "listarDetalleFactura/<str:factura_id>",
        listarDetalleFactura,
        name="listarDetalleFactura",
    ),
    path("verificar_proveedor/", verificar_proveedor, name="verificar_proveedor"),
    path(
        "obtener_detalle_proveedor/",
        obtener_detalle_proveedor,
        name="obtener_detalle_proveedor",
    ),
    path("add_to_cart/", add_to_cart, name="add_to_cart"),
    path("invoice_insert/", Invoice_Insert.as_view(), name="invoice_insert"),
    path('get_latest_invoice_id/', Invoice_Insert.as_view(), name='get_latest_invoice_id'),
    path(
        "invoice_detail_insert/<str:invo_det_invo_id>/",
        Invoice_Detail_Insert_View.as_view(),
        name="invoice_detail_insert",
    ),
    path('reporte_proveedores/', reporte_proveedores, name='reporte_proveedores'),

   path('generar_pdf/<int:invoice_id>/', generar_pdf, name='generar_pdf'),
]