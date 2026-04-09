from django.contrib import admin
from django.urls import path, include
from django.conf import settings # IMPORTANTE: Importa suas configurações
from django.conf.urls.static import static # IMPORTANTE: Importa a função de arquivos estáticos
from . import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Página Inicial (Dashboard)
    path('', views.dashboard, name='dashboard'),
    
    # MÓDULOS COM INCLUDE
    path('pessoas/', include('pessoas.urls', namespace='pessoas')),
    path('igrejas/', include('igrejas.urls', namespace='igrejas')),
    path('cultos/', include('cultos.urls', namespace='cultos')),
    # ROTAS DIRETAS
    path('relatorios/', views.relatorios, name='relatorios'),
    path('financeiro/', views.financeiro, name='financeiro'),
    path('pastoral/', views.pastoral, name='pastoral'),
]

# ESTA PARTE FICA FORA DOS COLCHETES:
# Ela diz ao Django: "Se estivermos em modo de desenvolvimento (DEBUG=True), 
# sirva os arquivos da pasta MEDIA para o navegador poder ler."
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)