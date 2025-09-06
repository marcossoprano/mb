from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
import csv
from produtos.models import Produto, Fornecedor, Categoria
from usuarios.models import Usuario
from .importacao import importar_produtos_csv

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exportar_produtos_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="produtos.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Nome', 'Descrição', 'Preço Custo', 'Preço Venda', 'Estoque Mínimo', 'Estoque Atual',
        'Validade', 'Código Barras', 'Data Fabricação', 'Lote', 'Marca', 'Fornecedor', 'Categoria'
    ])

    produtos = Produto.objects.select_related('fornecedor', 'categoria').filter(usuario=request.user)
    for produto in produtos:
        writer.writerow([
            produto.idProduto,
            produto.nome,
            produto.descricao or '',
            produto.preco_custo,
            produto.preco_venda,
            produto.estoque_minimo,
            produto.estoque_atual,
            produto.validade or '',
            produto.codigo_barras or '',
            produto.data_fabricacao or '',
            produto.lote or '',
            produto.marca or '',
            produto.fornecedor.nome if produto.fornecedor else '',
            produto.categoria.nome if produto.categoria else ''
        ])

    return response

# A view de importação já está pronta para ser usada diretamente
# Não precisa de um wrapper extra
