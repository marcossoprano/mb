from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from usuarios.models import Usuario

class Fornecedor(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Fornecedor")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    email = models.EmailField(verbose_name="Email")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        verbose_name="Usuário (Empresa) Responsável"
    )

    class Meta:
        unique_together = ['nome', 'usuario']

    def __str__(self):
        return self.nome

class Categoria(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        verbose_name="Usuário (Empresa) Responsável"
    )

    def __str__(self):
        return self.nome

class Produto(models.Model):
    idProduto = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, verbose_name="Nome do Produto")  # obrigatório
    preco_custo = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Preço de Custo"
    )  # obrigatório
    preco_venda = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Preço de Venda"
    )  # obrigatório
    estoque_minimo = models.PositiveIntegerField(verbose_name="Estoque Mínimo")  # obrigatório
    estoque_atual = models.PositiveIntegerField(verbose_name="Estoque Atual")  # obrigatório
    validade = models.DateField(verbose_name="Validade", null=True, blank=True)
    codigo_barras = models.CharField(
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[0-9]{13}$',
                message='Código de barras deve conter exatamente 13 dígitos numéricos'
            )
        ],
        help_text="Código de barras no padrão EAN-13 (13 dígitos)",
        blank=True,
        null=True
    )
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    data_fabricacao = models.DateField(verbose_name="Data de Fabricação", blank=True, null=True)
    lote = models.CharField(max_length=50, verbose_name="Número do Lote", blank=True, null=True)
    marca = models.CharField(max_length=50, verbose_name="Marca", blank=True, null=True)  # usado no search
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.PROTECT,
        verbose_name="Fornecedor",
        blank=True,
        null=True
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoria"  # usado no filtro exato
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        verbose_name="Usuário Responsável"
    )

    def __str__(self):
        return f"{self.nome} ({self.codigo_barras})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.preco_venda < self.preco_custo:
            raise ValidationError("Preço de venda não pode ser menor que o preço de custo")
        if self.estoque_minimo < 0:
            raise ValidationError("Estoque mínimo não pode ser negativo")

class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]
    
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        verbose_name="Produto",
        related_name='movimentacoes'
    )
    tipo = models.CharField(
        max_length=7,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Movimentação"
    )
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade Movimentada")
    estoque_anterior = models.PositiveIntegerField(verbose_name="Estoque Anterior")
    estoque_atual = models.PositiveIntegerField(verbose_name="Estoque Atual")
    data_movimentacao = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora da Movimentação")
    observacao = models.TextField(blank=True, verbose_name="Observação")
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        verbose_name="Usuário Responsável"
    )

    class Meta:
        ordering = ['-data_movimentacao']
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"

    def __str__(self):
        return f"{self.produto.nome} - {self.get_tipo_display()} ({self.quantidade}) - {self.data_movimentacao.strftime('%d/%m/%Y %H:%M')}"
