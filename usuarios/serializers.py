from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['cnpj', 'nome', 'telefone', 'email', 'endereco', 'cep', 'rua', 'numero', 'bairro', 'cidade', 'estado', 'password']

    def validate(self, data):
        # Validação: pelo menos email ou telefone deve ser fornecido
        email = data.get('email')
        telefone = data.get('telefone')
        
        if not email and not telefone:
            raise serializers.ValidationError(
                'Pelo menos um dos campos: email ou telefone deve ser fornecido'
            )
        
        # Validação: todos os campos de endereço são obrigatórios
        campos_endereco = ['cep', 'rua', 'numero', 'bairro', 'cidade', 'estado']
        campos_faltando = [campo for campo in campos_endereco if not data.get(campo)]
        
        if campos_faltando:
            raise serializers.ValidationError(
                f'Os seguintes campos de endereço são obrigatórios: {", ".join(campos_faltando)}'
            )
        
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user
