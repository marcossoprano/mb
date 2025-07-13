from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Produto, Fornecedor, Categoria, MovimentacaoEstoque
from .serializers import (
    ProdutoSerializer, 
    FornecedorSerializer, 
    CategoriaSerializer,
    CategoriaCreateSerializer,
    ProdutoCreateWithCategoriaSerializer,
    MovimentacaoEstoqueSerializer
)


# Produto CRUD (mantido igual ao seu)

class ProdutoCreateView(generics.CreateAPIView):
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        produto = serializer.save(usuario=self.request.user)
        # Registra a movimentação inicial se houver estoque
        if produto.estoque_atual > 0:
            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo='entrada',
                quantidade=produto.estoque_atual,
                estoque_anterior=0,
                estoque_atual=produto.estoque_atual,
                observacao='Cadastro inicial do produto',
                usuario=self.request.user
            )


class ProdutoCreateWithCategoriaView(generics.CreateAPIView):
    """View para criar produto com possibilidade de criar categoria inline"""
    serializer_class = ProdutoCreateWithCategoriaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        produto = serializer.save(usuario=self.request.user)
        # Registra a movimentação inicial se houver estoque
        if produto.estoque_atual > 0:
            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo='entrada',
                quantidade=produto.estoque_atual,
                estoque_anterior=0,
                estoque_atual=produto.estoque_atual,
                observacao='Cadastro inicial do produto',
                usuario=self.request.user
            )


class ProdutoListView(generics.ListAPIView):
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['categoria']  # filtro exato por categoria
    search_fields = ['nome', 'marca']

    def get_queryset(self):
        return Produto.objects.filter(usuario=self.request.user)

class ProdutoUpdateView(generics.UpdateAPIView):
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'idProduto'

    def get_queryset(self):
        return Produto.objects.filter(usuario=self.request.user)

    def perform_update(self, serializer):
        # Captura o produto antes da atualização
        produto_anterior = self.get_object()
        estoque_anterior = produto_anterior.estoque_atual
        
        # Salva as mudanças
        produto = serializer.save()
        estoque_atual = produto.estoque_atual
        
        # Verifica se houve mudança no estoque
        if estoque_anterior != estoque_atual:
            diferenca = estoque_atual - estoque_anterior
            
            if diferenca > 0:
                # Entrada de estoque
                tipo = 'entrada'
                observacao = f'Adição de {diferenca} unidades ao estoque'
            else:
                # Saída de estoque
                tipo = 'saida'
                observacao = f'Remoção de {abs(diferenca)} unidades do estoque'
            
            # Registra a movimentação
            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo=tipo,
                quantidade=abs(diferenca),
                estoque_anterior=estoque_anterior,
                estoque_atual=estoque_atual,
                observacao=observacao,
                usuario=self.request.user
            )

class ProdutoDeleteView(generics.DestroyAPIView):
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'idProduto'

    def get_queryset(self):
        return Produto.objects.filter(usuario=self.request.user)


# Views para Fornecedor
class FornecedorListCreateView(generics.ListCreateAPIView):
    serializer_class = FornecedorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Fornecedor.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


# Views para Categoria
class CategoriaListCreateView(generics.ListCreateAPIView):
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Categoria.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class CategoriaCreateView(generics.CreateAPIView):
    """View específica para criação de categoria com validação"""
    serializer_class = CategoriaCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


# Views para Movimentação de Estoque (apenas consulta)
class MovimentacaoEstoqueListView(generics.ListAPIView):
    """Lista todas as movimentações de estoque do usuário"""
    serializer_class = MovimentacaoEstoqueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo', 'produto']
    search_fields = ['produto__nome', 'observacao']

    def get_queryset(self):
        return MovimentacaoEstoque.objects.filter(usuario=self.request.user)


class MovimentacaoEstoqueProdutoListView(generics.ListAPIView):
    """Lista movimentações de um produto específico"""
    serializer_class = MovimentacaoEstoqueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        produto_id = self.kwargs.get('produto_id')
        return MovimentacaoEstoque.objects.filter(
            produto_id=produto_id,
            usuario=self.request.user
        )
