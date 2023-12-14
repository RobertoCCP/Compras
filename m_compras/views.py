from django.shortcuts import render, redirect
from .models import PayType
from .models import Providers
from django.db import connection
# Create your views here.


def consultar_pago(request):
    resultados = PayType.objects.raw('SELECT pay_id, pay_name FROM public."Pay_type"')
    return render(request, 'consultar_pagos.html', {'resultados': resultados})

def consultar_proveedores(request):
    # Llama a la función almacenada utilizando el ORM de Django
    results = Providers.objects.raw('SELECT * FROM select_providers_all();')
    # Puedes pasar los resultados a la plantilla o hacer cualquier otra cosa con ellos
    return render(request, 'consultar_proveedores.html', {'results': results})



def login_view(request):
    if request.method == 'POST':
        # Lógica de autenticación aquí (por ahora, simplemente redireccionamos)
        return redirect('menu')
    else:
        return render(request, 'login.html')
    
def menu_view(request):
    return render(request, 'menu.html')


from rest_framework import generics
from .models import Providers
from .serializers import ProvidersSerializer

class ProvidersListCreateView(generics.ListCreateAPIView):
    queryset = Providers.objects.all()
    serializer_class = ProvidersSerializer