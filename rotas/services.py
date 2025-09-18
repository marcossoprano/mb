import osmnx as ox
import networkx as nx
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
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
        
        # Cache para preços de combustível
        self._precos_cache = {}
        self._precos_ttl = 30 * 60  # 30 minutos em segundos
        
        # Contador para limpeza periódica de cache
        self._cache_cleanup_counter = 0
        
    def obter_preco_combustivel(self, tipo_combustivel):
        """
        Retorna preços de combustível com cache
        """
        # Verifica cache primeiro
        cache_key = f"preco_{tipo_combustivel}"
        if cache_key in self._precos_cache:
            cached_data = self._precos_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self._precos_ttl:
                return cached_data['preco']
        
        # Valores fixos de combustível (mantém compatibilidade)
        precos = {
            'diesel': 5.80,  # R$/L
            'gasolina': 6.36,  # R$/L
            'etanol': 4.20,  # R$/L
            'gnv': 3.50,  # R$/m³
        }
        
        preco = precos.get(tipo_combustivel, 5.80)
        
        # Armazena no cache
        self._precos_cache[cache_key] = {
            'preco': preco,
            'timestamp': time.time()
        }
        
        return preco
    
    def calcular_consumo_combustivel(self, distancia_total_km, veiculo):
        """
        Calcula o consumo de combustível baseado no tipo de combustível
        """
        if not veiculo:
            # Veículo padrão: gasolina com 8.0 km/L
            km_por_litro = 8.0
            litros_consumidos = float(distancia_total_km) / km_por_litro
            return litros_consumidos, 'litros'
        
        eficiencia = float(veiculo.eficiencia_km_l)
        
        if veiculo.tipo_combustivel == 'gnv':
            # Para GNV: eficiência em km/m³
            metros_cubicos_consumidos = float(distancia_total_km) / eficiencia
            return metros_cubicos_consumidos, 'metros_cubicos'
        else:
            # Para outros combustíveis: eficiência em km/L
            litros_consumidos = float(distancia_total_km) / eficiencia
            return litros_consumidos, 'litros'
    
    def calcular_valor_rota(self, distancia_total_km, veiculo, preco_combustivel_personalizado=None):
        """
        Calcula o valor da rota baseado no consumo de combustível e preço
        """
        consumo_combustivel, unidade = self.calcular_consumo_combustivel(distancia_total_km, veiculo)
        
        # Se foi fornecido um preço personalizado, usa ele
        if preco_combustivel_personalizado is not None:
            preco_combustivel = float(preco_combustivel_personalizado)
        else:
            # Senão, usa o preço base do tipo de combustível
            tipo_combustivel = veiculo.tipo_combustivel if veiculo else 'gasolina'
            preco_combustivel = self.obter_preco_combustivel(tipo_combustivel)
        
        valor_rota = consumo_combustivel * preco_combustivel
        return valor_rota, preco_combustivel
    
    def geocodificar_endereco(self, endereco):
        """
        Geocodifica um endereço para coordenadas com cache
        """
        # Normaliza o endereço para usar como chave de cache
        endereco_normalizado = endereco.lower().strip()
        cache_key = hashlib.md5(endereco_normalizado.encode()).hexdigest()
        
        # Verifica cache primeiro
        if cache_key in self._geocoding_cache:
            cached_data = self._geocoding_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self._geocoding_ttl:
                return cached_data['coordenadas']
        
        try:
            coordenadas = ox.geocode(endereco)
            if coordenadas:
                # Armazena no cache
                self._geocoding_cache[cache_key] = {
                    'coordenadas': coordenadas,
                    'timestamp': time.time()
                }
                return coordenadas
        except Exception as e:
            print(f"Erro na geocodificação de {endereco}: {e}")
        
        # Fallback: coordenadas de Maceió (já que os endereços são de lá)
        return None
    
    
    def resolver_tsp(self, matriz):
        """
        Resolve o problema do caixeiro viajante usando OR-Tools
        Força o retorno à origem (empresa)
        """
        if len(matriz) < 2:
            return [0, 0]  # Se só tem origem, retorna origem -> origem
            
        manager = pywrapcp.RoutingIndexManager(len(matriz), 1, 0)  # 1 veículo, início em 0
        routing = pywrapcp.RoutingModel(manager)

        def callback(from_index, to_index):
            return matriz[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

        transit_callback_index = routing.RegisterTransitCallback(callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Configura estratégia de solução otimizada
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        
        # Para poucos pontos, usa estratégia mais rápida
        if len(matriz) <= 4:
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.time_limit_ms = 1000  # 1 segundo máximo
        else:
            # Para muitos pontos, usa estratégia balanceada
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.SAVINGS
            )
            search_parameters.time_limit_ms = 5000  # 5 segundos máximo
        
        # Otimizações adicionais
        search_parameters.log_search = False  # Desabilita logs para performance

        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            index = routing.Start(0)
            rota = []
            while not routing.IsEnd(index):
                rota.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            rota.append(rota[0])  # volta ao início
            return rota
        else:
            # Fallback: otimização simples usando algoritmo guloso
            rota = self.otimizacao_gulosa(matriz)
            return rota
    
    def calcular_distancia_tempo(self, coordenadas_otimizadas):
        """
        Calcula distância total e tempo estimado da rota
        Inclui o retorno à origem (empresa)
        """
        if len(coordenadas_otimizadas) < 2:
            return 0, 0
        
        # Calcula distância total aproximada (em linha reta para simplificar)
        distancia_total_km = 0
        for i in range(len(coordenadas_otimizadas) - 1):
            lat1, lon1 = coordenadas_otimizadas[i]
            lat2, lon2 = coordenadas_otimizadas[i + 1]
            
            # Fórmula de Haversine para calcular distância entre coordenadas
            import math
            R = 6371  # Raio da Terra em km
            
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            
            a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
                 math.cos(lat1_rad) * math.cos(lat2_rad) *
                 math.sin(delta_lon/2) * math.sin(delta_lon/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distancia = R * c
            
            distancia_total_km += distancia
        
        # Verifica se a rota inclui retorno à origem
        if len(coordenadas_otimizadas) > 2 and coordenadas_otimizadas[0] == coordenadas_otimizadas[-1]:
            # Rota completa com retorno à origem
            num_paradas = len(coordenadas_otimizadas) - 2  # -2 porque origem e retorno contam como 1
        else:
            # Rota sem retorno explícito
            num_paradas = len(coordenadas_otimizadas) - 1
        
        # Tempo estimado: 40 km/h em média + tempo de parada (5 min por parada)
        tempo_estimado_minutos = int((distancia_total_km / 40) * 60) + num_paradas * 5
        
        return distancia_total_km, tempo_estimado_minutos
    
    def calcular_distancia_real(self, matriz, rota_otimizada):
        """
        Calcula distância total real usando a matriz de distâncias
        Inclui o retorno à origem (empresa)
        """
        if len(rota_otimizada) < 2:
            return 0, 0
        
        # Calcula distância total usando a matriz real
        distancia_total_metros = 0
        for i in range(len(rota_otimizada) - 1):
            origem_idx = rota_otimizada[i]
            destino_idx = rota_otimizada[i + 1]
            distancia_total_metros += matriz[origem_idx][destino_idx]
        
        # Converte para km
        distancia_total_km = distancia_total_metros / 1000
        
        # Verifica se a rota inclui retorno à origem
        if len(rota_otimizada) > 2 and rota_otimizada[0] == rota_otimizada[-1]:
            # Rota completa com retorno à origem
            num_paradas = len(rota_otimizada) - 2  # -2 porque origem e retorno contam como 1
        else:
            # Rota sem retorno explícito
            num_paradas = len(rota_otimizada) - 1
        
        # Tempo estimado: 40 km/h em média + tempo de parada (5 min por parada)
        tempo_estimado_minutos = int((distancia_total_km / 40) * 60) + num_paradas * 5
        
        return distancia_total_km, tempo_estimado_minutos
    
    def otimizacao_gulosa(self, matriz):
        """
        Implementa otimização gulosa para TSP quando OR-Tools falha
        Sempre começa na origem (índice 0) e retorna à origem
        """
        if len(matriz) < 2:
            return [0, 0]
        
        n = len(matriz)
        rota = [0]  # Sempre começa na origem
        visitados = {0}  # Conjunto de nós já visitados
        
        # Enquanto não visitou todos os nós
        while len(visitados) < n:
            atual = rota[-1]
            proximo = None
            menor_distancia = float('inf')
            
            # Encontra o próximo nó mais próximo
            for i in range(n):
                if i not in visitados and matriz[atual][i] < menor_distancia:
                    menor_distancia = matriz[atual][i]
                    proximo = i
            
            if proximo is not None:
                rota.append(proximo)
                visitados.add(proximo)
            else:
                break
        
        # Adiciona retorno à origem
        rota.append(0)
        return rota
    
    def gerar_link_maps(self, coordenadas_otimizadas):
        """
        Gera link do Google Maps com a rota otimizada
        Garante que o destino seja a origem (empresa) para mostrar o retorno
        """
        if not coordenadas_otimizadas:
            return ""
        
        # Se a rota tem retorno à origem, o último ponto deve ser igual ao primeiro
        if len(coordenadas_otimizadas) > 1 and coordenadas_otimizadas[0] == coordenadas_otimizadas[-1]:
            # Remove o último ponto duplicado para o link do Maps
            coordenadas_para_link = coordenadas_otimizadas[:-1]
        else:
            coordenadas_para_link = coordenadas_otimizadas
        
        origem = f"{coordenadas_para_link[0][0]},{coordenadas_para_link[0][1]}"
        destino = f"{coordenadas_para_link[0][0]},{coordenadas_para_link[0][1]}"  # Destino = Origem (retorno à empresa)
        
        waypoints = []
        for i in range(1, len(coordenadas_para_link)):
            lat, lon = coordenadas_para_link[i]
            waypoints.append(f"{lat},{lon}")
        
        waypoints_str = "|".join(waypoints) if waypoints else ""
        
        link = f"https://www.google.com/maps/dir/?api=1&origin={origem}&destination={destino}"
        if waypoints_str:
            link += f"&waypoints={waypoints_str}"
        
        return link
    
    def _calcular_matriz_otimizada(self, G, nos, coordenadas):
        """
        Calcula matriz de distâncias com otimizações de performance
        """
        n = len(nos)
        matriz = [[0]*n for _ in range(n)]
        
        # Para poucos pontos (<= 4), usa algoritmo mais simples
        if n <= 4:
            return self._calcular_matriz_simples(G, nos, coordenadas)
        
        # Para muitos pontos, usa otimizações mais avançadas
        for i in range(n):
            for j in range(i+1, n):  # Calcula apenas metade da matriz (simétrica)
                try:
                    # Tenta calcular distância real no grafo
                    distancia = int(nx.shortest_path_length(G, nos[i], nos[j], weight='length'))
                    matriz[i][j] = distancia
                    matriz[j][i] = distancia  # Matriz simétrica
                except Exception as e:
                    # Fallback para distância em linha reta
                    distancia = self._calcular_distancia_haversine(coordenadas[i], coordenadas[j])
                    matriz[i][j] = distancia
                    matriz[j][i] = distancia
        
        return matriz
    
    def _calcular_matriz_simples(self, G, nos, coordenadas):
        """
        Calcula matriz simples para poucos pontos
        """
        n = len(nos)
        matriz = [[0]*n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    try:
                        distancia = int(nx.shortest_path_length(G, nos[i], nos[j], weight='length'))
                        matriz[i][j] = distancia
                    except Exception as e:
                        # Fallback para distância em linha reta
                        matriz[i][j] = self._calcular_distancia_haversine(coordenadas[i], coordenadas[j])
        
        return matriz
    
    def _calcular_distancia_haversine(self, coord1, coord2):
        """
        Calcula distância em linha reta usando fórmula de Haversine
        """
        import math
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 6371000  # Raio da Terra em metros
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return int(R * c)
    
    def _limpar_cache_expirado(self):
        """
        Remove entradas expiradas dos caches para evitar vazamento de memória
        """
        current_time = time.time()
        
        # Limpa cache de geocodificação
        expired_keys = [
            key for key, data in self._geocoding_cache.items()
            if current_time - data['timestamp'] > self._geocoding_ttl
        ]
        for key in expired_keys:
            del self._geocoding_cache[key]
        
        # Limpa cache de grafos
        expired_keys = [
            key for key, data in self._grafos_cache.items()
            if current_time - data['timestamp'] > self._grafos_ttl
        ]
        for key in expired_keys:
            del self._grafos_cache[key]
        
        # Limpa cache de preços
        expired_keys = [
            key for key, data in self._precos_cache.items()
            if current_time - data['timestamp'] > self._precos_ttl
        ]
        for key in expired_keys:
            del self._precos_cache[key]
    
    def _obter_grafo_regiao(self, coordenadas):
        """
        Obtém grafo OSMnx com cache por região geográfica
        """
        # Calcula região baseada nas coordenadas (grid de 10km)
        media_lat = sum(lat for lat, lon in coordenadas) / len(coordenadas)
        media_lon = sum(lon for lat, lon in coordenadas) / len(coordenadas)
        
        # Cria chave de cache baseada na região (arredonda para grid de ~10km)
        grid_lat = round(media_lat / 0.09) * 0.09  # ~10km em graus
        grid_lon = round(media_lon / 0.09) * 0.09
        cache_key = f"grafo_{grid_lat:.3f}_{grid_lon:.3f}"
        
        # Verifica cache primeiro
        if cache_key in self._grafos_cache:
            cached_data = self._grafos_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self._grafos_ttl:
                return cached_data['grafo']
        
        try:
            # Baixa o grafo com configurações otimizadas
            G = ox.graph_from_point(
                (media_lat, media_lon), 
                dist=6000,  # Reduzido de 8000 para 6000 (melhor performance)
                network_type='drive',
                simplify=True,
                retain_all=False  # Remove nós desnecessários
            )
            
            # Armazena no cache
            self._grafos_cache[cache_key] = {
                'grafo': G,
                'timestamp': time.time()
            }
            
            return G
        except Exception as e:
            print(f"Erro ao baixar grafo: {e}")
            return None

    def otimizar_rota(self, enderecos, veiculo=None, produtos_quantidades=None, preco_combustivel_personalizado=None):
        """
        Função principal para otimizar a rota (OTIMIZADA)
        """
        try:
            # Limpeza periódica de cache (a cada 10 otimizações)
            self._cache_cleanup_counter += 1
            if self._cache_cleanup_counter % 10 == 0:
                self._limpar_cache_expirado()
            # 1. Geocodifica todos os endereços (com cache)
            coordenadas = [self.geocodificar_endereco(endereco) for endereco in enderecos]
            
            # Verifica se todas as coordenadas foram obtidas
            if None in coordenadas:
                return {
                    'sucesso': False,
                    'erro': 'Não foi possível geocodificar todos os endereços'
                }
            
            # 2. Obtém grafo com cache por região
            if len(coordenadas) > 1:
                G = self._obter_grafo_regiao(coordenadas)
                
                if G is not None:
                    try:
                        # 3. Mapeia coordenadas para nós do grafo
                        nos = [ox.distance.nearest_nodes(G, lon, lat) for lat, lon in coordenadas]
                        
                        # 4. Calcula a matriz de distâncias otimizada
                        n = len(nos)
                        matriz = self._calcular_matriz_otimizada(G, nos, coordenadas)
                        
                        # 5. Resolve o TSP
                        rota_otimizada = self.resolver_tsp(matriz)
                        
                        if rota_otimizada:
                            # 6. Converte índices em coordenadas otimizadas
                            coordenadas_otimizadas = [coordenadas[i] for i in rota_otimizada]
                            enderecos_otimizados = [enderecos[i] for i in rota_otimizada]
                            
                            # Garante que a rota sempre termine na origem (empresa)
                            # Se o último ponto não for a origem, adiciona a origem como ponto final
                            if coordenadas_otimizadas and coordenadas_otimizadas[-1] != coordenadas_otimizadas[0]:
                                coordenadas_otimizadas.append(coordenadas_otimizadas[0])
                                enderecos_otimizados.append(enderecos[0])
                            
                            # 7. Calcula distância real usando a matriz e tempo
                            distancia_total_km, tempo_estimado_minutos = self.calcular_distancia_real(matriz, rota_otimizada)
                            
                            # 8. Calcula valor da rota
                            valor_rota, preco_combustivel = self.calcular_valor_rota(distancia_total_km, veiculo, preco_combustivel_personalizado)
                            
                            # 9. Gera link do Maps
                            link_maps = self.gerar_link_maps(coordenadas_otimizadas)
                            
                            return {
                                'enderecos_otimizados': enderecos_otimizados,
                                'coordenadas_otimizadas': coordenadas_otimizadas,  # Inclui retorno à origem
                                'distancia_total_km': distancia_total_km,
                                'tempo_estimado_minutos': tempo_estimado_minutos,
                                'valor_rota': valor_rota,
                                'preco_combustivel_usado': preco_combustivel,
                                'link_maps': link_maps,
                                'sucesso': True
                            }
                    
                    except Exception as e:
                        print(f"Erro ao processar grafo: {e}")
            
            # Fallback: rota simples sem otimização
            coordenadas_otimizadas = coordenadas.copy()
            enderecos_otimizados = enderecos.copy()
            
            # Garante que a rota sempre termine na origem (empresa)
            if coordenadas_otimizadas and coordenadas_otimizadas[-1] != coordenadas_otimizadas[0]:
                coordenadas_otimizadas.append(coordenadas_otimizadas[0])
                enderecos_otimizados.append(enderecos[0])
            
            # Para o fallback, usa distância em linha reta (já que não temos matriz)
            distancia_total_km, tempo_estimado_minutos = self.calcular_distancia_tempo(coordenadas_otimizadas)
            
            valor_rota, preco_combustivel = self.calcular_valor_rota(distancia_total_km, veiculo, preco_combustivel_personalizado)
            link_maps = self.gerar_link_maps(coordenadas_otimizadas)
            
            return {
                'enderecos_otimizados': enderecos_otimizados,
                'coordenadas_otimizadas': coordenadas_otimizadas,  # Inclui retorno à origem
                'distancia_total_km': distancia_total_km,
                'tempo_estimado_minutos': tempo_estimado_minutos,
                'valor_rota': valor_rota,
                'preco_combustivel_usado': preco_combustivel,
                'link_maps': link_maps,
                'sucesso': True
            }
            
        except Exception as e:
            print(f"Erro na otimização da rota: {e}")
            return {
                'sucesso': False,
                'erro': str(e)
            } 