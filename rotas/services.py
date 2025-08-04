import osmnx as ox
import networkx as nx
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import requests
from decimal import Decimal
import json

class RotaOtimizacaoService:
    def __init__(self):
        self.API_KEY_GOOGLE_MAPS = None  # Será configurado via settings
        
    def obter_preco_combustivel(self, tipo_combustivel):
        """
        Retorna preços fixos de combustível
        """
        # Valores fixos de combustível
        precos = {
            'diesel': 5.80,  # R$/L
            'gasolina': 6.36,  # R$/L
        }
        return precos.get(tipo_combustivel, 5.80)
    
    def geocodificar_endereco(self, endereco):
        """
        Geocodifica um endereço para coordenadas
        Por enquanto, usa OSMnx para geocodificação
        """
        try:
            return ox.geocode(endereco)
        except Exception as e:
            # Fallback: coordenadas de Maceió (já que os endereços são de lá)
            print(f"Erro na geocodificação de {endereco}: {e}")
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

        # Configura estratégia de solução inicial
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

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
    
    def otimizar_rota(self, enderecos, veiculo=None, produtos_quantidades=None):
        """
        Função principal para otimizar a rota
        """
        try:
            # 1. Geocodifica todos os endereços
            coordenadas = [self.geocodificar_endereco(endereco) for endereco in enderecos]
            
            # Verifica se todas as coordenadas foram obtidas
            if None in coordenadas:
                return {
                    'sucesso': False,
                    'erro': 'Não foi possível geocodificar todos os endereços'
                }
            
            # 2. Baixa o grafo com ruas em torno de todos os pontos
            if len(coordenadas) > 1:
                media_lat = sum(lat for lat, lon in coordenadas) / len(coordenadas)
                media_lon = sum(lon for lat, lon in coordenadas) / len(coordenadas)
                
                try:
                    # Tenta baixar o grafo com configurações mais robustas
                    G = ox.graph_from_point(
                        (media_lat, media_lon), 
                        dist=8000, 
                        network_type='drive',
                        simplify=True
                    )
                    
                    # 3. Mapeia coordenadas para nós do grafo
                    nos = [ox.distance.nearest_nodes(G, lon, lat) for lat, lon in coordenadas]
                    
                    # 4. Calcula a matriz de distâncias reais (em metros)
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
                                    lat1, lon1 = coordenadas[i]
                                    lat2, lon2 = coordenadas[j]
                                    import math
                                    R = 6371000  # Raio da Terra em metros
                                    lat1_rad = math.radians(lat1)
                                    lat2_rad = math.radians(lat2)
                                    delta_lat = math.radians(lat2 - lat1)
                                    delta_lon = math.radians(lon2 - lon1)
                                    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
                                         math.cos(lat1_rad) * math.cos(lat2_rad) *
                                         math.sin(delta_lon/2) * math.sin(delta_lon/2))
                                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                                    distancia = int(R * c)
                                    matriz[i][j] = distancia
                    
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
                        if veiculo:
                            preco_combustivel = self.obter_preco_combustivel(veiculo.tipo_combustivel)
                            consumo_por_km = float(veiculo.consumo_por_km)
                        else:
                            # Usa valores padrão se não houver veículo
                            preco_combustivel = self.obter_preco_combustivel('gasolina')  # padrão
                            consumo_por_km = 2.0  # L/km padrão
                        
                        valor_rota = float(distancia_total_km) * consumo_por_km * preco_combustivel
                        
                        # 9. Gera link do Maps
                        link_maps = self.gerar_link_maps(coordenadas_otimizadas)
                        
                        return {
                            'enderecos_otimizados': enderecos_otimizados,
                            'coordenadas_otimizadas': coordenadas_otimizadas,  # Inclui retorno à origem
                            'distancia_total_km': distancia_total_km,
                            'tempo_estimado_minutos': tempo_estimado_minutos,
                            'valor_rota': valor_rota,
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
            
            if veiculo:
                preco_combustivel = self.obter_preco_combustivel(veiculo.tipo_combustivel)
                consumo_por_km = float(veiculo.consumo_por_km)
            else:
                # Usa valores padrão se não houver veículo
                preco_combustivel = self.obter_preco_combustivel('gasolina')  # padrão
                consumo_por_km = 2.0  # L/km padrão
            
            valor_rota = float(distancia_total_km) * consumo_por_km * preco_combustivel
            link_maps = self.gerar_link_maps(coordenadas_otimizadas)
            
            return {
                'enderecos_otimizados': enderecos_otimizados,
                'coordenadas_otimizadas': coordenadas_otimizadas,  # Inclui retorno à origem
                'distancia_total_km': distancia_total_km,
                'tempo_estimado_minutos': tempo_estimado_minutos,
                'valor_rota': valor_rota,
                'link_maps': link_maps,
                'sucesso': True
            }
            
        except Exception as e:
            print(f"Erro na otimização da rota: {e}")
            return {
                'sucesso': False,
                'erro': str(e)
            } 