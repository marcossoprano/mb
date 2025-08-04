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
        
        # Valida produtos e quantidades
        produtos_validados = []
        for item in produtos_quantidades:
            produto_id = item.get('produto_id')
            quantidade = item.get('quantidade', 0)
            
            if not produto_id or quantidade <= 0:
                return Response(
                    {'erro': 'Produto ID e quantidade são obrigatórios e quantidade deve ser > 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                produto = Produto.objects.get(idProduto=produto_id, usuario=request.user)
                if produto.estoque_atual < quantidade:
                    return Response(
                        {'erro': f'Estoque insuficiente para o produto {produto.nome}. Disponível: {produto.estoque_atual}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                produtos_validados.append({
                    'produto': produto,
                    'quantidade': quantidade
                })
            except Produto.DoesNotExist:
                return Response(
                    {'erro': f'Produto com ID {produto_id} não encontrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Prepara endereços (origem + destinos)
        # A rota sempre começa e termina na empresa (origem)
        endereco_origem = request.user.endereco_completo()
        enderecos = [endereco_origem] + serializer.validated_data['enderecos_destino']
        
        # Otimiza a rota (inclui retorno automático à origem/empresa)
        service = RotaOtimizacaoService()
        resultado = service.otimizar_rota(enderecos, veiculo, produtos_quantidades)
        
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
        service = RotaOtimizacaoService()
        
        try:
            # Obtém preços para ambos os tipos
            preco_diesel = service.obter_preco_combustivel('diesel')
            preco_gasolina = service.obter_preco_combustivel('gasolina')
            
            return Response({
                'diesel': preco_diesel,
                'gasolina': preco_gasolina,
                'unidade': 'R$/L',
                'fonte': 'combustivelapi.com.br',
                'atualizado_em': '2024-01-20T10:30:00Z'  # TODO: Implementar timestamp real
            })
        except Exception as e:
            return Response({
                'erro': f'Erro ao obter preços de combustível: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
