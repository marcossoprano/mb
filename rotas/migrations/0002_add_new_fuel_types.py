# Generated manually to add new fuel types

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('rotas', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='veiculo',
            name='tipo_combustivel',
            field=models.CharField(
                choices=[
                    ('diesel', 'Diesel'),
                    ('gasolina', 'Gasolina'),
                    ('etanol', 'Etanol'),
                    ('gnv', 'Gás Veicular (GNV)')
                ],
                max_length=10,
                verbose_name='Tipo de Combustível'
            ),
        ),
    ] 