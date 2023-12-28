# modulocompras/urls.py
from django.urls import path
from .views import consultar_pago
from .views import login_view, menu_view, dashboard_view
from .views import ProvidersListCreateView
from .views import consultar_proveedores, editar_proveedor, insertar_proveedor

urlpatterns = [
    path('consultar_pago/', consultar_pago, name='consultar_pago'),
    path('login/', login_view, name='login'),
    path('menu/', menu_view, name='menu'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('api/tumodelo/', ProvidersListCreateView.as_view(), name='tumodelo-list-create'),
    path('consultar_proveedores/', consultar_proveedores, name='consultar_proveedores'),
    path('editar_proveedor/<int:prov_id>/', editar_proveedor, name='editar_proveedor'),
    path('insertar_proveedor/', insertar_proveedor, name='insertar_proveedor'),
]
