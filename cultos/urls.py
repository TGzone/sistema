from django.urls import path
from . import views

app_name = 'cultos'

urlpatterns = [
    path('calendario/', views.calendario, name='calendario'),
    path('novo/', views.criar_culto, name='criar'),
    path('detalhe/<int:pk>/', views.detalhe_culto, name='detalhe'), # ROTA DE EDIÇÃO
    path('excluir/<int:pk>/', views.excluir_culto, name='excluir'), # ROTA DE EXCLUSÃO
]