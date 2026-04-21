from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.financeiro, name='financeiro'),
    path('movimentacoes/', views.movimentacoes, name='movimentacoes'),
    path('contas/', views.contas, name='contas'),
    path('manutencao/', views.manutencao, name='manutencao'),
    path('banco/', views.banco, name='banco'),
    path('contas/<int:conta_id>/', views.conta_detalhes, name='conta_detalhes'),
    path('banco/nova-conta/', views.nova_conta, name='nova_conta'), # A nova rota que recebe o POST
]