from django.db import models

class Igreja(models.Model):
    """
    Modelo para cadastro das unidades (Sedes, Filiais e Pontos)
    """
    TIPO_CHOICES = [
        ('SEDE', 'Sede'),
        ('FILIAL', 'Congregação / Filial'),
        ('PONTO', 'Ponto de Pregação'),
    ]

    STATUS_CHOICES = [
        ('ATIVO', 'Ativa'),
        ('REFORMA', 'Em Reforma'),
        ('INATIVA', 'Inativa / Fechada'),
    ]

    # --- Dados da Unidade ---
    nome = models.CharField(max_length=200, verbose_name="Nome da Unidade")
    cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name="CNPJ")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='FILIAL')
    data_fundacao = models.DateField(blank=True, null=True, verbose_name="Data de Fundação")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone de Contato")

    # --- Liderança (Relacionamento Direto com App Pessoas) ---
    pastor = models.ForeignKey(
        'pessoas.Pessoa', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='igrejas_dirigidas',
        verbose_name="Pastor Dirigente"
    )

    # --- Endereço ---
    cep = models.CharField(max_length=10, blank=True, null=True)
    pais = models.CharField(max_length=50, default="Brasil")
    rua = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)

    # --- Informações Estruturais ---
    capacidade = models.PositiveIntegerField(blank=True, null=True, verbose_name="Capacidade Sentada")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ATIVO')
    observacoes = models.TextField(blank=True, null=True, verbose_name="Breve Histórico")

    # --- Metadados ---
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Igreja"
        verbose_name_plural = "Igrejas"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class Evento(models.Model):
    """
    Modelo para os eventos vinculados às igrejas
    """
    CATEGORIAS = [
        ('culto', 'Culto Geral'),
        ('ebd', 'Escola Bíblica'),
        ('reuniao', 'Reunião de Liderança'),
        ('social', 'Ação Social'),
    ]

    igreja = models.ForeignKey(Igreja, related_name='eventos', on_delete=models.CASCADE, verbose_name="Unidade/Igreja", null=True)
    titulo = models.CharField(max_length=150, verbose_name="Título do Evento")
    data_hora = models.DateTimeField(verbose_name="Data e Horário")
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='culto')
    imagem = models.ImageField(upload_to='eventos/', blank=True, null=True, verbose_name="Banner/Flyer")
    descricao = models.TextField(blank=True, verbose_name="Descrição")

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['data_hora']

    def __str__(self):
        return f"{self.titulo} - {self.igreja.nome if self.igreja else 'Sem Igreja'}"