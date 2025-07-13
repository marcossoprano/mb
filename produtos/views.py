from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Produto, Fornecedor, Categoria
from .serializers import (
    ProdutoSerializer, 
    FornecedorSerializer, 
    CategoriaSerializer,
    CategoriaCreateSerializer,
    ProdutoCreateWithCategoriaSerializer
)


# Produto CRUD (mantido igual ao seu)

class ProdutoCreateView(generics.CreateAPIView):
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class ProdutoCreateWithCategoriaView(generics.CreateAPIView):
    """View para criar produto com possibilidade de criar categoria inline"""
    serializer_class = ProdutoCreateWithCategoriaSerializer
    permission_classes = [IsAuthenticated]


class ProdutoListView(generics.ListAPIView):
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['categoria']  # filtro exato por categoria
    search_fields = ['nome', 'marca']

    def get_queryset(self):
        return Produto.objects.filter(usuario=self.request.user)

# View para testes sem autenticação (REMOVER EM PRODUÇÃO)
class ProdutoTestListView(generics.ListAPIView):
    serializer_class = ProdutoSerializer
    permission_classes = [AllowAny]  # Permite acesso sem autenticação

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['categoria']
    search_fields = ['nome', 'marca']

    def get_queryset(self):
        # Retorna todos os produtos para teste
        return Produto.objects.all()



class ProdutoUpdateView(generics.UpdateAPIView):
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'idProduto'

    def get_queryset(self):
        return Produto.objects.filter(usuario=self.request.user)

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
