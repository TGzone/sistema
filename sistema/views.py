from django.shortcuts import render
from django.views.decorators.cache import never_cache
# --- ESTRUTURA BASE ---
@never_cache
def base(request):
    return render(request, "base/base.html")

@never_cache
def home(request):
    return render(request, "home.html")

@never_cache
def dashboard(request):
    return render(request, "dashboard.html")    

# --- MÓDULOS INDEPENDENTES (LOGICA CENTRALIZADA) ---

def pessoas(request):
    return render(request, "pessoas/pessoas.html")  

def igrejas(request):
    return render(request, "igrejas.html")  

def pastoral(request):
    return render(request, "pastoral.html")

def cultos(request):
    return render(request, "cultos/cultos.html")    

# --- MÓDULO FINANCEIRO (SUBMENUS) ---
def financeiro(request):
    return render(request, "financeiro/financeiro.html")