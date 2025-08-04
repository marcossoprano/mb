# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rotas', '0004_rename_consumo_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='rota',
            name='preco_combustivel_usado',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=6,
                null=True,
                verbose_name='Preço do Combustível Usado (R$/L ou R$/m³)'
            ),
        ),
    ] 