from django.shortcuts import render, redirect
from .models import PayType
# Create your views here.


def consultar_pago(request):
    resultados = PayType.objects.raw('SELECT pay_id, pay_name FROM public."Pay_type"')
    return render(request, 'consultar_pagos.html', {'resultados': resultados})

def login_view(request):
    if request.method == 'POST':
        # Lógica de autenticación aquí (por ahora, simplemente redireccionamos)
        return redirect('menu')
    else:
        return render(request, 'login.html')
    
def menu_view(request):
    return render(request, 'menu.html')