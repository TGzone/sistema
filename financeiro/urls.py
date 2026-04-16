from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.financeiro, name='financeiro'),
    path('movimentacoes/', views.movimentacoes, name='movimentacoes'),
    path('contas/', views.contas, name='contas'),
    path('manutencao/', views.manutencao, name='manutencao'),
    path('bancos/', views.bancos, name='bancos'),
]