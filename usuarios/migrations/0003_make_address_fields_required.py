# Generated manually to make address fields required

from django.db import migrations, models


def preencher_enderecos_vazios(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    # Preencher registros existentes com valores padrão
    for usuario in Usuario.objects.all():
        if not usuario.cep:
            usuario.cep = '00000000'
        if not usuario.rua:
            usuario.rua = 'Endereço não informado'
        if not usuario.numero:
            usuario.numero = 'S/N'
        if not usuario.bairro:
            usuario.bairro = 'Bairro não informado'
        if not usuario.cidade:
            usuario.cidade = 'Cidade não informada'
        if not usuario.estado:
            usuario.estado = 'SP'
        usuario.save()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_add_address_fields'),
    ]

    operations = [
        # Primeiro, preencher campos vazios com valores padrão
        migrations.RunPython(preencher_enderecos_vazios),
        
        # Depois, tornar os campos obrigatórios
        migrations.AlterField(
            model_name='usuario',
            name='cep',
            field=models.CharField(max_length=8),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='rua',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='numero',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='bairro',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='cidade',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='estado',
            field=models.CharField(max_length=2),
        ),
    ] 