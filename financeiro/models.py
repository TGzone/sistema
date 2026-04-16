from django.db import models
from django.utils import timezone

class Movimentacao(models.Model):
    TIPO_CHOICES = [('ENTRADA', 'Entrada'), ('SAIDA', 'Saída')]
    CATEGORIA_CHOICES = [
        ('DIZIMO', 'Dízimo'),
        ('OFERTA', 'Oferta'),
        ('MISSIONARIA', 'Oferta Missionária'),
        ('AVULSA', 'Oferta Avulsa'),
        ('OUTROS', 'Outros'),
    ]
    
    # Vínculos com outros módulos conforme seu Mapa Funcional
    igreja = models.ForeignKey('igrejas.Igreja', on_delete=models.CASCADE, related_name='movimentacoes')
    membro = models.ForeignKey('pessoas.Pessoa', on_delete=models.SET_NULL, null=True, blank=True)
    culto_vinculado = models.ForeignKey('cultos.Culto', on_delete=models.SET_NULL, null=True, blank=True)
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    descricao = models.CharField(max_length=255) # Campo aberto para finalidade
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField(default=timezone.now)
    origem_whatsapp = models.BooleanField(default=False)

class ContaFixa(models.Model):
    igreja = models.ForeignKey('igrejas.Igreja', on_delete=models.CASCADE)
    nome = models.CharField(max_length=100) # Ex: Luz, Água
    empresa = models.CharField(max_length=100)
    vencimento_dia = models.IntegerField()
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2)

class Manutencao(models.Model):
    igreja = models.ForeignKey('igrejas.Igreja', on_delete=models.CASCADE)
    STATUS_CHOICES = [('URGENTE', 'Urgente'), ('NECESSARIO', 'Necessário'), ('MELHORIA', 'Melhoria')]
    item = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NECESSARIO')
    observacao = models.TextField()
    orcamento_aprovado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

class DadosBancarios(models.Model):
    igreja = models.OneToOneField('igrejas.Igreja', on_delete=models.CASCADE)
    banco = models.CharField(max_length=100)
    agencia = models.CharField(max_length=20)
    conta = models.CharField(max_length=50)
    chave_pix = models.CharField(max_length=255)