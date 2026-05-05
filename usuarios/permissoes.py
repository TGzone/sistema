# usuarios/permissoes.py
# NÃO importar nada de 'usuarios' aqui — causa circular import.

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def perfil_requerido(*perfis):
    """
    Bloqueia a view se o perfil do usuário não estiver na lista.
    Sempre use com @login_required acima.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('usuarios:login')
            perfil_atual = str(getattr(request.user, 'perfil', '')).upper()
            if perfil_atual not in [p.upper() for p in perfis]:
                messages.error(request, 'Você não tem permissão para acessar esta área.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def filtrar_por_igreja(queryset, user, campo='igreja'):
    """
    Presidente vê tudo. Os demais veem só a própria igreja.
    Uso: qs = filtrar_por_igreja(Pessoa.objects.all(), request.user, campo='unidade')
    """
    if str(getattr(user, 'perfil', '')).upper() == 'PRESIDENTE':
        return queryset
    return queryset.filter(**{campo: user.igreja})


# ── Grupos de perfil ──────────────────────────────────────────────────────────
# Nomes em maiúsculo para bater com os choices do model e com o views.py central

PERFIS_MASTER       = ('PRESIDENTE', 'DIRETORIA')
PERFIS_GERENCIAIS   = ('PRESIDENTE', 'DIRETORIA', 'PASTOR_UNIDADE')
PERFIS_FINANCEIROS  = ('PRESIDENTE', 'DIRETORIA', 'PASTOR_UNIDADE', 'TESOUREIRO')
PERFIS_OPERACIONAIS = ('PRESIDENTE', 'DIRETORIA', 'PASTOR_UNIDADE', 'LIDER_DEPARTAMENTO', 'MIDIA')