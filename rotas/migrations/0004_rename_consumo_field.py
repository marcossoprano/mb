# Generated manually to rename consumo_por_km to eficiencia_km_l

from django.db import migrations, models
from django.core.validators import MinValueValidator

class Migration(migrations.Migration):

    dependencies = [
        ('rotas', '0003_update_consumo_field'),
    ]

    operations = [
        migrations.RenameField(
            model_name='veiculo',
            old_name='consumo_por_km',
            new_name='eficiencia_km_l',
        ),
        migrations.AlterField(
            model_name='veiculo',
            name='eficiencia_km_l',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=5,
                validators=[MinValueValidator(0.01)],
                verbose_name='Eficiência (km/L para líquidos, km/m³ para GNV)'
            ),
        ),
    ] 