from rest_framework import serializers
from decimal import Decimal
from .models import Venda, ItemVenda
from produtos.models import Produto
from produtos.serializers import ProdutoSerializer

class ItemVendaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_codigo_barras = serializers.CharField(source='produto.codigo_barras', read_only=True)
    produto_preco_venda = serializers.DecimalField(source='produto.preco_venda', max_digits=8, decimal_places=2, read_only=True)
    produto_estoque_atual = serializers.IntegerField(source='produto.estoque_atual', read_only=True)
    
    class Meta:
        model = ItemVenda
        fields = [
            'id',
            'produto',
            'produto_nome',
            'produto_codigo_barras',
            'produto_preco_venda',
            'produto_estoque_atual',
            'quantidade',
            'preco_unitario',
            'subtotal'
        ]
        read_only_fields = ['id', 'subtotal', 'produto_nome', 'produto_codigo_barras', 'produto_preco_venda', 'produto_estoque_atual']

    def validate_produto(self, value):
        """Valida se o produto pertence ao usuário"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if value.usuario != request.user:
                raise serializers.ValidationError("Produto não pertence ao usuário")
        return value

    def validate_quantidade(self, value):
        """Valida a quantidade"""
        if value <= 0:
            raise serializers.ValidationError("Quantidade deve ser maior que zero")
        return value

    def validate_preco_unitario(self, value):
        """Valida o preço unitário"""
        if value <= 0:
            raise serializers.ValidationError("Preço unitário deve ser maior que zero")
        return value

class ItemVendaCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de itens de venda"""
    
    class Meta:
        model = ItemVenda
        fields = ['produto', 'quantidade', 'preco_unitario']

    def validate_produto(self, value):
        """Valida se o produto pertence ao usuário"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if value.usuario != request.user:
                raise serializers.ValidationError("Produto não pertence ao usuário")
        return value

    def validate_quantidade(self, value):
        """Valida a quantidade"""
        if value <= 0:
            raise serializers.ValidationError("Quantidade deve ser maior que zero")
        return value

    def validate_preco_unitario(self, value):
        """Valida o preço unitário"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Preço unitário deve ser maior que zero")
        return value

    def validate(self, data):
        """Validação geral e define preço unitário padrão"""
        produto = data.get('produto')
        preco_unitario = data.get('preco_unitario')
        
        # Se preço unitário não foi informado, usa o preço de venda do produto
        if preco_unitario is None and produto:
            data['preco_unitario'] = produto.preco_venda
        
        return data

class VendaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    itens = ItemVendaSerializer(many=True, read_only=True)
    total_itens = serializers.SerializerMethodField()
    
    class Meta:
        model = Venda
        fields = [
            'id',
            'data_criacao',
            'data_atualizacao',
            'total',
            'status',
            'status_display',
            'observacoes',
            'itens',
            'total_itens'
        ]
        read_only_fields = ['id', 'data_criacao', 'data_atualizacao', 'total', 'status_display', 'itens', 'total_itens']

    def get_total_itens(self, obj):
        """Retorna o número total de itens na venda"""
        return obj.itens.count()

class VendaCreateSerializer(serializers.Serializer):
    """Serializer para criação de vendas"""
    observacoes = serializers.CharField(required=False, allow_blank=True)
    itens = ItemVendaCreateSerializer(many=True, min_length=1)

    def validate_itens(self, value):
        """Valida os itens da venda"""
        if not value:
            raise serializers.ValidationError("A venda deve ter pelo menos um item")
        
        # Verifica se há produtos duplicados
        produtos_ids = [item['produto'].idProduto for item in value]
        if len(produtos_ids) != len(set(produtos_ids)):
            raise serializers.ValidationError("Não é possível adicionar o mesmo produto mais de uma vez")
        
        # Verifica estoque para cada produto
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            for item in value:
                produto = item['produto']
                quantidade = item['quantidade']
                
                if produto.estoque_atual < quantidade:
                    raise serializers.ValidationError(
                        f"Estoque insuficiente para o produto {produto.nome}. Disponível: {produto.estoque_atual}"
                    )
        
        return value

    def create(self, validated_data):
        """Cria a venda e seus itens"""
        request = self.context.get('request')
        itens_data = validated_data.pop('itens')
        
        # Calcula o total da venda
        total = Decimal('0.00')
        for item_data in itens_data:
            # Se preço unitário não foi informado, usa o preço de venda do produto
            preco_unitario = item_data.get('preco_unitario')
            if preco_unitario is None:
                preco_unitario = item_data['produto'].preco_venda
                item_data['preco_unitario'] = preco_unitario
            
            subtotal = preco_unitario * item_data['quantidade']
            total += subtotal
        
        # Cria a venda
        venda = Venda.objects.create(
            total=total,
            observacoes=validated_data.get('observacoes', ''),
            usuario=request.user
        )
        
        # Cria os itens da venda
        for item_data in itens_data:
            ItemVenda.objects.create(
                venda=venda,
                produto=item_data['produto'],
                quantidade=item_data['quantidade'],
                preco_unitario=item_data['preco_unitario']
            )
        
        return venda

class VendaUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de vendas (apenas observações e status)"""
    
    class Meta:
        model = Venda
        fields = ['observacoes', 'status']

    def validate_status(self, value):
        """Valida mudanças de status"""
        instance = self.instance
        if instance:
            if instance.status == 'finalizada' and value != 'finalizada':
                raise serializers.ValidationError("Vendas finalizadas não podem ter o status alterado")
            if instance.status == 'cancelada' and value != 'cancelada':
                raise serializers.ValidationError("Vendas canceladas não podem ter o status alterado")
        return value

class VendaFinalizarSerializer(serializers.Serializer):
    """Serializer para finalizar vendas"""
    
    def validate(self, data):
        """Valida se a venda pode ser finalizada"""
        venda = self.context.get('venda')
        if not venda:
            raise serializers.ValidationError("Venda não encontrada")
        
        if venda.status != 'pendente':
            raise serializers.ValidationError("Apenas vendas pendentes podem ser finalizadas")
        
        if not venda.itens.exists():
            raise serializers.ValidationError("A venda deve ter pelo menos um item")
        
        # Verifica estoque novamente
        for item in venda.itens.all():
            if item.produto.estoque_atual < item.quantidade:
                raise serializers.ValidationError(
                    f"Estoque insuficiente para o produto {item.produto.nome}. Disponível: {item.produto.estoque_atual}"
                )
        
        return data

class VendaCancelarSerializer(serializers.Serializer):
    """Serializer para cancelar vendas"""
    
    def validate(self, data):
        """Valida se a venda pode ser cancelada"""
        venda = self.context.get('venda')
        if not venda:
            raise serializers.ValidationError("Venda não encontrada")
        
        if venda.status == 'finalizada':
            raise serializers.ValidationError("Vendas finalizadas não podem ser canceladas")
        
        return data
