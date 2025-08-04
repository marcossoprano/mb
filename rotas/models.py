from django.db import models
from django.core.validators import MinValueValidator
from usuarios.models import Usuario
from produtos.models import Produto

class Veiculo(models.Model):
    TIPO_COMBUSTIVEL_CHOICES = [
        ('diesel', 'Diesel'),
        ('gasolina', 'Gasolina'),
        ('etanol', 'Etanol'),
        ('gnv', 'Gás Veicular (GNV)'),
    ]
    
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, verbose_name="Nome do Veículo")
    tipo_combustivel = models.CharField(
        max_length=10,
        choices=TIPO_COMBUSTIVEL_CHOICES,
        verbose_name="Tipo de Combustível"
    )
    eficiencia_km_l = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Eficiência (km/L para líquidos, km/m³ para GNV)"
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        verbose_name="Usuário Responsável"
    )
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_combustivel_display()})"
    
    def get_unidade_eficiencia(self):
        """
        Retorna a unidade de eficiência baseada no tipo de combustível
        """
        if self.tipo_combustivel == 'gnv':
            return 'km/m³'
        else:
            return 'km/L'
    
    def get_eficiencia_display(self):
        """
        Retorna a eficiência formatada com a unidade correta
        """
        return f"{self.eficiencia_km_l} {self.get_unidade_eficiencia()}"

class Rota(models.Model):
    STATUS_CHOICES = [
        ('em_progresso', 'Em Progresso'),
        ('concluido', 'Concluído'),
    ]
    
    id = models.AutoField(primary_key=True)
    data_geracao = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora de Geração")
    enderecos_otimizados = models.JSONField(verbose_name="Endereços na Ordem Otimizada")
    coordenadas_otimizadas = models.JSONField(verbose_name="Coordenadas na Ordem Otimizada")
    distancia_total_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Distância Total (km)"
    )
    tempo_estimado_minutos = models.IntegerField(verbose_name="Tempo Estimado (minutos)")
    veiculo = models.ForeignKey(
        Veiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Veículo Escolhido"
    )
    nome_motorista = models.CharField(
        max_length=100, 
        verbose_name="Nome do Motorista",
        null=True,
        blank=True
    )
    valor_rota = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor da Rota (R$)"
    )
    preco_combustivel_usado = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Preço do Combustível Usado (R$/L ou R$/m³)"
    )
    produtos_quantidades = models.JSONField(verbose_name="Produtos e Quantidades")
    link_maps = models.URLField(max_length=500, verbose_name="Link do Google Maps")
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='em_progresso',
        verbose_name="Status da Rota"
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        verbose_name="Usuário Responsável"
    )

    class Meta:
        verbose_name = "Rota"
        verbose_name_plural = "Rotas"
        ordering = ['-data_geracao']

    def __str__(self):
        return f"Rota {self.id} - {self.nome_motorista} ({self.get_status_display()})"
