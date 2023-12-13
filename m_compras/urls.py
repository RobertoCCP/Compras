# modulocompras/urls.py
from django.urls import path
from .views import consultar_pago
from .views import login_view, menu_view


urlpatterns = [
    path('consultar-pago/', consultar_pago, name='consultar_pago'),
    path('login/', login_view, name='login'),
    path('menu/', menu_view, name='menu'),
]
