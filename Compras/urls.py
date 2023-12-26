"""
URL configuration for Compras project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from m_compras.views import login_view
from m_compras.views import consultar_pago
from m_compras.views import ProvidersListCreateView
from m_compras.views import consultar_proveedores
from m_compras.views import login_view, menu_view, dashboard_view
from m_compras.views import ProvidersListCreateView
from m_compras.views import consultar_proveedores, editar_proveedor, insertar_proveedor

urlpatterns = [
    path('admin/', admin.site.urls),
     #path('m_compras/', include('m_compras.urls')),
    #path('', ProvidersListCreateView.as_view(), name='inicio'),  # Agrega esta línea para la ruta raíz
    #path('', consultar_pago, name='inicio'),
    #path('', consultar_proveedores, name='inicio'),
    path('', login_view, name='inicio'),
     path('consultar_pago/', consultar_pago, name='consultar_pago'),
    path('login/', login_view, name='login'),
    path('menu/', menu_view, name='menu'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('api/tumodelo/', ProvidersListCreateView.as_view(), name='tumodelo-list-create'),
    path('consultar_proveedores/', consultar_proveedores, name='consultar_proveedores'),
    path('editar_proveedor/<int:prov_id>/', editar_proveedor, name='editar_proveedor'),
    path('insertar_proveedor/', insertar_proveedor, name='insertar_proveedor'),
]




