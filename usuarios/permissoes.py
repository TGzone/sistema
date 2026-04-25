# usuarios/permissoes.py (Ajustado)
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect

# DEFINIÇÃO DOS GRUPOS DE ACESSO (CRACHÁS)
PERFIS_MASTER = ['PRESIDENTE', 'DIRETORIA']
PERFIS_GERENCIAIS = ['PRESIDENTE', 'DIRETORIA', 'PASTOR_UNIDADE']
PERFIS_FINANCEIROS = ['PRESIDENTE', 'DIRETORIA', 'PASTOR_UNIDADE', 'TESOUREIRO']
PERFIS_OPERACIONAIS = ['PRESIDENTE', 'DIRETORIA', 'PASTOR_UNIDADE', 'LIDER_DEPARTAMENTO', 'MIDIA']

def perfil_requerido(*perfis_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('usuarios:login')
            
            # PULO DO GATO: Converte o perfil do usuário para maiúsculo para garantir a leitura correta
            perfil_usuario = str(request.user.perfil).upper() if request.user.perfil else ''
            
            if perfil_usuario in perfis_permitidos:
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied("Acesso Negado: Seu perfil não tem permissão para esta área.")
            
        return _wrapped_view
    return decorator