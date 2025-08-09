from django.contrib import admin
from .models import Veiculo, Rota

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo_combustivel', 'eficiencia_km_l', 'usuario', 'data_cadastro']
    list_filter = ['tipo_combustivel', 'data_cadastro']
    search_fields = ['nome', 'usuario__nome']
    readonly_fields = ['data_cadastro', 'data_atualizacao']
    ordering = ['nome']

@admin.register(Rota)
class RotaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome_motorista', 'veiculo', 'distancia_total_km', 'valor_rota', 'status', 'data_geracao', 'usuario']
    list_filter = ['status', 'data_geracao', 'veiculo__tipo_combustivel']
    search_fields = ['nome_motorista', 'usuario__nome', 'veiculo__nome']
    readonly_fields = ['data_geracao', 'enderecos_otimizados', 'coordenadas_otimizadas', 'distancia_total_km', 'tempo_estimado_minutos', 'valor_rota', 'link_maps']
    ordering = ['-data_geracao']
