from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Veiculo, Rota
from .serializers import (
    VeiculoSerializer, 
    RotaSerializer, 
    RotaCreateSerializer, 
    RotaStatusUpdateSerializer
)
from .services import RotaOtimizacaoService

# Instância singleton para reutilizar caches entre requisições
_rota_service_instance = None

def get_rota_service():
    """Retorna instância singleton do serviço de otimização"""
    global _rota_service_instance
    if _rota_service_instance is None:
        _rota_service_instance = RotaOtimizacaoService()
    return _rota_service_instance
from produtos.models import Produto, MovimentacaoEstoque

class VeiculoCreateView(generics.CreateAPIView):
    """Criar um novo veículo"""
    serializer_class = VeiculoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class VeiculoListView(generics.ListAPIView):
    """Listar todos os veículos do usuário"""
    serializer_class = VeiculoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo_combustivel']
    search_fields = ['nome']

    def get_queryset(self):
        return Veiculo.objects.filter(usuario=self.request.user)

class VeiculoDetailView(generics.RetrieveAPIView):
    """Obter detalhes de um veículo específico"""
    serializer_class = VeiculoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Veiculo.objects.filter(usuario=self.request.user)

class VeiculoUpdateView(generics.UpdateAPIView):
    """Atualizar um veículo"""
    serializer_class = VeiculoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Veiculo.objects.filter(usuario=self.request.user)

class VeiculoDeleteView(generics.DestroyAPIView):
    """Excluir um veículo"""
    serializer_class = VeiculoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Veiculo.objects.filter(usuario=self.request.user)

class RotaCreateView(generics.CreateAPIView):
    """Criar uma nova rota otimizada"""
    serializer_class = RotaCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validações
        veiculo_id = serializer.validated_data.get('veiculo_id')
        produtos_quantidades = serializer.validated_data['produtos_quantidades']
        nome_motorista = serializer.validated_data.get('nome_motorista', '')
        preco_combustivel = serializer.validated_data.get('preco_combustivel')
        
        # Verifica se o veículo pertence ao usuário (se fornecido)
        veiculo = None
        if veiculo_id:
            try:
                veiculo = Veiculo.objects.get(id=veiculo_id, usuario=request.user)
            except Veiculo.DoesNotExist:
                return Response(
                    {'erro': 'Veículo não encontrado ou não pertence ao usuário'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Valida produtos e quantidades (OTIMIZADO - consulta em lote)
        produtos_validados = []
        
        # Extrai IDs dos produtos para consulta em lote
        produto_ids = [item.get('produto_id') for item in produtos_quantidades if item.get('produto_id')]
        quantidades = [item.get('quantidade', 0) for item in produtos_quantidades]
        
        # Validações básicas
        if not produto_ids or any(q <= 0 for q in quantidades):
            return Response(
                {'erro': 'Produto ID e quantidade são obrigatórios e quantidade deve ser > 0'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Consulta em lote todos os produtos
        try:
            produtos_queryset = Produto.objects.filter(
                idProduto__in=produto_ids, 
                usuario=request.user
            ).values('idProduto', 'nome', 'estoque_atual')
            
            # Cria dicionário para acesso rápido
            produtos_dict = {p['idProduto']: p for p in produtos_queryset}
            
            # Valida cada produto
            for i, item in enumerate(produtos_quantidades):
                produto_id = item.get('produto_id')
                quantidade = item.get('quantidade', 0)
                
                if produto_id not in produtos_dict:
                    return Response(
                        {'erro': f'Produto com ID {produto_id} não encontrado'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                produto_data = produtos_dict[produto_id]
                if produto_data['estoque_atual'] < quantidade:
                    return Response(
                        {'erro': f'Estoque insuficiente para o produto {produto_data["nome"]}. Disponível: {produto_data["estoque_atual"]}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Busca o objeto completo do produto para uso posterior
                produto = Produto.objects.get(idProduto=produto_id, usuario=request.user)
                produtos_validados.append({
                    'produto': produto,
                    'quantidade': quantidade
                })
                
        except Exception as e:
            return Response(
                {'erro': f'Erro na validação de produtos: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepara endereços (origem + destinos)
        # A rota sempre começa e termina na empresa (origem)
        endereco_origem = request.user.endereco_completo()
        enderecos = [endereco_origem] + serializer.validated_data['enderecos_destino']
        
        # Otimiza a rota (inclui retorno automático à origem/empresa)
        # Usa instância singleton para reutilizar caches
        service = get_rota_service()
        resultado = service.otimizar_rota(enderecos, veiculo, produtos_quantidades, preco_combustivel)
        
        if not resultado['sucesso']:
            return Response(
                {'erro': f'Erro na otimização da rota: {resultado.get("erro", "Erro desconhecido")}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Cria a rota
        rota = Rota.objects.create(
            enderecos_otimizados=resultado['enderecos_otimizados'],
            coordenadas_otimizadas=resultado['coordenadas_otimizadas'],
            distancia_total_km=resultado['distancia_total_km'],
            tempo_estimado_minutos=resultado['tempo_estimado_minutos'],
            veiculo=veiculo,
            nome_motorista=nome_motorista if nome_motorista else None,
            valor_rota=resultado['valor_rota'],
            preco_combustivel_usado=resultado['preco_combustivel_usado'],
            produtos_quantidades=produtos_quantidades,
            link_maps=resultado['link_maps'],
            usuario=request.user
        )
        
        # Atualiza estoque dos produtos
        for item in produtos_validados:
            produto = item['produto']
            quantidade = item['quantidade']
            estoque_anterior = produto.estoque_atual
            produto.estoque_atual -= quantidade
            produto.save()
            
            # Registra movimentação de estoque
            motorista_info = rota.nome_motorista if rota.nome_motorista else 'Sem motorista'
            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo='saida',
                quantidade=quantidade,
                estoque_anterior=estoque_anterior,
                estoque_atual=produto.estoque_atual,
                observacao=f'Saída para rota {rota.id} - {motorista_info}',
                usuario=request.user
            )
        
        # Retorna a rota criada
        rota_serializer = RotaSerializer(rota)
        return Response(rota_serializer.data, status=status.HTTP_201_CREATED)

class RotaListView(generics.ListAPIView):
    """Listar todas as rotas do usuário"""
    serializer_class = RotaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'veiculo']
    search_fields = ['nome_motorista']

    def get_queryset(self):
        return Rota.objects.filter(usuario=self.request.user)

class RotaDetailView(generics.RetrieveAPIView):
    """Obter detalhes de uma rota específica"""
    serializer_class = RotaSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Rota.objects.filter(usuario=self.request.user)

class RotaStatusUpdateView(generics.UpdateAPIView):
    """Atualizar apenas o status de uma rota"""
    serializer_class = RotaStatusUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Rota.objects.filter(usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        rota = self.get_object()
        serializer = self.get_serializer(rota, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        rota.status = serializer.validated_data['status']
        rota.save()
        
        rota_serializer = RotaSerializer(rota)
        return Response(rota_serializer.data)

class RotaDeleteView(generics.DestroyAPIView):
    """Excluir uma rota"""
    serializer_class = RotaSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Rota.objects.filter(usuario=self.request.user)

class PrecosCombustivelView(APIView):
    """Obter preços atuais de combustível"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        service = get_rota_service()  # Usa singleton para cache
        
        try:
            # Obtém preços para todos os tipos de combustível
            preco_diesel = service.obter_preco_combustivel('diesel')
            preco_gasolina = service.obter_preco_combustivel('gasolina')
            preco_etanol = service.obter_preco_combustivel('etanol')
            preco_gnv = service.obter_preco_combustivel('gnv')
            
            return Response({
                'diesel': preco_diesel,
                'gasolina': preco_gasolina,
                'etanol': preco_etanol,
                'gnv': preco_gnv,
                'unidades': {
                    'diesel': 'R$/L',
                    'gasolina': 'R$/L',
                    'etanol': 'R$/L',
                    'gnv': 'R$/m³'
                },
                'fonte': 'combustivelapi.com.br',
                'atualizado_em': '2024-01-20T10:30:00Z'  # TODO: Implementar timestamp real
            })
        except Exception as e:
            return Response({
                'erro': f'Erro ao obter preços de combustível: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
