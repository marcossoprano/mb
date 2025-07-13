from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario
from .serializers import UsuarioSerializer
from rest_framework.permissions import IsAuthenticated #pra facilitar o uso da classe IsAuthenticated

# Create your views here.

class UsuarioCreateView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.AllowAny]

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['cnpj'] = user.cnpj
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout realizado com sucesso'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Refresh token é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trocar_senha_view(request):
    usuario = request.user
    nova_senha = request.data.get("nova_senha")

    if not nova_senha:
        return Response ({'erro': 'Nova senha não fornecida'}, status=status.HTTP_400_BAD_REQUEST)
    
    usuario.set_password(nova_senha)
    usuario.save()
    return Response({'mensagem': 'Senha atualizada com sucesso'}, status=status.HTTP_200_OK)



@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def deletar_conta_view(request):
    usuario = request.user
    usuario.delete()
    return Response({'mensagem': 'Conta deletada com sucesso'}, status=status.HTTP_204_NO_CONTENT)





