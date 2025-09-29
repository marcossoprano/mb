from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """Health check endpoint para monitoramento"""
    return JsonResponse({
        'status': 'ok',
        'service': 'Milo Backend API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'usuarios': '/api/usuarios/',
            'produtos': '/api/produtos/',
            'rotas': '/api/rotas/',
            'planilhas': '/api/planilhas/',
            'vendas': '/api/vendas/',
            'relatorios': '/api/relatorios/'
        }
    })

@require_http_methods(["GET"])
def api_info(request):
    """Informações da API"""
    return JsonResponse({
        'message': 'Milo Backend API - Sistema de Gestão',
        'documentation': 'Em desenvolvimento',
        'status': 'online'
    })