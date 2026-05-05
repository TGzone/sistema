from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from usuarios.permissoes import perfil_requerido, PERFIS_MASTER, PERFIS_GERENCIAIS, PERFIS_FINANCEIROS, PERFIS_OPERACIONAIS


@login_required
@perfil_requerido(*PERFIS_OPERACIONAIS)
def dashboard(request):
    return render(request, "dashboard.html")

