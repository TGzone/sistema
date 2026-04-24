from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect 
from . import views 

urlpatterns = [
    # 1. Rota Raiz: Manda pro login
    path('', lambda request: redirect('usuarios:login'), name='root'),

    # 2. Admin
    path('admin/', admin.site.urls),
    
    # 3. Dashboard (Corrigi o erro de digitação de 'deshboard' para 'dashboard')
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # 4. MÓDULO DE USUÁRIOS (Faltava essa linha para o redirect acima funcionar!)
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),
    
    # 5. Outros Módulos
    path('pessoas/', include('pessoas.urls', namespace='pessoas')),
    path('igrejas/', include('igrejas.urls', namespace='igrejas')),
    path('cultos/', include('cultos.urls', namespace='cultos')),
    path('financeiro/', include('financeiro.urls', namespace='financeiro')),
    path('pastoral/', views.pastoral, name='pastoral'),
]

# Configuração de arquivos de mídia
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)