from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from usuarios.permissoes import perfil_requerido, PERFIS_MASTER, PERFIS_GERENCIAIS, PERFIS_FINANCEIROS, PERFIS_OPERACIONAIS





# --- ESTRUTURA BASE ---


@perfil_requerido('PRESIDENTE', 'DIRETORIA', 'PASTOR_UNIDADE', 'LIDER_DEPARTAMENTO', 'MIDIA')
@login_required
@never_cache
def base(request):
    return render(request, "base/base.html")

@login_required
@perfil_requerido(*PERFIS_OPERACIONAIS)
@never_cache
def home(request):
    return render(request, "home.html")

@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
@never_cache
def dashboard(request):
    return render(request, "dashboard.html")    

# --- MÓDULOS INDEPENDENTES (LOGICA CENTRALIZADA) ---
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
@never_cache
def pessoas(request):
    return render(request, "pessoas/pessoas.html")  

def igrejas(request):
    return render(request, "igrejas.html")  

def pastoral(request):
    return render(request, "pastoral.html")

def cultos(request):
    return render(request, "cultos/cultos.html")    


# --- MÓDULO FINANCEIRO (SUBMENUS) ---

@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
@never_cache
def financeiro(request):
    return render(request, "financeiro/financeiro.html")

def usuarios (request):
    return render(request, "usuarios/usuarios.html")