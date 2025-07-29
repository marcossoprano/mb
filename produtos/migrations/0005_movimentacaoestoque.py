import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0004_fornecedor_email_fornecedor_endereco_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MovimentacaoEstoque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('entrada', 'Entrada'), ('saida', 'Saída')], max_length=7, verbose_name='Tipo de Movimentação')),
                ('quantidade', models.PositiveIntegerField(verbose_name='Quantidade Movimentada')),
                ('estoque_anterior', models.PositiveIntegerField(verbose_name='Estoque Anterior')),
                ('estoque_atual', models.PositiveIntegerField(verbose_name='Estoque Atual')),
                ('data_movimentacao', models.DateTimeField(auto_now_add=True, verbose_name='Data e Hora da Movimentação')),
                ('observacao', models.TextField(blank=True, verbose_name='Observação')),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimentacoes', to='produtos.produto', verbose_name='Produto')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuário Responsável')),
            ],
            options={
                'verbose_name': 'Movimentação de Estoque',
                'verbose_name_plural': 'Movimentações de Estoque',
                'ordering': ['-data_movimentacao'],
            },
        ),
    ]
