from rest_framework import serializers
from .models import Veiculo, Rota
from produtos.models import Produto

class VeiculoSerializer(serializers.ModelSerializer):
    tipo_combustivel_display = serializers.CharField(source='get_tipo_combustivel_display', read_only=True)
    eficiencia_display = serializers.CharField(source='get_eficiencia_display', read_only=True)
    
    class Meta:
        model = Veiculo
        fields = [
            'id', 
            'nome', 
            'tipo_combustivel', 
            'tipo_combustivel_display',
            'eficiencia_km_l',
            'eficiencia_display',
            'data_cadastro', 
            'data_atualizacao'
        ]
        read_only_fields = ['id', 'data_cadastro', 'data_atualizacao']

class RotaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    veiculo_nome = serializers.SerializerMethodField()
    preco_combustivel_na_geracao = serializers.SerializerMethodField()
    
    class Meta:
        model = Rota
        fields = [
            'id',
            'data_geracao',
            'enderecos_otimizados',
            'coordenadas_otimizadas',
            'distancia_total_km',
            'tempo_estimado_minutos',
            'veiculo',
            'veiculo_nome',
            'nome_motorista',
            'valor_rota',
            'preco_combustivel_usado',
            'produtos_quantidades',
            'link_maps',
            'status',
            'status_display',
            'preco_combustivel_na_geracao'
        ]
        read_only_fields = ['id', 'data_geracao', 'enderecos_otimizados', 'coordenadas_otimizadas', 
                           'distancia_total_km', 'tempo_estimado_minutos', 'valor_rota', 'link_maps']
    
    def get_veiculo_nome(self, obj):
        """
        Retorna o nome do veículo ou 'Veículo Padrão' se não houver veículo
        """
        if obj.veiculo:
            return obj.veiculo.nome
        return "Veículo Padrão"
    
    def get_preco_combustivel_na_geracao(self, obj):
        """
        Retorna o preço do combustível usado na geração da rota
        """
        if obj.preco_combustivel_usado:
            return float(obj.preco_combustivel_usado)
        
        # Fallback: calcula o preço do combustível usado na geração da rota
        try:
            # Se tem veículo, usa o consumo dele
            if obj.veiculo and obj.distancia_total_km > 0 and obj.veiculo.eficiencia_km_l > 0:
                eficiencia = float(obj.veiculo.eficiencia_km_l)
                
                if obj.veiculo.tipo_combustivel == 'gnv':
                    # Para GNV: eficiência em km/m³
                    metros_cubicos_consumidos = float(obj.distancia_total_km) / eficiencia
                    if metros_cubicos_consumidos > 0:
                        preco_por_m3 = float(obj.valor_rota) / metros_cubicos_consumidos
                        return round(preco_por_m3, 2)
                else:
                    # Para outros combustíveis: eficiência em km/L
                    litros_consumidos = float(obj.distancia_total_km) / eficiencia
                    if litros_consumidos > 0:
                        preco_por_litro = float(obj.valor_rota) / litros_consumidos
                        return round(preco_por_litro, 2)
            # Se não tem veículo, usa consumo padrão (8.0 km/L)
            elif obj.distancia_total_km > 0:
                km_por_litro_padrao = 8.0  # km/L padrão
                litros_consumidos = float(obj.distancia_total_km) / km_por_litro_padrao
                if litros_consumidos > 0:
                    preco_por_litro = float(obj.valor_rota) / litros_consumidos
                    return round(preco_por_litro, 2)
        except:
            pass
        
        # Fallback: retorna None se não conseguir calcular
        return None

class RotaCreateSerializer(serializers.Serializer):
    enderecos_destino = serializers.ListField(
        child=serializers.CharField(max_length=500),
        min_length=1,
        help_text="Lista de endereços de destino"
    )
    nome_motorista = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True,
        help_text="Nome do motorista (opcional)"
    )
    veiculo_id = serializers.IntegerField(
        required=False,
        help_text="ID do veículo (opcional - será usado valor padrão se não informado)"
    )
    preco_combustivel = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        min_value=0.01,
        help_text="Preço do combustível por litro ou m³ (opcional - será usado valor base se não informado)"
    )
    produtos_quantidades = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de produtos com suas quantidades"
    )

class RotaStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Rota.STATUS_CHOICES) 