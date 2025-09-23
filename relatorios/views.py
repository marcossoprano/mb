from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

from django.db.models import Sum, F, Q
from django.http import HttpResponse
from django.utils.timezone import now
from django.template.loader import render_to_string

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from produtos.models import MovimentacaoEstoque, Produto
from rotas.models import Rota
from vendas.models import Venda, ItemVenda


class RelatorioHTMLView(APIView):
    permission_classes = [IsAuthenticated]

    def get_periodo(self, periodo: str):
        referencia = now()
        if periodo == 'ultimo_ano':
            inicio = referencia - timedelta(days=365)
        elif periodo == 'ultimos_6_meses':
            inicio = referencia - timedelta(days=182)
        elif periodo == 'ultimo_mes':
            inicio = referencia - timedelta(days=30)
        else:
            # default: últimos 30 dias
            inicio = referencia - timedelta(days=30)
        return inicio, referencia

    def extract_neighborhood_from_address(self, address):
        """Extrai o bairro de um endereço usando regex"""
        if not address:
            return "Não informado"
        
        # Padrões específicos para os endereços encontrados
        patterns = [
            # Padrão específico: "Avenida Eraldo Lins Cavalcante, 676, Barro Duro, Maceió - AL, 57045430"
            r',\s*[0-9]+,\s*([^,]+),\s*[^,]+',  # ..., número, Bairro, Cidade
            
            # Padrão específico: "Rua Prof. Silvio de Macedo, 125, Jatiúca"
            r',\s*[0-9]+,\s*([^,]+)$',  # ..., número, Bairro (final)
            
            # Padrões com vírgulas e estado
            r',\s*([^,]+),\s*[A-Z]{2}',  # ..., Bairro, SP
            r'-\s*([^,]+),\s*[A-Z]{2}',  # - Bairro, SP
            
            # Padrões com palavras-chave
            r'Bairro\s+([^,]+)',        # Bairro Nome
            r'Distrito\s+([^,]+)',      # Distrito Nome
            
            # Padrões mais genéricos
            r',\s*([^,]+),\s*[0-9]{5}-[0-9]{3}',  # ..., Bairro, 12345-678
            r'-\s*([^,]+),\s*[0-9]{5}-[0-9]{3}',  # - Bairro, 12345-678
            
            # Padrão para endereços que terminam com cidade
            r',\s*([^,]+),\s*[A-Za-z\s]+$',  # ..., Bairro, Cidade
            
            # Padrão para endereços com números de CEP
            r',\s*([^,]+),\s*[0-9]{5}',  # ..., Bairro, 12345
        ]
        
        for pattern in patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                neighborhood = match.group(1).strip()
                # Filtrar palavras muito comuns que não são bairros
                if neighborhood.lower() not in ['sp', 'rj', 'mg', 'rs', 'pr', 'sc', 'ba', 'go', 'pe', 'ce', 'pa', 'ma', 'al', 'pb', 'rn', 'pi', 'to', 'mt', 'ms', 'ac', 'ro', 'rr', 'ap', 'am', 'df', 'maceió']:
                    # Filtrar números puros
                    if not neighborhood.isdigit():
                        return neighborhood
        
        # Se não encontrou com regex, tentar extrair a penúltima parte do endereço
        parts = [part.strip() for part in address.split(',')]
        if len(parts) >= 2:
            # Pegar a penúltima parte (geralmente é o bairro)
            potential_neighborhood = parts[-2]
            if potential_neighborhood and len(potential_neighborhood) > 2 and not potential_neighborhood.isdigit():
                return potential_neighborhood
        
        return "Não identificado"

    def get(self, request):
        # Query params: periodo=ultimo_ano|ultimos_6_meses|ultimo_mes|custom & inicio=YYYY-MM-DD & fim=YYYY-MM-DD
        periodo = request.query_params.get('periodo', 'ultimo_mes')
        if periodo == 'custom':
            inicio_str = request.query_params.get('inicio')
            fim_str = request.query_params.get('fim')
            try:
                inicio = datetime.fromisoformat(inicio_str)
                fim = datetime.fromisoformat(fim_str)
            except Exception:
                return HttpResponse('Parâmetros de data inválidos', status=400)
        else:
            inicio, fim = self.get_periodo(periodo)

        usuario = request.user

        # ===== COLETA DE DADOS =====
        
        # Movimentações de estoque
        movs = MovimentacaoEstoque.objects.filter(
            usuario=usuario,
            data_movimentacao__range=(inicio, fim)
        ).select_related('produto')

        total_entradas = movs.filter(tipo='entrada').aggregate(total=Sum('quantidade'))['total'] or 0
        total_saidas = movs.filter(tipo='saida').aggregate(total=Sum('quantidade'))['total'] or 0

        # Entradas/Saídas detalhadas por produto
        entradas_qs = (
            movs.filter(tipo='entrada')
            .select_related('produto')  # Otimizar query
            .values('produto__idProduto', 'produto__nome')
            .annotate(total=Sum('quantidade'))
            .order_by('-total')
        )
        saidas_qs = (
            movs.filter(tipo='saida')
            .select_related('produto')  # Otimizar query
            .values('produto__idProduto', 'produto__nome')
            .annotate(total=Sum('quantidade'))
            .order_by('-total')
        )


        # Rotas
        rotas = Rota.objects.filter(usuario=usuario, data_geracao__range=(inicio, fim))
        num_rotas = rotas.count()
        rotas_concluidas = rotas.filter(status='concluido')
        num_rotas_concluidas = rotas_concluidas.count()

        # Vendas
        vendas = Venda.objects.filter(
            usuario=usuario,
            data_criacao__range=(inicio, fim),
            status='finalizada'
        ).select_related()

        # ===== ANÁLISE DE DADOS =====

        # Top bairros mais visitados - usar todas as rotas já que não há rotas concluídas
        neighborhood_counter = Counter()
        
        # Processar todas as rotas (não apenas concluídas)
        for rota in rotas:
            enderecos = rota.enderecos_otimizados or []
            if len(enderecos) > 2:
                # Analisar apenas endereços de entrega (excluir origem e destino da loja)
                enderecos_entrega = enderecos[1:-1]
                for endereco in enderecos_entrega:
                    neighborhood = self.extract_neighborhood_from_address(endereco)
                    neighborhood_counter[neighborhood] += 1

        top_neighborhoods = neighborhood_counter.most_common(10)

        # Produtos enviados em rotas concluídas
        envio_por_produto = defaultdict(int)
        produtos_concluidos = {}
        total_vendas_rotas = 0
        
        for rota in rotas_concluidas:
            pq = rota.produtos_quantidades or {}
            for pid_str, qtd in pq.items():
                try:
                    pid = int(pid_str)
                    envio_por_produto[pid] += int(qtd)
                    
                    # Buscar produto para calcular valor de venda
                    if pid not in produtos_concluidos:
                        try:
                            produto = Produto.objects.get(idProduto=pid, usuario=usuario)
                            produtos_concluidos[pid] = produto
                            total_vendas_rotas += int(qtd) * float(produto.preco_venda)
                        except Produto.DoesNotExist:
                            pass
                except (ValueError, TypeError):
                    continue

        # Produtos vendidos em vendas diretas
        vendas_por_produto = defaultdict(int)
        total_vendas_diretas = 0
        
        for venda in vendas:
            total_vendas_diretas += float(venda.total)
            for item in venda.itens.all():
                vendas_por_produto[item.produto.idProduto] += item.quantidade

        # Produtos mais/menos vendidos no total (rotas + vendas)
        total_vendas_por_produto = defaultdict(int)
        for pid, qtd in envio_por_produto.items():
            total_vendas_por_produto[pid] += qtd
        for pid, qtd in vendas_por_produto.items():
            total_vendas_por_produto[pid] += qtd

        # Resolver nomes de produtos - buscar todos os produtos do usuário para garantir mapeamento completo
        todos_produtos_ids = set(envio_por_produto.keys()) | set(vendas_por_produto.keys())
        produtos_usuario = Produto.objects.filter(usuario=usuario, idProduto__in=todos_produtos_ids)
        id_to_nome = {p.idProduto: p.nome for p in produtos_usuario}
        
        # Debug: verificar se todos os produtos foram encontrados
        produtos_nao_encontrados = todos_produtos_ids - set(id_to_nome.keys())
        if produtos_nao_encontrados:
            print(f"Produtos não encontrados: {produtos_nao_encontrados}")
            # Adicionar produtos não encontrados com nome genérico
            for pid in produtos_nao_encontrados:
                id_to_nome[pid] = f"Produto ID {pid}"

        # Top produtos mais/menos vendidos
        top_produtos_vendidos = sorted(total_vendas_por_produto.items(), key=lambda x: x[1], reverse=True)[:10]
        menos_produtos_vendidos = sorted(total_vendas_por_produto.items(), key=lambda x: x[1])[:10]

        # Top produtos mais/menos enviados em rotas
        top_produtos_rotas = sorted(envio_por_produto.items(), key=lambda x: x[1], reverse=True)[:10]
        menos_produtos_rotas = sorted(envio_por_produto.items(), key=lambda x: x[1])[:10]

        # Preparar dados das rotas com novas colunas
        rotas_data = []
        total_custo = 0
        total_vendas_rotas_detalhado = 0
        
        for rota in rotas:
            veiculo_nome = rota.veiculo.nome if rota.veiculo else 'Veículo Padrão'
            motorista = rota.nome_motorista or 'Sem motorista'
            data_formatada = rota.data_geracao.strftime('%d/%m/%Y %H:%M')
            status_display = 'Concluído' if rota.status == 'concluido' else 'Em Progresso'
            
            # Destinos (apenas endereços de entrega, excluindo origem e destino da loja)
            enderecos = rota.enderecos_otimizados or []
            if len(enderecos) > 2:
                # Remove primeiro (origem da loja) e último (retorno à loja)
                destinos_reais = enderecos[1:-1]
                destinos = ', '.join(destinos_reais)
            elif len(enderecos) == 2:
                # Apenas origem e destino da loja, sem entregas
                destinos = 'Sem entregas'
            elif len(enderecos) == 1:
                # Apenas origem da loja
                destinos = 'Sem entregas'
            else:
                destinos = 'Sem destinos'
            
            # Calcular valor total de vendas desta rota
            valor_vendas_rota = 0
            if rota.status == 'concluido':
                pq = rota.produtos_quantidades or {}
                for pid_str, qtd in pq.items():
                    try:
                        pid = int(pid_str)
                        produto = produtos_concluidos.get(pid)
                        if produto:
                            valor_vendas_rota += int(qtd) * float(produto.preco_venda)
                    except (ValueError, TypeError):
                        continue
            
            # Calcular lucro (vendas - custo)
            lucro = valor_vendas_rota - float(rota.valor_rota)
            
            total_custo += float(rota.valor_rota)
            total_vendas_rotas_detalhado += valor_vendas_rota
            
            rotas_data.append({
                'id': rota.id,
                'distancia': f"{rota.distancia_total_km} km",
                'destinos': destinos,
                'veiculo': veiculo_nome,
                'motorista': motorista,
                'custo': f"R$ {rota.valor_rota:.2f}",
                'vendas': f"R$ {valor_vendas_rota:.2f}",
                'lucro': f"R$ {lucro:.2f}",
                'status': status_display,
                'data': data_formatada
            })

        # Adicionar linha de total na tabela de rotas
        if rotas_data:
            total_lucro_rotas = total_vendas_rotas_detalhado - total_custo
            rotas_data.append({
                'id': 'TOTAL',
                'distancia': '',
                'destinos': '',
                'veiculo': '',
                'motorista': '',
                'custo': f"R$ {total_custo:.2f}",
                'vendas': f"R$ {total_vendas_rotas_detalhado:.2f}",
                'lucro': f"R$ {total_lucro_rotas:.2f}",
                'status': '',
                'data': ''
            })

        # Preparar dados de todas as vendas (diretas + rotas)
        vendas_detalhadas = []
        
        # Vendas diretas
        for venda in vendas:
            for item in venda.itens.all():
                vendas_detalhadas.append({
                    'data': venda.data_criacao.strftime('%d/%m/%Y %H:%M'),
                    'produto': item.produto.nome,
                    'quantidade': item.quantidade,
                    'preco_unitario': f"R$ {item.preco_unitario:.2f}",
                    'subtotal': f"R$ {item.subtotal:.2f}",
                    'tipo': 'Venda Direta',
                    'observacao': f'Venda ID: {venda.id}'
                })
        
        # Vendas em rotas (saídas de produtos)
        for rota in rotas_concluidas:
            pq = rota.produtos_quantidades or {}
            for pid_str, qtd in pq.items():
                try:
                    pid = int(pid_str)
                    produto = produtos_concluidos.get(pid)
                    if produto:
                        vendas_detalhadas.append({
                            'data': rota.data_geracao.strftime('%d/%m/%Y %H:%M'),
                            'produto': produto.nome,
                            'quantidade': int(qtd),
                            'preco_unitario': f"R$ {produto.preco_venda:.2f}",
                            'subtotal': f"R$ {int(qtd) * float(produto.preco_venda):.2f}",
                            'tipo': 'Venda em Rota',
                            'observacao': f'Rota ID: {rota.id}'
                        })
                except (ValueError, TypeError):
                    continue

        # Ordenar por data
        vendas_detalhadas.sort(key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y %H:%M'))

        # Preparar dados para o template
        context = {
            'usuario': usuario,
            'inicio': inicio.date(),
            'fim': fim.date(),
            'periodo': periodo,
            
            # Resumo
            'total_entradas': total_entradas,
            'total_saidas': total_saidas,
            'num_rotas': num_rotas,
            'num_rotas_concluidas': num_rotas_concluidas,
            'num_vendas': vendas.count(),
            'total_vendas_diretas': total_vendas_diretas,
            'total_vendas_rotas': total_vendas_rotas,
            'total_vendas_geral': total_vendas_diretas + total_vendas_rotas,
            
            # Top entradas e saídas - processar dados para garantir nomes corretos
            'top_entradas': [
                {
                    'id': entrada['produto__idProduto'],
                    'nome': entrada['produto__nome'] or f"Produto ID {entrada['produto__idProduto']}",
                    'total': entrada['total']
                }
                for entrada in entradas_qs[:10]
            ],
            'top_saidas': [
                {
                    'id': saida['produto__idProduto'],
                    'nome': saida['produto__nome'] or f"Produto ID {saida['produto__idProduto']}",
                    'total': saida['total']
                }
                for saida in saidas_qs[:10]
            ],
            
            # Top produtos vendidos
            'top_produtos_vendidos': [(id_to_nome.get(pid, f"ID {pid}"), qtd) for pid, qtd in top_produtos_vendidos],
            'menos_produtos_vendidos': [(id_to_nome.get(pid, f"ID {pid}"), qtd) for pid, qtd in menos_produtos_vendidos],
            
            # Top bairros
            'top_bairros': top_neighborhoods,
            
            # Top produtos em rotas
            'top_produtos_rotas': [(id_to_nome.get(pid, f"ID {pid}"), qtd) for pid, qtd in top_produtos_rotas],
            'menos_produtos_rotas': [(id_to_nome.get(pid, f"ID {pid}"), qtd) for pid, qtd in menos_produtos_rotas],
            
            # Dados detalhados
            'rotas_data': rotas_data,
            'vendas_detalhadas': vendas_detalhadas,
            'total_custo_rotas': total_custo,
            'total_lucro_rotas': total_vendas_rotas_detalhado - total_custo,
        }

        # Gerar HTML
        html_content = self.generate_html_report(context)
        
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'inline; filename="relatorio_{usuario.cnpj}.html"'
        return response

    def generate_html_report(self, context):
        """Gera o relatório em HTML com CSS embutido"""
        
        html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Gestão - {{ usuario.nome }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }

        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .header .period {
            margin-top: 15px;
            font-size: 1em;
            opacity: 0.8;
        }

        .content {
            padding: 30px;
        }

        .section {
            margin-bottom: 40px;
            page-break-inside: avoid;
        }

        .section-title {
            font-size: 1.8em;
            color: #ff8c42;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #ff8c42;
            font-weight: 500;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #ff8c42;
            transition: transform 0.2s ease;
        }

        .summary-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .summary-card h3 {
            color: #ff8c42;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .summary-card .value {
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
        }

        .table-container {
            overflow-x: auto;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        th {
            background: #ff8c42;
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
            word-wrap: break-word;
            word-break: break-word;
        }
        
        /* Coluna de destinos com quebra de linha */
        .destinos-column {
            max-width: 300px;
            word-wrap: break-word;
            word-break: break-word;
            white-space: normal;
        }

        tr:hover {
            background-color: #f8f9fa;
        }

        tr:nth-child(even) {
            background-color: #fafafa;
        }

        .number {
            text-align: right;
            font-weight: 500;
        }

        .status-concluido {
            color: #27ae60;
            font-weight: bold;
        }

        .status-progresso {
            color: #f39c12;
            font-weight: bold;
        }

        .profit-positive {
            color: #27ae60;
            font-weight: bold;
        }

        .profit-negative {
            color: #e74c3c;
            font-weight: bold;
        }

        .print-button {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff8c42;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            box-shadow: 0 4px 15px rgba(255, 140, 66, 0.3);
            transition: all 0.3s ease;
            z-index: 1000;
        }

        .print-button:hover {
            background: #ff6b35;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 140, 66, 0.4);
        }

        .no-data {
            text-align: center;
            color: #7f8c8d;
            font-style: italic;
            padding: 40px;
            background: #f8f9fa;
            border-radius: 8px;
        }

        /* Responsividade */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .content {
                padding: 20px;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .print-button {
                position: static;
                width: 100%;
                margin-bottom: 20px;
            }
        }

        /* Estilos para impressão */
        @media print {
            @page {
                margin: 1cm;
                size: A4;
            }
            
            body {
                background: white;
                padding: 0;
                font-size: 12px;
                line-height: 1.4;
            }
            
            .container {
                box-shadow: none;
                border-radius: 0;
                margin: 0;
                max-width: none;
            }
            
            .print-button {
                display: none;
            }
            
            .header {
                background: #ff8c42 !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
                page-break-after: avoid;
            }
            
            .section {
                page-break-inside: avoid;
                margin-bottom: 20px;
            }
            
            .section-title {
                page-break-after: avoid;
                color: #ff8c42 !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
            }
            
            table {
                page-break-inside: auto;
                font-size: 10px;
            }
            
            .destinos-column {
                max-width: 200px;
                font-size: 9px;
            }
            
            th {
                background: #ff8c42 !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
                page-break-after: avoid;
            }
            
            tr {
                page-break-inside: avoid;
                page-break-after: auto;
            }
            
            .summary-card:hover {
                transform: none;
                box-shadow: none;
            }
            
            .summary-grid {
                display: block;
            }
            
            .summary-card {
                display: inline-block;
                width: 45%;
                margin: 5px;
                page-break-inside: avoid;
            }
            
            h3 {
                color: #ff8c42 !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
            }
        }

        /* Animações */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .section {
            animation: fadeInUp 0.6s ease-out;
        }

        .section:nth-child(2) { animation-delay: 0.1s; }
        .section:nth-child(3) { animation-delay: 0.2s; }
        .section:nth-child(4) { animation-delay: 0.3s; }
        .section:nth-child(5) { animation-delay: 0.4s; }
        .section:nth-child(6) { animation-delay: 0.5s; }
    </style>
</head>
<body>
    <button class="print-button" onclick="printReport()">🖨️ Imprimir / PDF</button>
    
    <div class="container">
        <div class="header">
            <h1>Relatório de Gestão</h1>
            <div class="subtitle">{{ usuario.nome }}</div>
            <div class="subtitle">CNPJ: {{ usuario.cnpj }}</div>
            <div class="period">Período: {{ inicio }} a {{ fim }}</div>
        </div>

        <div class="content">
            <!-- Seção 1: Resumo Executivo -->
            <div class="section">
                <h2 class="section-title">1. Resumo Executivo</h2>
                
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>Total de Entradas</h3>
                        <div class="value">{{ total_entradas|floatformat:0 }}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Total de Saídas</h3>
                        <div class="value">{{ total_saidas|floatformat:0 }}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Rotas Concluídas</h3>
                        <div class="value">{{ num_rotas_concluidas }}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Rotas Totais</h3>
                        <div class="value">{{ num_rotas }}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Vendas Finalizadas</h3>
                        <div class="value">{{ num_vendas }}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Receita Total</h3>
                        <div class="value">R$ {{ total_vendas_geral|floatformat:2 }}</div>
                    </div>
                </div>
            </div>

            <!-- Seção 2: Análise de Produtos -->
            <div class="section">
                <h2 class="section-title">2. Análise de Produtos</h2>
                
                <h3 style="margin: 20px 0 10px 0; color: #ff8c42;">Top 10 Entradas de Produtos</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Produto</th>
                                <th class="number">Quantidade</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for entrada in top_entradas %}
                            <tr>
                                <td>{{ entrada.nome }}</td>
                                <td class="number">{{ entrada.total|floatformat:0 }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="2" class="no-data">Sem dados disponíveis</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <h3 style="margin: 20px 0 10px 0; color: #ff8c42;">Top 10 Saídas de Produtos</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Produto</th>
                                <th class="number">Quantidade</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for saida in top_saidas %}
                            <tr>
                                <td>{{ saida.nome }}</td>
                                <td class="number">{{ saida.total|floatformat:0 }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="2" class="no-data">Sem dados disponíveis</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <h3 style="margin: 20px 0 10px 0; color: #ff8c42;">Top 10 Produtos Mais Vendidos (Total)</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Produto</th>
                                <th class="number">Quantidade Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for produto, qtd in top_produtos_vendidos %}
                            <tr>
                                <td>{{ produto }}</td>
                                <td class="number">{{ qtd|floatformat:0 }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="2" class="no-data">Sem dados disponíveis</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <h3 style="margin: 20px 0 10px 0; color: #ff8c42;">Top 10 Produtos Menos Vendidos (Total)</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Produto</th>
                                <th class="number">Quantidade Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for produto, qtd in menos_produtos_vendidos %}
                            <tr>
                                <td>{{ produto }}</td>
                                <td class="number">{{ qtd|floatformat:0 }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="2" class="no-data">Sem dados disponíveis</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Seção 3: Análise de Rotas -->
            <div class="section">
                <h2 class="section-title">3. Análise de Rotas</h2>
                
                <h3 style="margin: 20px 0 10px 0; color: #ff8c42;">Top 10 Bairros Mais Visitados</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Bairro</th>
                                <th class="number">Número de Visitas</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for bairro, count in top_bairros %}
                            <tr>
                                <td>{{ bairro }}</td>
                                <td class="number">{{ count }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="2" class="no-data">Sem dados disponíveis</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <h3 style="margin: 20px 0 10px 0; color: #ff8c42;">Top 10 Produtos Mais Enviados em Rotas</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Produto</th>
                                <th class="number">Quantidade</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for produto, qtd in top_produtos_rotas %}
                            <tr>
                                <td>{{ produto }}</td>
                                <td class="number">{{ qtd|floatformat:0 }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="2" class="no-data">Sem dados disponíveis</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <h3 style="margin: 20px 0 10px 0; color: #ff8c42;">Top 10 Produtos Menos Enviados em Rotas</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Produto</th>
                                <th class="number">Quantidade</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for produto, qtd in menos_produtos_rotas %}
                            <tr>
                                <td>{{ produto }}</td>
                                <td class="number">{{ qtd|floatformat:0 }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="2" class="no-data">Sem dados disponíveis</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Seção 4: Detalhamento de Rotas -->
            <div class="section">
                <h2 class="section-title">4. Detalhamento de Rotas</h2>
                
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Distância</th>
                                <th>Destinos de Entrega (apenas entregas)</th>
                                <th>Veículo</th>
                                <th>Motorista</th>
                                <th class="number">Custo</th>
                                <th class="number">Vendas</th>
                                <th class="number">Lucro</th>
                                <th>Status</th>
                                <th>Data</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for rota in rotas_data %}
                            <tr {% if rota.id == 'TOTAL' %}style="background-color: #fff4e6; font-weight: bold; border-top: 2px solid #ff8c42;"{% endif %}>
                                <td {% if rota.id == 'TOTAL' %}style="font-weight: bold; color: #ff8c42;"{% endif %}>{{ rota.id }}</td>
                                <td>{{ rota.distancia }}</td>
                                <td class="destinos-column">{{ rota.destinos }}</td>
                                <td>{{ rota.veiculo }}</td>
                                <td>{{ rota.motorista }}</td>
                                <td class="number" {% if rota.id == 'TOTAL' %}style="font-weight: bold; color: #ff8c42;"{% endif %}>{{ rota.custo }}</td>
                                <td class="number" {% if rota.id == 'TOTAL' %}style="font-weight: bold; color: #ff8c42;"{% endif %}>{{ rota.vendas }}</td>
                                <td class="number {% if 'R$ -' in rota.lucro %}profit-negative{% else %}profit-positive{% endif %}" {% if rota.id == 'TOTAL' %}style="font-weight: bold;"{% endif %}>{{ rota.lucro }}</td>
                                <td>
                                    {% if rota.status %}
                                    <span class="{% if rota.status == 'Concluído' %}status-concluido{% else %}status-progresso{% endif %}">
                                        {{ rota.status }}
                                    </span>
                                    {% endif %}
                                </td>
                                <td>{{ rota.data }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="10" class="no-data">Sem dados disponíveis</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Seção 5: Detalhamento de Vendas -->
            <div class="section">
                <h2 class="section-title">5. Detalhamento de Vendas do Período</h2>
                
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Data/Hora</th>
                                <th>Produto</th>
                                <th class="number">Qtd</th>
                                <th class="number">Preço Unit.</th>
                                <th class="number">Subtotal</th>
                                <th>Tipo</th>
                                <th>Observação</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for venda in vendas_detalhadas %}
                            <tr>
                                <td>{{ venda.data }}</td>
                                <td>{{ venda.produto }}</td>
                                <td class="number">{{ venda.quantidade }}</td>
                                <td class="number">{{ venda.preco_unitario }}</td>
                                <td class="number">{{ venda.subtotal }}</td>
                                <td>{{ venda.tipo }}</td>
                                <td>{{ venda.observacao }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="7" class="no-data">Sem dados disponíveis</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Função para imprimir/gerar PDF
        function printReport() {
            // Adicionar informações de impressão
            const printInfo = document.createElement('div');
            printInfo.innerHTML = `
                <div style="text-align: center; margin-bottom: 20px; color: #666; font-size: 12px;">
                    Relatório gerado em: ${new Date().toLocaleString('pt-BR')}<br>
                    Usuário: {{ usuario.nome }} (CNPJ: {{ usuario.cnpj }})<br>
                    Período: {{ inicio }} a {{ fim }}
                </div>
            `;
            
            // Inserir informações antes do conteúdo principal
            const container = document.querySelector('.container');
            container.insertBefore(printInfo, container.firstChild);
            
            // Imprimir
            window.print();
            
            // Remover informações após impressão
            setTimeout(() => {
                if (printInfo.parentNode) {
                    printInfo.parentNode.removeChild(printInfo);
                }
            }, 1000);
        }

        // Adicionar funcionalidade de ordenação nas tabelas
        document.addEventListener('DOMContentLoaded', function() {
            const tables = document.querySelectorAll('table');
            
            tables.forEach(table => {
                const headers = table.querySelectorAll('th');
                headers.forEach((header, index) => {
                    header.style.cursor = 'pointer';
                    header.title = 'Clique para ordenar';
                    header.addEventListener('click', () => {
                        sortTable(table, index);
                    });
                });
            });
        });

        function sortTable(table, columnIndex) {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            const isNumeric = !isNaN(parseFloat(rows[0].cells[columnIndex].textContent.replace(/[^0-9.-]/g, '')));
            
            rows.sort((a, b) => {
                const aVal = a.cells[columnIndex].textContent.trim();
                const bVal = b.cells[columnIndex].textContent.trim();
                
                if (isNumeric) {
                    const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, '')) || 0;
                    const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, '')) || 0;
                    return bNum - aNum;
                } else {
                    return aVal.localeCompare(bVal);
                }
            });
            
            rows.forEach(row => tbody.appendChild(row));
        }
    </script>
</body>
</html>
        """
        
        from django.template import Template, Context
        template = Template(html_template)
        return template.render(Context(context))