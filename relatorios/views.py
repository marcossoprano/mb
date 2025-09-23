from datetime import datetime, timedelta
from io import BytesIO

from django.db.models import Sum, F
from django.http import HttpResponse
from django.utils.timezone import now

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from produtos.models import MovimentacaoEstoque, Produto
from rotas.models import Rota


class RelatorioPDFView(APIView):
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

        # Movimentações (entradas e saídas) do usuário no período
        movs = MovimentacaoEstoque.objects.filter(
            usuario=usuario,
            data_movimentacao__range=(inicio, fim)
        ).select_related('produto')

        total_entradas = movs.filter(tipo='entrada').aggregate(total=Sum('quantidade'))['total'] or 0
        total_saidas = movs.filter(tipo='saida').aggregate(total=Sum('quantidade'))['total'] or 0

        # Entradas/Saídas detalhadas por produto (todas as movimentações no período)
        # Inclui amostra da observação mais recente por produto/tipo
        entradas_qs = (
            movs.filter(tipo='entrada')
            .values('produto__idProduto', 'produto__nome')
            .annotate(total=Sum('quantidade'))
            .order_by('-total')
        )
        saidas_qs = (
            movs.filter(tipo='saida')
            .values('produto__idProduto', 'produto__nome')
            .annotate(total=Sum('quantidade'))
            .order_by('-total')
        )

        # Rotas do usuário no período
        rotas = Rota.objects.filter(usuario=usuario, data_geracao__range=(inicio, fim))
        num_rotas = rotas.count()

        # Estimar lucro: considerar somente saídas provenientes de rotas concluídas
        # Lucro = sum(qtd * (preco_venda - preco_custo)) para produtos enviados em rotas com status 'concluido'
        rotas_concluidas = rotas.filter(status='concluido')
        num_rotas_concluidas = rotas_concluidas.count()
        envio_concluido_por_produto = {}
        for r in rotas_concluidas:
            pq = r.produtos_quantidades or {}
            for pid_str, qtd in pq.items():
                try:
                    pid = int(pid_str)
                except Exception:
                    continue
                envio_concluido_por_produto[pid] = envio_concluido_por_produto.get(pid, 0) + int(qtd)

        lucro_estimado = 0.0
        if envio_concluido_por_produto:
            produtos_concluidos = Produto.objects.filter(
                usuario=usuario,
                idProduto__in=envio_concluido_por_produto.keys()
            ).values('idProduto', 'preco_venda', 'preco_custo')
            precos_map = {
                p['idProduto']: (float(p['preco_venda']), float(p['preco_custo'])) for p in produtos_concluidos
            }
            for pid, qtd in envio_concluido_por_produto.items():
                if pid in precos_map:
                    pv, pc = precos_map[pid]
                    lucro_estimado += float(qtd) * (pv - pc)

        # Produtos mais/menos enviados nas rotas concluídas
        envio_por_produto = {}
        for r in rotas_concluidas:
            pq = r.produtos_quantidades or {}
            for pid_str, qtd in pq.items():
                try:
                    pid = int(pid_str)
                except Exception:
                    continue
                envio_por_produto[pid] = envio_por_produto.get(pid, 0) + int(qtd)

        # Resolver nomes de produtos do usuário
        produtos_usuario = Produto.objects.filter(usuario=usuario, idProduto__in=envio_por_produto.keys())
        id_to_nome = {p.idProduto: p.nome for p in produtos_usuario}

        top_produtos = sorted(envio_por_produto.items(), key=lambda x: x[1], reverse=True)[:5]
        bottom_produtos = sorted(envio_por_produto.items(), key=lambda x: x[1])[:5]

        # Montar PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_{usuario.cnpj}.pdf"'

        c = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        # Cabeçalho
        c.setFont('Helvetica-Bold', 14)
        c.drawString(2*cm, height - 2*cm, 'Relatório da Conta')
        c.setFont('Helvetica', 10)
        c.drawString(2*cm, height - 2.6*cm, f'Usuário: {usuario.nome} (CNPJ: {usuario.cnpj})')
        c.drawString(2*cm, height - 3.1*cm, f'Período: {inicio.date()} a {fim.date()}')

        y = height - 4*cm

        # Utilitário: desenhar tabela com quebra de página se necessário (com wrap em colunas largas)
        def draw_table_with_pagination(title, header, rows):
            nonlocal y
            styles = getSampleStyleSheet()
            body_style = styles['BodyText']
            body_style.fontName = 'Helvetica'
            body_style.fontSize = 9
            body_style.leading = 12
            c.setFont('Helvetica-Bold', 12)
            if y < 3*cm:
                c.showPage()
                y = height - 2*cm
            c.drawString(2*cm, y, title)
            y -= 0.6*cm
            # Converter strings longas em Paragraph para quebrar linha
            wrapped_rows = []
            for r in rows:
                nome = Paragraph(r[0], body_style)
                qtd = r[1]
                tipo_obs = Paragraph(r[2], body_style)
                wrapped_rows.append([nome, qtd, tipo_obs])
            data = [header] + wrapped_rows
            table = Table(data, colWidths=[6*cm, 2.5*cm, 5.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ALIGN', (1,1), (1,-1), 'RIGHT'),
                ('ALIGN', (2,1), (2,-1), 'LEFT'),
            ]))
            w, h = table.wrapOn(c, width - 4*cm, y)
            # Se a tabela não couber inteira, dividir em páginas
            if (y - h) < 2*cm:
                # Paginar em blocos
                max_rows_per_page = 25
                chunk = [header]
                for i, r in enumerate(wrapped_rows, start=1):
                    chunk.append(r)
                    if len(chunk) == max_rows_per_page + 1 or i == len(rows):
                        t = Table(chunk, colWidths=[6*cm, 2.5*cm, 5.5*cm])
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                            ('ALIGN', (1,1), (1,-1), 'RIGHT'),
                            ('ALIGN', (2,1), (2,-1), 'LEFT'),
                        ]))
                        w2, h2 = t.wrapOn(c, width - 4*cm, y)
                        if (y - h2) < 2*cm:
                            c.showPage()
                            y = height - 2*cm
                        t.drawOn(c, 2*cm, y - h2)
                        y = y - h2 - 0.6*cm
                        chunk = [header]
                return
            # Cabe
            table.drawOn(c, 2*cm, y - h)
            y = y - h - 0.6*cm


        # Gráfico 1: Entradas vs Saídas (barras)
        fig1, ax1 = plt.subplots(figsize=(4, 3))
        ax1.bar(['Entradas', 'Saídas'], [total_entradas, total_saidas], color=['#4CAF50', '#F44336'])
        ax1.set_title('Movimentações de Estoque')
        ax1.set_ylabel('Quantidade')
        buf1 = BytesIO()
        fig1.tight_layout()
        fig1.savefig(buf1, format='png')
        plt.close(fig1)
        buf1.seek(0)

        # Gráfico 2: Produtos enviados (rotas concluídas)
        # Mostrar todos os produtos enviados, não apenas top
        all_produtos_enviados = sorted(envio_por_produto.items(), key=lambda x: x[1], reverse=True)
        labels_all = [id_to_nome.get(pid, f'ID {pid}') for pid, _ in all_produtos_enviados] or ['Sem dados']
        values_all = [q for _, q in all_produtos_enviados] or [0]
        
        # Limitar a 10 produtos para não sobrecarregar o gráfico
        labels_limited = labels_all[:10]
        values_limited = values_all[:10]
        
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.bar(labels_limited, values_limited, color='#2196F3')
        ax2.set_title('Produtos enviados (rotas concluídas)')
        ax2.set_ylabel('Quantidade')
        ax2.tick_params(axis='x', rotation=45, labelsize=8)
        fig2.tight_layout()
        buf2 = BytesIO()
        fig2.savefig(buf2, format='png')
        plt.close(fig2)
        buf2.seek(0)


        # Inserir gráficos
        from reportlab.lib.utils import ImageReader
        img1 = ImageReader(buf1)
        img2 = ImageReader(buf2)

        # Seção Resumo
        c.setFont('Helvetica-Bold', 14)
        c.drawString(2*cm, y, 'Resumo')
        y -= 0.8*cm
        
        # Tabela de resumo
        resumo_data = [
            ['Métrica', 'Valor'],
            ['Entradas (qtd)', str(total_entradas)],
            ['Saídas (qtd)', str(total_saidas)],
            ['Rotas concluídas no período', str(num_rotas_concluidas)],
            ['Rotas totais no período', str(num_rotas)],
            ['Lucro em rotas concluídas (R$)', f"{lucro_estimado:.2f}"],
        ]
        table = Table(resumo_data, colWidths=[8*cm, 6*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        w, h = table.wrapOn(c, width - 4*cm, y)
        table.drawOn(c, 2*cm, y - h)
        y = y - h - 1*cm

        # Seção: Produtos
        c.setFont('Helvetica-Bold', 13)
        c.drawString(2*cm, y, 'Seção: Produtos')
        y -= 0.8*cm

        c.drawString(2*cm, y, 'Gráfico: Entradas vs Saídas')
        y -= 0.5*cm
        # Ajustar tamanho do gráfico para evitar corte
        graph_h = 6*cm
        graph_w = 10*cm
        if y - graph_h < 2*cm:
            c.showPage()
            y = height - 2*cm
        c.drawImage(img1, 2*cm, y - graph_h, width=graph_w, height=graph_h, preserveAspectRatio=True, mask='auto')
        y -= (graph_h + 0.8*cm)

        # Montar linhas de entradas e saídas
        entradas_rows = []
        for e in entradas_qs:
            nome = e['produto__nome'] or f"ID {e['produto__idProduto']}"
            # Buscar observação mais recente desta combinação
            obs = (
                MovimentacaoEstoque.objects.filter(
                    usuario=usuario,
                    tipo='entrada',
                    produto__idProduto=e['produto__idProduto'],
                    data_movimentacao__range=(inicio, fim)
                )
                .order_by('-data_movimentacao')
                .values_list('observacao', flat=True)
                .first()
            )
            tipo_obs = f"Entrada — {obs}" if obs else 'Entrada'
            entradas_rows.append([nome, str(e['total']), tipo_obs])
        if not entradas_rows:
            entradas_rows = [['Sem dados', '0', 'Entrada']]

        saidas_rows = []
        for s in saidas_qs:
            nome = s['produto__nome'] or f"ID {s['produto__idProduto']}"
            obs = (
                MovimentacaoEstoque.objects.filter(
                    usuario=usuario,
                    tipo='saida',
                    produto__idProduto=s['produto__idProduto'],
                    data_movimentacao__range=(inicio, fim)
                )
                .order_by('-data_movimentacao')
                .values_list('observacao', flat=True)
                .first()
            )
            tipo_obs = f"Saída — {obs}" if obs else 'Saída'
            saidas_rows.append([nome, str(s['total']), tipo_obs])
        if not saidas_rows:
            saidas_rows = [['Sem dados', '0', 'Saída']]

        # Tabelas de entradas e saídas por produto (na seção de Produtos)
        if y < 4*cm:
            c.showPage()
            y = height - 2*cm

        # Desenhar tabelas de entradas e saídas (todas as movimentações)
        draw_table_with_pagination('Entradas por produto (todas as entradas no período)', ['Produto', 'Quantidade', 'Tipo / Observação'], entradas_rows)
        draw_table_with_pagination('Saídas por produto (todas as saídas no período)', ['Produto', 'Quantidade', 'Tipo / Observação'], saidas_rows)

        # Quebra de página para iniciar seção de Rotas
        if y < 6*cm:
            c.showPage()
            y = height - 2*cm

        # Seção: Rotas
        c.setFont('Helvetica-Bold', 13)
        c.drawString(2*cm, y, 'Seção: Rotas')
        y -= 0.8*cm

        c.drawString(2*cm, y, 'Gráfico: Produtos enviados (rotas concluídas)')
        y -= 0.5*cm
        if y - graph_h < 2*cm:
            c.showPage()
            y = height - 2*cm
        c.drawImage(img2, 2*cm, y - graph_h, width=graph_w, height=graph_h, preserveAspectRatio=True, mask='auto')
        y -= (graph_h + 0.8*cm)

        if y < 4*cm:
            c.showPage()
            y = height - 2*cm

        # Título: Top produtos mais enviados
        c.setFont('Helvetica-Bold', 11)
        c.drawString(2*cm, y, 'Top produtos mais enviados (rotas concluídas)')
        y -= 0.6*cm

        # Tabela: Top produtos mais enviados (rotas concluídas)
        mais_header = ['Produto', 'Qtd enviada']
        mais_rows = [[id_to_nome.get(pid, f'ID {pid}'), str(qtd)] for pid, qtd in top_produtos]
        if not mais_rows:
            mais_rows = [['Sem dados', '0']]
        mais_table = Table([mais_header] + mais_rows, colWidths=[8*cm, 3*cm])
        mais_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        w2, h2 = mais_table.wrapOn(c, width - 4*cm, y)
        mais_table.drawOn(c, 2*cm, y - h2)

        y = y - h2 - 1*cm

        # Título: Top produtos menos enviados
        c.setFont('Helvetica-Bold', 11)
        c.drawString(2*cm, y, 'Top produtos menos enviados (rotas concluídas)')
        y -= 0.6*cm

        # Tabela: Top produtos menos enviados (rotas concluídas)
        menos_header = ['Produto', 'Qtd enviada']
        menos_rows = [[id_to_nome.get(pid, f'ID {pid}'), str(qtd)] for pid, qtd in bottom_produtos]
        if not menos_rows:
            menos_rows = [['Sem dados', '0']]
        menos_table = Table([menos_header] + menos_rows, colWidths=[8*cm, 3*cm])
        menos_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        w3, h3 = menos_table.wrapOn(c, width - 4*cm, y)
        menos_table.drawOn(c, 2*cm, y - h3)

        y = y - h3 - 1*cm

        # Tabela: Todas as rotas geradas no período
        if y < 4*cm:
            c.showPage()
            y = height - 2*cm

        # Título: Todas as rotas geradas
        c.setFont('Helvetica-Bold', 11)
        c.drawString(2*cm, y, 'Todas as rotas geradas no período')
        y -= 0.6*cm

        # Preparar dados das rotas
        rotas_data = []
        total_gasto = 0
        for rota in rotas:
            veiculo_nome = rota.veiculo.nome if rota.veiculo else 'Veículo Padrão'
            motorista = rota.nome_motorista or 'Sem motorista'
            data_formatada = rota.data_geracao.strftime('%d/%m/%Y %H:%M')
            status_display = 'Concluído' if rota.status == 'concluido' else 'Em Progresso'
            total_gasto += rota.valor_rota
            
            rotas_data.append([
                str(rota.id),
                f"{rota.distancia_total_km} km",
                veiculo_nome,
                motorista,
                f"R$ {rota.valor_rota:.2f}",
                status_display,
                data_formatada
            ])

        if not rotas_data:
            rotas_data = [['Sem dados', '', '', '', '', '', '']]
        else:
            # Adicionar linha de total
            rotas_data.append([
                'TOTAL',
                '',
                '',
                '',
                f"R$ {total_gasto:.2f}",
                '',
                ''
            ])

        # Criar tabela de rotas
        rotas_header = ['ID', 'Distância', 'Veículo', 'Motorista', 'Valor', 'Status', 'Data']
        rotas_table = Table([rotas_header] + rotas_data, colWidths=[1.0*cm, 1.8*cm, 4.0*cm, 2.2*cm, 1.8*cm, 2.0*cm, 2.6*cm])
        # Calcular índice da linha de total
        total_row_index = len(rotas_data) if rotas_data and rotas_data[0] != ['Sem dados', '', '', '', '', '', ''] else -1
        
        rotas_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,1), (0,-1), 'CENTER'),  # ID centralizado
            ('ALIGN', (1,1), (1,-1), 'CENTER'),  # Distância centralizada
            ('ALIGN', (4,1), (4,-1), 'RIGHT'),   # Valor alinhado à direita
            ('ALIGN', (5,1), (5,-1), 'CENTER'),  # Status centralizado
            # Destacar linha de total se existir
            ('BACKGROUND', (0, total_row_index), (-1, total_row_index), colors.lightblue) if total_row_index > 0 else ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0, total_row_index), (-1, total_row_index), 'Helvetica-Bold') if total_row_index > 0 else ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))

        # Verificar se a tabela cabe na página
        w4, h4 = rotas_table.wrapOn(c, width - 4*cm, y)
        if (y - h4) < 2*cm:
            c.showPage()
            y = height - 2*cm
            # Redesenhar título na nova página
            c.setFont('Helvetica-Bold', 11)
            c.drawString(2*cm, y, 'Todas as rotas geradas no período')
            y -= 0.6*cm

        rotas_table.drawOn(c, 2*cm, y - h4)
        y = y - h4 - 0.6*cm

        c.showPage()
        c.save()
        return response


