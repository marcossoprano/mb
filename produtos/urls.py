from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendaViewSet, VendaListView
from .views import (
    ProdutoCreateView,
    ProdutoCreateWithCategoriaView,
    ProdutoListView,
    ProdutoUpdateView,
    ProdutoDeleteView,
    FornecedorListCreateView,
    CategoriaListCreateView,
    CategoriaCreateView,
    MovimentacaoEstoqueListView,
    MovimentacaoEstoqueProdutoListView,
)

router = DefaultRouter()



urlpatterns = [
    path('', include(router.urls)),
    # Rotas Produtos
    path('cadastrar/', ProdutoCreateView.as_view(), name='cadastrar-produto'),
    path('cadastrar-com-categoria/', ProdutoCreateWithCategoriaView.as_view(), name='cadastrar-produto-com-categoria'),
    path('', ProdutoListView.as_view(), name='listar-produtos'),
    # Listagem detalhada de vendas
    path('vendas/listar/', VendaListView.as_view(), name='venda-listar'),
    path('<int:idProduto>/atualizar/', ProdutoUpdateView.as_view(), name='atualizar-produto'),
    path('<int:idProduto>/excluir/', ProdutoDeleteView.as_view(), name='excluir-produto'),

    # Rotas Fornecedores
    path('fornecedores/', FornecedorListCreateView.as_view(), name='fornecedores'),

    # Rotas Categorias
    path('categorias/', CategoriaListCreateView.as_view(), name='categorias'),
    path('categorias/criar/', CategoriaCreateView.as_view(), name='criar-categoria'),

    # Rotas Movimentação de Estoque (apenas consulta)
    path('movimentacoes/', MovimentacaoEstoqueListView.as_view(), name='listar-movimentacoes'),
    path('movimentacoes/produto/<int:produto_id>/', MovimentacaoEstoqueProdutoListView.as_view(), name='movimentacoes-produto'),
]
