# Generated manually to update consumo field to use km/L instead of L/km

from django.db import migrations, models
from django.core.validators import MinValueValidator

class Migration(migrations.Migration):

    dependencies = [
        ('rotas', '0002_add_new_fuel_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='veiculo',
            name='consumo_por_km',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=5,
                validators=[MinValueValidator(0.01)],
                verbose_name='Consumo de Combustível (km/L)'
            ),
        ),
    ] 