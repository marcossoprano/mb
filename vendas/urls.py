from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'vendas'

urlpatterns = [
    # CRUD de Vendas
    path('', views.VendaListView.as_view(), name='venda-list'),
    path('create/', views.VendaCreateView.as_view(), name='venda-create'),
    path('<int:id>/', views.VendaDetailView.as_view(), name='venda-detail'),
    path('<int:id>/update/', views.VendaUpdateView.as_view(), name='venda-update'),
    path('<int:id>/delete/', views.VendaDeleteView.as_view(), name='venda-delete'),
    
    # Ações específicas de venda
    path('<int:pk>/finalizar/', views.VendaFinalizarView.as_view(), name='venda-finalizar'),
    path('<int:pk>/cancelar/', views.VendaCancelarView.as_view(), name='venda-cancelar'),
    
    # Estatísticas
    path('estatisticas/', views.VendaEstatisticasView.as_view(), name='venda-estatisticas'),
    
    # CRUD de Itens de Venda
    path('<int:venda_id>/itens/', views.ItemVendaCreateView.as_view(), name='item-venda-create'),
    path('<int:venda_id>/itens/<int:id>/', views.ItemVendaUpdateView.as_view(), name='item-venda-update'),
    path('<int:venda_id>/itens/<int:id>/delete/', views.ItemVendaDeleteView.as_view(), name='item-venda-delete'),
]
