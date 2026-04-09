from django.urls import path
from . import views

app_name = 'cultos'

urlpatterns = [
    path('calendario/', views.calendario, name='calendario'),
    path('novo/', views.criar_culto, name='criar_culto'),
    path('<int:pk>/', views.detalhe_culto, name='detalhe'),
]