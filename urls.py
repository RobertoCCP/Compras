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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('m_compras/', include('m_compras.urls')),
    #path('', ProvidersListCreateView.as_view(), name='inicio'),  # Agrega esta línea para la ruta raíz
    #path('', consultar_pago, name='inicio'),
    path('', login_view, name='inicio'),
    #path('', consultar_proveedores, name='inicio'),
]

