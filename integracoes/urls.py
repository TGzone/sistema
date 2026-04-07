from django.contrib import admin
from django.urls import path, include
from . import views  # Importa as views globais (dashboard, relatorios, etc)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. PÁGINA INICIAL (DASHBOARD)
    path('', views.dashboard, name='dashboard'),
    
    # 2. MÓDULOS COM INCLUDE (Cada pasta tem seu próprio urls.py)
    path('pessoas/', include('pessoas.urls', namespace='pessoas')),
    path('igrejas/', include('igrejas.urls', namespace='igrejas')),
    
    # 3. ROTAS DIRETAS (Views que ainda estão na pasta 'sistema')
    path('relatorios/', views.relatorios, name='relatorios'),
    path('financeiro/', views.financeiro, name='financeiro'),
    path('pastoral/', views.pastoral, name='pastoral'),
]