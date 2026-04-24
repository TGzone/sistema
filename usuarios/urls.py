from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('cadastro_usuarios/', views.cadastro_usuarios, name='cadastro_usuarios'),
    path('lista_solicitacoes/', views.lista_solicitacoes, name='lista_solicitacoes'),
    path('cadastro_usuarios_sistema/', views.cadastro_usuarios_sistema, name='cadastro_usuarios_sistema'),
]