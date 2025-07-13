from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.http import JsonResponse
import json

class JWTAutoRefreshMiddleware(MiddlewareMixin):
    """
    Middleware para renovação automática de tokens JWT
    """
    
    def process_request(self, request):
        # Verifica se é uma requisição para a API
        if not request.path.startswith('/api/'):
            return None
            
        # Pula endpoints de autenticação
        if request.path in ['/api/usuarios/login/', '/api/usuarios/register/', '/api/usuarios/token/refresh/']:
            return None
            
        # Verifica se há um refresh token no header
        refresh_token = request.headers.get('X-Refresh-Token')
        
        if refresh_token:
            try:
                # Tenta renovar o token
                refresh = RefreshToken(refresh_token)
                new_access_token = str(refresh.access_token)
                
                # Adiciona o novo token ao request
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'
                
                # Adiciona headers para o cliente saber que o token foi renovado
                request.META['HTTP_X-NEW-ACCESS-TOKEN'] = new_access_token
                
            except (InvalidToken, TokenError):
                # Se o refresh token for inválido, não faz nada
                # A autenticação normal do DRF vai lidar com isso
                pass
                
        return None
        
    def process_response(self, request, response):
        # Se um novo token foi gerado, adiciona ao response
        if hasattr(request, 'META') and 'HTTP_X-NEW-ACCESS-TOKEN' in request.META:
            response['X-New-Access-Token'] = request.META['HTTP_X-NEW-ACCESS-TOKEN']
            
        return response 