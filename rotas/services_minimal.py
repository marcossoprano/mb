# Versão simplificada temporária do services.py para deploy
import requests
from decimal import Decimal
import json
import hashlib
import time
from functools import lru_cache

class RotaOtimizacaoService:
    def __init__(self):
        # Cache em memória para geocodificação (endereço -> coordenadas)
        self._geocoding_cache = {}
        self._geocoding_ttl = 24 * 60 * 60  # 24 horas em segundos
        
        # Cache em memória para grafos OSMnx (região -> grafo)
        self._grafos_cache = {}
        self._grafos_ttl = 60 * 60  # 1 hora em segundos
    
    def otimizar_rota(self, *args, **kwargs):
        """Versão simplificada - retorna mensagem informativa"""
        return {
            'sucesso': False,
            'mensagem': 'Otimização de rotas temporariamente indisponível durante o deploy. Será reativada em breve.',
            'rota_otimizada': [],
            'distancia_total': 0,
            'tempo_total': 0
        }
    
    def calcular_distancia_tempo(self, *args, **kwargs):
        """Versão simplificada"""
        return {'distancia': 0, 'tempo': 0}
    
    def geocodificar_endereco(self, endereco):
        """Versão simplificada usando API básica"""
        try:
            # Usando uma API simples de geocodificação
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                'q': endereco,
                'format': 'json',
                'limit': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data:
                return (float(data[0]['lat']), float(data[0]['lon']))
            else:
                return None
                
        except Exception as e:
            print(f"Erro na geocodificação: {e}")
            return None