from django.db import models
from igrejas.models import Igreja # Importando sua model de Unidades

class Culto(models.Model):
    TIPO_CHOICES = [
        ('culto_domingo', 'Culto de Domingo'),
        ('doutrina', 'Culto de Doutrina'),
        ('oracao', 'Reunião de Oração'),
        ('celula', 'Célula'),
        ('ensaio', 'Ensaio do Louvor'),
        ('evento_especial', 'Evento Especial'), 
        ('outros', 'Outros'),
    ]

    ESTILO_CHOICES = [
        ('solido', 'Cor Sólida'),
        ('gradiente', 'Gradiente Animado'),
        ('desenhado', 'Padrão Geométrico'),
    ]

    igreja = models.ForeignKey(Igreja, on_delete=models.CASCADE, related_name='cultos')
    titulo = models.CharField(max_length=200, help_text="Nome do evento ou Tema do culto")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='culto_domingo')
    
    # Data e Hora
    data = models.DateField()
    horario = models.TimeField()
    
    # Detalhes do Evento
    pregador_palestrante = models.CharField(max_length=150, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True, help_text="Descrição livre para eventos especiais")
    local = models.CharField(max_length=200, default="Templo Principal")
    
    # Personalização Visual (O pulo do gato!)
    cor_personalizada = models.CharField(max_length=7, default="#2563eb", help_text="Cor em Hexadecimal")
    estilo_card = models.CharField(max_length=20, choices=ESTILO_CHOICES, default='solido')
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Culto/Evento"
        verbose_name_plural = "Cultos e Eventos"
        ordering = ['-data', '-horario']

    def __str__(self):
        return f"{self.titulo} - {self.data.strftime('%d/%m/%Y')}"