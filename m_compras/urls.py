# modulocompras/urls.py
from django.urls import path
from .views import consultar_pago
from .views import login_view, menu_view, dashboard_view, logout_view
from .views import ProvidersListCreateView
from .views import (consultar_proveedores, 
                    editar_proveedor, 
                    insertar_proveedor,
                    vista_factura, 
                    detalle,
                    consultar_facturas,
                    listarDetalleFactura,)
urlpatterns = [
    path('consultar_pago/', consultar_pago, name='consultar_pago'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('api/tumodelo/', ProvidersListCreateView.as_view(), name='tumodelo-list-create'),
    path('consultar_proveedores/', consultar_proveedores, name='consultar_proveedores'),
    path('editar_proveedor/<int:prov_id>/', editar_proveedor, name='editar_proveedor'),
    path('insertar_proveedor/', insertar_proveedor, name='insertar_proveedor'),
    path('detalle_factura/', vista_factura, name='detalle_factura'),
    path('detalle/', detalle, name='detalle'),
    path("consultar_facturas/", consultar_facturas, name="consultar_facturas"),
    path("listarDetalleFactura/<str:factura_id>", listarDetalleFactura, name="listarDetalleFactura"),
]
