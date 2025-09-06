from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import csv
from io import TextIOWrapper
from produtos.models import Produto, Fornecedor, Categoria

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def importar_produtos_csv(request):
    fornecedor_id = request.data.get('fornecedor_id')
    arquivo = request.FILES.get('arquivo')
    if not fornecedor_id or not arquivo:
        return Response({'erro': 'Fornecedor e arquivo são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fornecedor = Fornecedor.objects.get(id=fornecedor_id, usuario=request.user)
    except Fornecedor.DoesNotExist:
        return Response({'erro': 'Fornecedor não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    produtos_criados = []
    erros = []
    reader = csv.DictReader(TextIOWrapper(arquivo, encoding='utf-8'))
    with transaction.atomic():
        for i, row in enumerate(reader, start=2):
            try:
                produto = Produto(
                    nome=row.get('Nome'),
                    preco_custo=row.get('Preço Custo'),
                    preco_venda=row.get('Preço Venda'),
                    estoque_minimo=row.get('Estoque Mínimo'),
                    estoque_atual=row.get('Estoque Atual'),
                    validade=row.get('Validade') or None,
                    codigo_barras=row.get('Código Barras') or None,
                    descricao=row.get('Descrição') or '',
                    data_fabricacao=row.get('Data Fabricação') or None,
                    lote=row.get('Lote') or '',
                    marca=row.get('Marca') or '',
                    fornecedor=fornecedor,
                    usuario=request.user
                )
                produto.full_clean()
                produto.save()
                produtos_criados.append(produto.nome)
            except Exception as e:
                erros.append(f"Linha {i}: {str(e)}")
    return Response({
        'produtos_importados': produtos_criados,
        'erros': erros
    }, status=status.HTTP_201_CREATED if not erros else status.HTTP_207_MULTI_STATUS)
