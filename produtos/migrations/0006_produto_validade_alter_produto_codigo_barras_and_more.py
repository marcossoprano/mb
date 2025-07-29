

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0005_movimentacaoestoque'),
    ]

    operations = [
        migrations.AddField(
            model_name='produto',
            name='validade',
            field=models.DateField(blank=True, null=True, verbose_name='Validade'),
        ),
        migrations.AlterField(
            model_name='produto',
            name='codigo_barras',
            field=models.CharField(blank=True, help_text='Código de barras no padrão EAN-13 (13 dígitos)', max_length=13, null=True, unique=True, validators=[django.core.validators.RegexValidator(message='Código de barras deve conter exatamente 13 dígitos numéricos', regex='^[0-9]{13}$')]),
        ),
        migrations.AlterField(
            model_name='produto',
            name='data_fabricacao',
            field=models.DateField(blank=True, null=True, verbose_name='Data de Fabricação'),
        ),
        migrations.AlterField(
            model_name='produto',
            name='descricao',
            field=models.TextField(blank=True, null=True, verbose_name='Descrição'),
        ),
        migrations.AlterField(
            model_name='produto',
            name='fornecedor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='produtos.fornecedor', verbose_name='Fornecedor'),
        ),
        migrations.AlterField(
            model_name='produto',
            name='lote',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Número do Lote'),
        ),
        migrations.AlterField(
            model_name='produto',
            name='marca',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Marca'),
        ),
    ]
