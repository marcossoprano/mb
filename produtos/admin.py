from django.contrib import admin
from .models import Produto, Fornecedor, Categoria, MovimentacaoEstoque

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'email', 'usuario']
    list_filter = ['usuario']
    search_fields = ['nome', 'email']

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'usuario']
    list_filter = ['usuario']
    search_fields = ['nome']

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo_barras', 'marca', 'estoque_atual', 'estoque_minimo', 'preco_venda', 'categoria', 'usuario']
    list_filter = ['categoria', 'fornecedor', 'usuario']
    search_fields = ['nome', 'codigo_barras', 'marca']
    readonly_fields = ['data_cadastro', 'data_atualizacao']

@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo', 'quantidade', 'estoque_anterior', 'estoque_atual', 'data_movimentacao', 'usuario']
    list_filter = ['tipo', 'data_movimentacao', 'usuario', 'produto']
    search_fields = ['produto__nome', 'observacao']
    readonly_fields = ['data_movimentacao', 'estoque_anterior', 'estoque_atual']
    date_hierarchy = 'data_movimentacao'
