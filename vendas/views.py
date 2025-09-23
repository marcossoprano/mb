from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Venda, ItemVenda
from .serializers import (
    VendaSerializer,
    VendaCreateSerializer,
    VendaUpdateSerializer,
    VendaFinalizarSerializer,
    VendaCancelarSerializer,
    ItemVendaSerializer
)

class VendaCreateView(generics.CreateAPIView):
    """Criar uma nova venda"""
    serializer_class = VendaCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                venda = serializer.save()
                venda_serializer = VendaSerializer(venda)
                return Response(venda_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'erro': f'Erro ao criar venda: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class VendaListView(generics.ListAPIView):
    """Listar todas as vendas do usuário"""
    serializer_class = VendaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['observacoes']
    ordering_fields = ['data_criacao', 'total']
    ordering = ['-data_criacao']

    def get_queryset(self):
        return Venda.objects.filter(usuario=self.request.user).prefetch_related('itens__produto')

class VendaDetailView(generics.RetrieveAPIView):
    """Obter detalhes de uma venda específica"""
    serializer_class = VendaSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Venda.objects.filter(usuario=self.request.user).prefetch_related('itens__produto')

class VendaUpdateView(generics.UpdateAPIView):
    """Atualizar uma venda (apenas observações e status)"""
    serializer_class = VendaUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Venda.objects.filter(usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        venda = self.get_object()
        serializer = self.get_serializer(venda, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                serializer.save()
                venda_serializer = VendaSerializer(venda)
                return Response(venda_serializer.data)
        except Exception as e:
            return Response(
                {'erro': f'Erro ao atualizar venda: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class VendaDeleteView(generics.DestroyAPIView):
    """Excluir uma venda"""
    serializer_class = VendaSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Venda.objects.filter(usuario=self.request.user)

    def destroy(self, request, *args, **kwargs):
        venda = self.get_object()
        
        # Só permite exclusão de vendas pendentes ou canceladas
        if venda.status == 'finalizada':
            return Response(
                {'erro': 'Não é possível excluir vendas finalizadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        venda.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class VendaFinalizarView(APIView):
    """Finalizar uma venda (registra movimentações de estoque)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        venda = get_object_or_404(Venda, id=pk, usuario=request.user)
        
        serializer = VendaFinalizarSerializer(
            data=request.data,
            context={'venda': venda}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                venda.finalizar_venda()
                venda_serializer = VendaSerializer(venda)
                return Response(venda_serializer.data)
        except ValueError as e:
            return Response(
                {'erro': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'erro': f'Erro ao finalizar venda: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VendaCancelarView(APIView):
    """Cancelar uma venda"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        venda = get_object_or_404(Venda, id=pk, usuario=request.user)
        
        serializer = VendaCancelarSerializer(
            data=request.data,
            context={'venda': venda}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                venda.cancelar_venda()
                venda_serializer = VendaSerializer(venda)
                return Response(venda_serializer.data)
        except ValueError as e:
            return Response(
                {'erro': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'erro': f'Erro ao cancelar venda: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ItemVendaCreateView(generics.CreateAPIView):
    """Adicionar item a uma venda"""
    serializer_class = ItemVendaSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        venda_id = kwargs.get('venda_id')
        venda = get_object_or_404(Venda, id=venda_id, usuario=request.user)
        
        # Verifica se a venda pode ser modificada
        if venda.status != 'pendente':
            return Response(
                {'erro': 'Apenas vendas pendentes podem ser modificadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                item = serializer.save(venda=venda)
                
                # Recalcula o total da venda
                venda.total = venda.calcular_total()
                venda.save()
                
                item_serializer = ItemVendaSerializer(item)
                return Response(item_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'erro': f'Erro ao adicionar item: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ItemVendaUpdateView(generics.UpdateAPIView):
    """Atualizar item de uma venda"""
    serializer_class = ItemVendaSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        venda_id = self.kwargs.get('venda_id')
        return ItemVenda.objects.filter(venda_id=venda_id, venda__usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        item = self.get_object()
        
        # Verifica se a venda pode ser modificada
        if item.venda.status != 'pendente':
            return Response(
                {'erro': 'Apenas vendas pendentes podem ser modificadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                serializer.save()
                
                # Recalcula o total da venda
                item.venda.total = item.venda.calcular_total()
                item.venda.save()
                
                return Response(serializer.data)
        except Exception as e:
            return Response(
                {'erro': f'Erro ao atualizar item: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ItemVendaDeleteView(generics.DestroyAPIView):
    """Remover item de uma venda"""
    serializer_class = ItemVendaSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        venda_id = self.kwargs.get('venda_id')
        return ItemVenda.objects.filter(venda_id=venda_id, venda__usuario=self.request.user)

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        
        # Verifica se a venda pode ser modificada
        if item.venda.status != 'pendente':
            return Response(
                {'erro': 'Apenas vendas pendentes podem ser modificadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                venda = item.venda
                item.delete()
                
                # Recalcula o total da venda
                venda.total = venda.calcular_total()
                venda.save()
                
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'erro': f'Erro ao remover item: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VendaEstatisticasView(APIView):
    """Obter estatísticas das vendas do usuário"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vendas = Venda.objects.filter(usuario=request.user)
        
        total_vendas = vendas.count()
        vendas_finalizadas = vendas.filter(status='finalizada').count()
        vendas_pendentes = vendas.filter(status='pendente').count()
        vendas_canceladas = vendas.filter(status='cancelada').count()
        
        # Calcula totais
        total_faturado = sum(venda.total for venda in vendas.filter(status='finalizada'))
        total_pendente = sum(venda.total for venda in vendas.filter(status='pendente'))
        
        # Venda com maior valor
        venda_maior_valor = vendas.filter(status='finalizada').order_by('-total').first()
        
        estatisticas = {
            'total_vendas': total_vendas,
            'vendas_finalizadas': vendas_finalizadas,
            'vendas_pendentes': vendas_pendentes,
            'vendas_canceladas': vendas_canceladas,
            'total_faturado': float(total_faturado) if total_faturado else 0,
            'total_pendente': float(total_pendente) if total_pendente else 0,
            'venda_maior_valor': {
                'id': venda_maior_valor.id,
                'total': float(venda_maior_valor.total),
                'data': venda_maior_valor.data_criacao
            } if venda_maior_valor else None
        }
        
        return Response(estatisticas)
