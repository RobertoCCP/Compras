# modulocompras/urls.py
from django.urls import path
from .views import consultar_pago
from .views import login_view, menu_view
from .views import ProvidersListCreateView
from .views import consultar_proveedores

urlpatterns = [
    path('consultar_pago/', consultar_pago, name='consultar_pago'),
    path('login/', login_view, name='login'),
    path('menu/', menu_view, name='menu'),
    path('api/tumodelo/', ProvidersListCreateView.as_view(), name='tumodelo-list-create'),
    path('consultar_proveedores/', consultar_proveedores, name='consultar_proveedores'),
]
