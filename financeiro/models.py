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

class Obrigacao(models.Model): 
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('atrasado', 'Atrasado'),
    ]
    RECORRENCIA_CHOICES = [
        ('unica', 'Única'),
        ('mensal', 'Mensal'),
        ('anual', 'Anual'),
    ]

    igreja = models.ForeignKey('igrejas.Igreja', on_delete=models.CASCADE)
    nome = models.CharField(max_length=100) # Ex: Conta de Energia
    empresa = models.CharField(max_length=100, blank=True, null=True) # Fornecedor
    categoria = models.CharField(max_length=50, default='Outros') # Ex: Manutenção, Utilidades
    
    valor = models.DecimalField(max_digits=10, decimal_places=2) # Valor real
    vencimento = models.DateField() # Data exata (DD/MM/YYYY)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    recorrencia = models.CharField(max_length=20, choices=RECORRENCIA_CHOICES, default='mensal')
    observacao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nome} - {self.get_status_display()}"

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