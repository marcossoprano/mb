from django.urls import path
from .views import (
    VeiculoCreateView,
    VeiculoListView,
    VeiculoDetailView,
    VeiculoUpdateView,
    VeiculoDeleteView,
    RotaCreateView,
    RotaListView,
    RotaDetailView,
    RotaStatusUpdateView,
    RotaDeleteView,
    PrecosCombustivelView
)

urlpatterns = [
    # CRUD de Veículos
    path('veiculos/', VeiculoListView.as_view(), name='veiculo-list'),
    path('veiculos/criar/', VeiculoCreateView.as_view(), name='veiculo-create'),
    path('veiculos/<int:id>/', VeiculoDetailView.as_view(), name='veiculo-detail'),
    path('veiculos/<int:id>/atualizar/', VeiculoUpdateView.as_view(), name='veiculo-update'),
    path('veiculos/<int:id>/excluir/', VeiculoDeleteView.as_view(), name='veiculo-delete'),
    
    # CRUD de Rotas
    path('rotas/', RotaListView.as_view(), name='rota-list'),
    path('rotas/criar/', RotaCreateView.as_view(), name='rota-create'),
    path('rotas/<int:id>/', RotaDetailView.as_view(), name='rota-detail'),
    path('rotas/<int:id>/status/', RotaStatusUpdateView.as_view(), name='rota-status-update'),
    path('rotas/<int:id>/excluir/', RotaDeleteView.as_view(), name='rota-delete'),
    
    # Preços de Combustível
    path('precos-combustivel/', PrecosCombustivelView.as_view(), name='precos-combustivel'),
] 