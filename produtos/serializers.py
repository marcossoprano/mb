from rest_framework import serializers
from .models import Produto, Fornecedor, Categoria, MovimentacaoEstoque

class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = ['id', 'nome', 'telefone', 'email', 'endereco']
        read_only_fields = ['id']
    
    def validate(self, data):
        # Verifica se já existe um fornecedor com este nome para o usuário
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if Fornecedor.objects.filter(nome=data['nome'], usuario=request.user).exists():
                raise serializers.ValidationError("Já existe um fornecedor com este nome.")
        return data


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome']
        read_only_fields = ['id']  # opcional


class CategoriaCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de categoria com validação de nome único por usuário"""
    
    class Meta:
        model = Categoria
        fields = ['nome']
    
    def validate_nome(self, value):
        # Verifica se já existe uma categoria com este nome para o usuário
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if Categoria.objects.filter(nome=value, usuario=request.user).exists():
                raise serializers.ValidationError("Já existe uma categoria com este nome.")
        return value


class ProdutoSerializer(serializers.ModelSerializer):
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    
    class Meta:
        model = Produto
        fields = [
            'idProduto',
            'nome',
            'codigo_barras',
            'descricao',
            'data_fabricacao',
            'lote',
            'preco_custo',
            'preco_venda',
            'marca',
            'estoque_minimo',
            'estoque_atual',
            'data_cadastro',
            'data_atualizacao',
            'fornecedor',
            'fornecedor_nome',
            'categoria',
            'categoria_nome',
            # Não expomos o campo usuario para o cliente,
            # ele é definido automaticamente no backend
        ]
        read_only_fields = ['idProduto', 'data_cadastro', 'data_atualizacao', 'fornecedor_nome', 'categoria_nome']

    def validate(self, data):
        preco_custo = data.get('preco_custo')
        preco_venda = data.get('preco_venda')
        if preco_custo and preco_venda and preco_venda < preco_custo:
            raise serializers.ValidationError("Preço de venda não pode ser menor que o preço de custo.")
        return data

    def validate_codigo_barras(self, value):
        if not value.isdigit() or len(value) != 13:
            raise serializers.ValidationError("Código de barras deve conter exatamente 13 dígitos numéricos.")
        return value


class ProdutoCreateWithCategoriaSerializer(serializers.ModelSerializer):
    """Serializer para criação de produto com possibilidade de criar categoria inline"""
    
    nova_categoria = serializers.CharField(max_length=100, required=False, write_only=True)
    categoria_id = serializers.IntegerField(required=False, write_only=True)
    
    class Meta:
        model = Produto
        fields = [
            'nome',
            'codigo_barras',
            'descricao',
            'data_fabricacao',
            'lote',
            'preco_custo',
            'preco_venda',
            'marca',
            'estoque_minimo',
            'estoque_atual',
            'fornecedor',
            'categoria_id',
            'nova_categoria',
        ]
    
    def validate(self, data):
        # Validação de preços
        preco_custo = data.get('preco_custo')
        preco_venda = data.get('preco_venda')
        if preco_custo and preco_venda and preco_venda < preco_custo:
            raise serializers.ValidationError("Preço de venda não pode ser menor que o preço de custo.")
        
        # Validação de categoria
        categoria_id = data.get('categoria_id')
        nova_categoria = data.get('nova_categoria')
        
        if not categoria_id and not nova_categoria:
            raise serializers.ValidationError("É necessário selecionar uma categoria ou criar uma nova.")
        
        if categoria_id and nova_categoria:
            raise serializers.ValidationError("Não é possível selecionar uma categoria e criar uma nova ao mesmo tempo.")
        
        return data
    
    def validate_codigo_barras(self, value):
        if not value.isdigit() or len(value) != 13:
            raise serializers.ValidationError("Código de barras deve conter exatamente 13 dígitos numéricos.")
        return value
    
    def create(self, validated_data):
        nova_categoria = validated_data.pop('nova_categoria', None)
        categoria_id = validated_data.pop('categoria_id', None)
        
        # Se foi fornecida uma nova categoria, cria ela primeiro
        if nova_categoria:
            request = self.context.get('request')
            categoria = Categoria.objects.create(
                nome=nova_categoria,
                usuario=request.user
            )
            validated_data['categoria'] = categoria
        elif categoria_id:
            # Se foi fornecido um ID de categoria, busca ela
            try:
                categoria = Categoria.objects.get(id=categoria_id, usuario=self.context['request'].user)
                validated_data['categoria'] = categoria
            except Categoria.DoesNotExist:
                raise serializers.ValidationError("Categoria não encontrada.")
        
        # Cria o produto
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = MovimentacaoEstoque
        fields = [
            'id',
            'produto',
            'produto_nome',
            'tipo',
            'tipo_display',
            'quantidade',
            'estoque_anterior',
            'estoque_atual',
            'data_movimentacao',
            'observacao',
        ]
        read_only_fields = ['id', 'estoque_anterior', 'estoque_atual', 'data_movimentacao', 'produto_nome', 'tipo_display']
