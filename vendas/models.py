from django.db import models
from django.core.validators import MinValueValidator
from usuarios.models import Usuario
from produtos.models import Produto, MovimentacaoEstoque
from decimal import Decimal

class Venda(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]
    
    id = models.AutoField(primary_key=True)
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Total da Venda"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name="Status da Venda"
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        verbose_name="Usuário Responsável"
    )

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Venda {self.id} - {self.get_status_display()} - R$ {self.total}"

    def calcular_total(self):
        """Calcula o total da venda baseado nos itens"""
        total = Decimal('0.00')
        for item in self.itens.all():
            total += item.subtotal
        return total

    def finalizar_venda(self):
        """Finaliza a venda e registra as movimentações de estoque"""
        if self.status != 'pendente':
            raise ValueError("Apenas vendas pendentes podem ser finalizadas")
        
        # Atualiza estoque e registra movimentações
        for item in self.itens.all():
            produto = item.produto
            estoque_anterior = produto.estoque_atual
            
            # Verifica se há estoque suficiente
            if produto.estoque_atual < item.quantidade:
                raise ValueError(f"Estoque insuficiente para o produto {produto.nome}. Disponível: {produto.estoque_atual}")
            
            # Atualiza estoque
            produto.estoque_atual -= item.quantidade
            produto.save()
            
            # Registra movimentação de estoque
            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo='saida',
                quantidade=item.quantidade,
                estoque_anterior=estoque_anterior,
                estoque_atual=produto.estoque_atual,
                observacao=f'Saída para venda {self.id}',
                usuario=self.usuario
            )
        
        # Atualiza status da venda
        self.status = 'finalizada'
        self.save()

    def cancelar_venda(self):
        """Cancela a venda"""
        if self.status == 'finalizada':
            raise ValueError("Vendas finalizadas não podem ser canceladas")
        
        self.status = 'cancelada'
        self.save()

class ItemVenda(models.Model):
    venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Venda"
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        verbose_name="Produto"
    )
    quantidade = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Quantidade"
    )
    preco_unitario = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Preço Unitário"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Subtotal"
    )

    class Meta:
        verbose_name = "Item da Venda"
        verbose_name_plural = "Itens da Venda"
        unique_together = ['venda', 'produto']

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade}x R$ {self.preco_unitario} = R$ {self.subtotal}"

    def save(self, *args, **kwargs):
        # Calcula o subtotal automaticamente
        self.subtotal = self.preco_unitario * self.quantidade
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Verifica se o produto pertence ao mesmo usuário da venda
        if self.produto.usuario != self.venda.usuario:
            raise ValidationError("O produto deve pertencer ao mesmo usuário da venda")
        
        # Verifica se há estoque suficiente (apenas para vendas pendentes)
        if self.venda.status == 'pendente' and self.produto.estoque_atual < self.quantidade:
            raise ValidationError(f"Estoque insuficiente. Disponível: {self.produto.estoque_atual}")
