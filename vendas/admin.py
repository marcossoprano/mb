from django.contrib import admin
from .models import Venda, ItemVenda

class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['produto', 'quantidade', 'preco_unitario', 'subtotal']

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'data_criacao', 'total', 'status', 'total_itens']
    list_filter = ['status', 'data_criacao', 'usuario']
    search_fields = ['id', 'usuario__nome', 'observacoes']
    readonly_fields = ['id', 'data_criacao', 'data_atualizacao', 'total']
    inlines = [ItemVendaInline]
    
    def total_itens(self, obj):
        return obj.itens.count()
    total_itens.short_description = 'Total de Itens'

@admin.register(ItemVenda)
class ItemVendaAdmin(admin.ModelAdmin):
    list_display = ['id', 'venda', 'produto', 'quantidade', 'preco_unitario', 'subtotal']
    list_filter = ['venda__status', 'venda__usuario']
    search_fields = ['produto__nome', 'venda__id']
    readonly_fields = ['subtotal']
