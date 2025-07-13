from django.urls import path
from .views import (
    ProdutoCreateView,
    ProdutoCreateWithCategoriaView,
    ProdutoListView,
    ProdutoTestListView,
    ProdutoUpdateView,
    ProdutoDeleteView,
    FornecedorListCreateView,
    CategoriaListCreateView,
    CategoriaCreateView,
)

urlpatterns = [
    # Rotas Produtos
    path('cadastrar/', ProdutoCreateView.as_view(), name='cadastrar-produto'),
    path('cadastrar-com-categoria/', ProdutoCreateWithCategoriaView.as_view(), name='cadastrar-produto-com-categoria'),
    path('', ProdutoListView.as_view(), name='listar-produtos'),
    path('teste/', ProdutoTestListView.as_view(), name='teste-produtos'),  # REMOVER EM PRODUÇÃO
    path('<int:idProduto>/atualizar/', ProdutoUpdateView.as_view(), name='atualizar-produto'),
    path('<int:idProduto>/excluir/', ProdutoDeleteView.as_view(), name='excluir-produto'),

    # Rotas Fornecedores
    path('fornecedores/', FornecedorListCreateView.as_view(), name='fornecedores'),

    # Rotas Categorias
    path('categorias/', CategoriaListCreateView.as_view(), name='categorias'),
    path('categorias/criar/', CategoriaCreateView.as_view(), name='criar-categoria'),
]
