# MILO Backend

Sistema de configuração logística inteligente para microindústrias

## Pré-requisitos
- Python 3.10+
- MySQL
- Git

## Passo a passo para rodar o projeto

### 1. Clone o repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd backend
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente do banco
- Crie o arquivo abaixo na pasta raiz:
  ```
  DBCREDENTIALS.env
  ```
- Insira no arquivo `DBCREDENTIALS.env` os dados do seu MySQL:
  ```
  DB_NAME=milo_db
  DB_USER=seu_usuario
  DB_PASSWORD=sua_senha
  DB_HOST=localhost
  DB_PORT=3306
  ```

### 4. Crie o banco de dados no MySQL
Acesse o MySQL e execute:
```sql
CREATE DATABASE milo_db;
```

### 5. Aplique as migrações
```bash
python manage.py makemigrations
python manage.py migrate
```
ou
```bash
py manage.py makemigrations
py manage.py migrate
```

### 6. Inicie o servidor
```bash
python manage.py runserver
```
ou
```bash
py manage.py runserver
```

### 7. Teste as rotas de registro e login no Postman

#### Cadastro de usuário
- **Endpoint:** `POST http://127.0.0.1:8000/api/usuarios/register/`
- **Body (JSON):**
  ```json
  {
    "cnpj": "12345678000199",
    "nome": "Empresa Exemplo",
    "telefone": "11999999999",
    "email": "empresa@exemplo.com",
    "cep": "12345678",
    "rua": "Rua Exemplo",
    "numero": "123",
    "bairro": "Centro",
    "cidade": "São Paulo",
    "estado": "SP",
    "password": "senhaSegura123"
  }
  ```

**⚠️ Validações importantes:**
- **CNPJ e Nome** são obrigatórios
- **Email OU Telefone** - pelo menos um dos dois deve ser fornecido (não é obrigatório fornecer ambos)
- **Todos os campos de endereço** são obrigatórios: cep, rua, numero, bairro, cidade, estado

**Exemplos válidos:**

**Cadastro apenas com email:**
```json
{
  "cnpj": "12345678000199",
  "nome": "Empresa Exemplo",
  "email": "empresa@exemplo.com",
  "cep": "12345678",
  "rua": "Rua Exemplo",
  "numero": "123",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "estado": "SP",
  "password": "senhaSegura123"
}
```

**Cadastro apenas com telefone:**
```json
{
  "cnpj": "12345678000198",
  "nome": "Empresa Exemplo 2",
  "telefone": "11999999999",
  "cep": "12345678",
  "rua": "Rua Exemplo",
  "numero": "123",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "estado": "SP",
  "password": "senhaSegura123"
}
```

**Cadastro com ambos (email e telefone):**
```json
{
  "cnpj": "12345678000197",
  "nome": "Empresa Exemplo 3",
  "telefone": "11999999999",
  "email": "empresa@exemplo.com",
  "cep": "12345678",
  "rua": "Rua Exemplo",
  "numero": "123",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "estado": "SP",
  "password": "senhaSegura123"
}
```

**❌ Exemplos que gerarão erro:**

**Erro: Nenhum contato fornecido**
```json
{
  "cnpj": "12345678000199",
  "nome": "Empresa Exemplo",
  "cep": "12345678",
  "rua": "Rua Exemplo",
  "numero": "123",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "estado": "SP",
  "password": "senhaSegura123"
}
```
*Erro: "Pelo menos um dos campos: email ou telefone deve ser fornecido"*

**Erro: Campos de endereço faltando**
```json
{
  "cnpj": "12345678000199",
  "nome": "Empresa Exemplo",
  "email": "empresa@exemplo.com",
  "password": "senhaSegura123"
}
```
*Erro: "Os seguintes campos de endereço são obrigatórios: cep, rua, numero, bairro, cidade, estado"*

#### Login
- **Endpoint:** `POST http://127.0.0.1:8000/api/usuarios/login/`
- **Body (JSON):**
  ```json
  {
    "cnpj": "12345678000199",
    "password": "senhaSegura123"
  }
  ```
- **Resposta:**
  ```json
  {
    "refresh": "...",
    "access": "..."
  }
  ```

#### Logout
- **Endpoint:** `POST http://127.0.0.1:8000/api/usuarios/logout/`
- **Headers:**
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
  - `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
    "refresh_token": "SEU_REFRESH_TOKEN_AQUI"
  }
  ```
- **Resposta de sucesso:**
  ```json
  {
    "message": "Logout realizado com sucesso"
  }
  ```
- **Observação:** O refresh token será invalidado e não poderá ser usado novamente

#### Trocar senha
- **Endpoint:** `POST http://127.0.0.1:8000/api/usuarios/trocar-senha/`
- **Headers:**
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
  - `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
    
  "nova_senha": "novaSenhaSegura123"

  }
  ```
- **Resposta de sucesso:**
  ```json
  
  {
  "mensagem": "Senha atualizada com sucesso"

  }
  ```
  - **Observação:** Essa rota exige autenticação com token válido (access token)


#### Deletar conta
- **Endpoint:**  `DELETE http://127.0.0.1:8000/api/usuarios/deletar-conta/`

- **Headers:**

  -  `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

- **Body (JSON):**  

  - `não é necessário enviar nenhum corpo na requisição`

- **Resposta de sucesso:**
  ```json
  
  {
  "mensagem": "Conta deletada com sucesso"

  }
  ```
  - **Observação:**A conta autenticada será permanentemente removida do sistema


#### Usando o token de acesso
- Para acessar rotas protegidas, envie o token no header:
  - **Key:** `Authorization`
  - **Value:** `Bearer SEU_TOKEN_AQUI`

---

### 8. Teste as outras rotas no Postman

#### 📦 **Produtos**

#### Cadastrar Produto com Categoria Existente
- **Endpoint:** `POST http://127.0.0.1:8000/api/produtos/cadastrar-com-categoria/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Body (JSON):**
  ```json
  {
    "nome": "Notebook Pro",
    "codigo_barras": "9876543210987",
    "descricao": "Notebook profissional",
    "data_fabricacao": "2024-01-15",
    "validade": "2025-01-15",
    "lote": "LOT002",
    "preco_custo": "1500.00",
    "preco_venda": "2200.00",
    "marca": "TechBrand",
    "estoque_minimo": 3,
    "estoque_atual": 8,
    "fornecedor": 1,
    "categoria_id": 1
  }
  ```

#### Cadastrar Produto Criando Nova Categoria
- **Endpoint:** `POST http://127.0.0.1:8000/api/produtos/cadastrar-com-categoria/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Body (JSON):**
  ```json
  {
    "nome": "Produto Especial",
    "codigo_barras": "1112223334445",
    "descricao": "Produto com categoria nova",
    "data_fabricacao": "2024-01-15",
    "validade": "2025-01-15",
    "lote": "LOT003",
    "preco_custo": "100.00",
    "preco_venda": "150.00",
    "marca": "MarcaNova",
    "estoque_minimo": 3,
    "estoque_atual": 8,
    "fornecedor": 1,
    "nova_categoria": "Categoria Especial"
  }
  ```
#### Listar Produtos
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Atualizar Produto
- **Endpoint:** `PUT http://127.0.0.1:8000/api/produtos/{id}/atualizar/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Body (JSON):**
  ```json
  {
    "nome": "Smartphone XYZ Atualizado",
    "codigo_barras": "1234567890123",
    "descricao": "Smartphone atualizado",
    "data_fabricacao": "2024-01-15",
    "validade": "2025-01-15",
    "lote": "LOT001",
    "preco_custo": "850.00",
    "preco_venda": "1250.00",
    "marca": "TechBrand",
    "estoque_minimo": 5,
    "estoque_atual": 12,
    "fornecedor": 1,
    "categoria": 1
  }
  ```

#### Excluir Produto
- **Endpoint:** `DELETE http://127.0.0.1:8000/api/produtos/{id}/excluir/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Criar Categoria
- **Endpoint:** `POST http://127.0.0.1:8000/api/produtos/categorias/criar/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Body (JSON):**
  ```json
  {
    "nome": "Eletrônicos"
  }
  ```
#### Listar Categorias
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/categorias/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Criar Fornecedor
- **Endpoint:** `POST http://127.0.0.1:8000/api/produtos/fornecedores/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Body (JSON):**
  ```json
  {
    "nome": "Fornecedor ABC LTDA",
    "telefone": "(11) 99999-9999",
    "email": "contato@fornecedorabc.com",
    "endereco": "Rua do Fornecedor, 123 - São Paulo/SP"
  }
  ```
#### Listar Fornecedores
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/fornecedores/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### 📊 **Movimentações de Estoque**

O sistema registra automaticamente todas as movimentações de estoque quando:
- **Criação de produto**: Se o produto for criado com estoque inicial, registra uma movimentação de entrada
- **Atualização de produto**: Se o estoque for alterado durante a atualização, registra automaticamente a movimentação

#### Listar Todas as Movimentações
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/movimentacoes/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Resposta:**
  ```json
  [
    {
      "id": 1,
      "produto": 1,
      "produto_nome": "Smartphone XYZ",
      "tipo": "entrada",
      "tipo_display": "Entrada",
      "quantidade": 20,
      "estoque_anterior": 0,
      "estoque_atual": 20,
      "data_movimentacao": "2024-01-20T10:30:00Z",
      "observacao": "Cadastro inicial do produto"
    },
    {
      "id": 2,
      "produto": 1,
      "produto_nome": "Smartphone XYZ",
      "tipo": "saida",
      "tipo_display": "Saída",
      "quantidade": 5,
      "estoque_anterior": 20,
      "estoque_atual": 15,
      "data_movimentacao": "2024-01-20T11:00:00Z",
      "observacao": "Remoção de 5 unidades do estoque"
    }
  ]
  ```

#### Listar Movimentações de um Produto Específico
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/movimentacoes/produto/{produto_id}/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Filtrar Movimentações por Tipo
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/movimentacoes/?tipo=entrada`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Filtrar Movimentações por Produto
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/movimentacoes/?produto=1`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Buscar Movimentações por Texto
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/movimentacoes/?search=Smartphone`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### 🔍 **Filtros e Busca**

#### Filtrar Produtos por Categoria
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/?categoria=1`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Buscar Produtos por Nome ou Marca
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/?search=smartphone`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

---

#### 🚗 **Veículos**

#### Cadastrar Veículo
- **Endpoint:** `POST http://127.0.0.1:8000/api/rotas/veiculos/criar/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Body (JSON):**
  ```json
  {
    "nome": "Caminhão Mercedes-Benz",
    "tipo_combustivel": "diesel",
    "consumo_por_km": "2.5"
  }
  ```
- **Resposta:**
  ```json
  {
    "id": 1,
    "nome": "Caminhão Mercedes-Benz",
    "tipo_combustivel": "diesel",
    "tipo_combustivel_display": "Diesel",
    "consumo_por_km": "2.50",
    "data_cadastro": "2024-01-20T10:30:00Z",
    "data_atualizacao": "2024-01-20T10:30:00Z"
  }
  ```

#### Listar Veículos
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/veiculos/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Resposta:**
  ```json
  [
    {
      "id": 1,
      "nome": "Caminhão Mercedes-Benz",
      "tipo_combustivel": "diesel",
      "tipo_combustivel_display": "Diesel",
      "consumo_por_km": "2.50",
      "data_cadastro": "2024-01-20T10:30:00Z",
      "data_atualizacao": "2024-01-20T10:30:00Z"
    },
    {
      "id": 2,
      "nome": "Van Ford Transit",
      "tipo_combustivel": "gasolina",
      "tipo_combustivel_display": "Gasolina",
      "consumo_por_km": "1.8",
      "data_cadastro": "2024-01-20T11:00:00Z",
      "data_atualizacao": "2024-01-20T11:00:00Z"
    }
  ]
  ```

#### Obter Detalhes de um Veículo
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/veiculos/{id}/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Resposta:**
  ```json
  {
    "id": 1,
    "nome": "Caminhão Mercedes-Benz",
    "tipo_combustivel": "diesel",
    "tipo_combustivel_display": "Diesel",
    "consumo_por_km": "2.50",
    "data_cadastro": "2024-01-20T10:30:00Z",
    "data_atualizacao": "2024-01-20T10:30:00Z"
  }
  ```

#### Atualizar Veículo
- **Endpoint:** `PUT http://127.0.0.1:8000/api/rotas/veiculos/{id}/atualizar/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Body (JSON):**
  ```json
  {
    "nome": "Caminhão Mercedes-Benz Atualizado",
    "tipo_combustivel": "diesel",
    "consumo_por_km": "2.3"
  }
  ```

#### Excluir Veículo
- **Endpoint:** `DELETE http://127.0.0.1:8000/api/rotas/veiculos/{id}/excluir/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### 🔍 **Filtros e Busca para Veículos**

#### Filtrar Veículos por Tipo de Combustível
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/veiculos/?tipo_combustivel=diesel`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Buscar Veículos por Nome
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/veiculos/?search=mercedes`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Valores Válidos para Tipo de Combustível
- `diesel` - Diesel
- `gasolina` - Gasolina

---

#### 🛣️ **Rotas Otimizadas**

#### Criar Rota Otimizada
- **Endpoint:** `POST http://127.0.0.1:8000/api/rotas/rotas/criar/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Body (JSON):**
  ```json
  {
    "enderecos_destino": [
      "Avenida Paulista, 1000, São Paulo, Brasil",
      "Rua Augusta, 1500, São Paulo, Brasil",
      "Mercado Municipal de São Paulo"
    ],
    "nome_motorista": "João Silva",
    "veiculo_id": 1,
    "produtos_quantidades": [
      {
        "produto_id": 1,
        "quantidade": 5
      },
      {
        "produto_id": 2,
        "quantidade": 3
      }
    ]
  }
  ```
  
  **Exemplo sem veículo e motorista (campos opcionais):**
  ```json
  {
    "enderecos_destino": [
      "Rua Prof. Silvio de Macedo, 125, Jatiúca",
      "Universidade Federal de Alagoas"
    ],
    "produtos_quantidades": [
      {
        "produto_id": 1,
        "quantidade": 5
      }
    ]
  }
  ```
- **Resposta:**
  ```json
  {
    "id": 1,
    "data_geracao": "2024-01-20T10:30:00Z",
    "enderecos_otimizados": [
      "Rua da Empresa",
      "Universidade Federal de Alagoas",
      "Rua Prof. Silvio de Macedo, 125, Jatiúca",
      "Rua da Empresa"
    ],
    "coordenadas_otimizadas": [
      [-11.1111, -11.1111],
      [-9.5536252, -35.7739006],
      [-9.6461711, -35.7034641],
      [-11.1111, -11.1111]
    ],
    "distancia_total_km": "25.50",
    "tempo_estimado_minutos": 45,
    "veiculo": 1,
    "veiculo_nome": "Caminhão Mercedes-Benz",
    "nome_motorista": "João Silva",
    "valor_rota": "350.75",
    "produtos_quantidades": [
      {
        "produto_id": 1,
        "quantidade": 5
      },
      {
        "produto_id": 2,
        "quantidade": 3
      }
    ],
    "link_maps": "https://www.google.com/maps/dir/?api=1&origin=-23.5505,-46.6333&destination=-23.5505,-46.6333&waypoints=-23.5631,-46.6544|-23.5489,-46.6388",
    "status": "em_progresso",
    "status_display": "Em Progresso",
    "preco_combustivel_na_geracao": 5.50
  }
  ```

#### Listar Rotas
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/rotas/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Resposta:**
  ```json
  [
    {
      "id": 1,
      "data_geracao": "2024-01-20T10:30:00Z",
      "enderecos_otimizados": [...],
      "coordenadas_otimizadas": [...],
      "distancia_total_km": "25.50",
      "tempo_estimado_minutos": 45,
      "veiculo": 1,
      "veiculo_nome": "Caminhão Mercedes-Benz",
      "nome_motorista": "João Silva",
      "valor_rota": "350.75",
      "produtos_quantidades": [...],
      "link_maps": "...",
      "status": "em_progresso",
      "status_display": "Em Progresso",
      "preco_combustivel_na_geracao": 5.8
    }
  ]
  ```

#### Obter Detalhes de uma Rota
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/rotas/{id}/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Atualizar Status da Rota
- **Endpoint:** `PUT http://127.0.0.1:8000/api/rotas/rotas/{id}/status/`
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Body (JSON):**
  ```json
  {
    "status": "concluido"
  }
  ```

#### Excluir Rota
- **Endpoint:** `DELETE http://127.0.0.1:8000/api/rotas/rotas/{id}/excluir/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### 🔍 **Filtros e Busca para Rotas**

#### Filtrar Rotas por Status
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/rotas/?status=em_progresso`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Filtrar Rotas por Veículo
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/rotas/?veiculo=1`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Buscar Rotas por Nome do Motorista
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/rotas/?search=joão`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Valores Válidos para Status da Rota
- `em_progresso` - Em Progresso
- `concluido` - Concluído

#### ⛽ **Preços de Combustível**

#### Obter Preços Atuais
- **Endpoint:** `GET http://127.0.0.1:8000/api/rotas/precos-combustivel/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`
- **Resposta:**
  ```json
  {
    "diesel": 5.50,
    "gasolina": 5.80,
    "unidade": "R$/L",
    "fonte": "combustivelapi.com.br",
    "atualizado_em": "2024-01-20T10:30:00Z"
  }
  ```

---

## 📋 **Ordem Sugerida de Testes**

1. **Registrar usuário** (POST `/api/usuarios/register/`)
2. **Login** (POST `/api/usuarios/login/`) - Guarde o token
3. **Criar categoria** (POST `/api/produtos/categorias/criar/`)
4. **Criar fornecedor** (POST `/api/produtos/fornecedores/`)
5. **Cadastrar produto** (POST `/api/produtos/cadastrar-com-categoria/`)
6. **Listar produtos** (GET `/api/produtos/`)
7. **Verificar movimentações** (GET `/api/produtos/movimentacoes/`)
8. **Atualizar produto** (PUT `/api/produtos/{id}/atualizar/`) - Alterar estoque
9. **Verificar movimentações novamente** (GET `/api/produtos/movimentacoes/`)
10. **Cadastrar veículo** (POST `/api/rotas/veiculos/criar/`)
11. **Listar veículos** (GET `/api/rotas/veiculos/`)
12. **Atualizar veículo** (PUT `/api/rotas/veiculos/{id}/atualizar/`)
13. **Testar filtros de veículos** (GET `/api/rotas/veiculos/?tipo_combustivel=diesel`)
14. **Obter preços de combustível** (GET `/api/rotas/precos-combustivel/`)
15. **Criar rota otimizada** (POST `/api/rotas/rotas/criar/`)
16. **Listar rotas** (GET `/api/rotas/rotas/`)
17. **Verificar movimentações de estoque da rota** (GET `/api/produtos/movimentacoes/`)
18. **Atualizar status da rota** (PUT `/api/rotas/rotas/{id}/status/`)
19. **Testar filtros de rotas** (GET `/api/rotas/rotas/?status=em_progresso`)
20. **Testar outros endpoints**

---

## Observações
- **Nunca commite o arquivo `DBCCREDENTIALS.env`!**
- Todos os endpoints de produtos, veículos e rotas requerem autenticação
- Código de barras deve ter exatamente 13 dígitos numéricos
- Preço de venda não pode ser menor que o preço de custo
- Categorias e fornecedores são únicos por usuário
- Fornecedores não podem ter o mesmo nome para o mesmo usuário
- **Movimentações de estoque são registradas automaticamente** quando o estoque é alterado
- Veículos e rotas são isolados por usuário (multi-tenant)
- **Rotas sempre começam e terminam no endereço do usuário** (origem = destino)
- **Estoque é automaticamente reduzido** quando uma rota é criada
- **Algoritmo de otimização usa TSP (Traveling Salesman Problem)** para encontrar a melhor rota

### Metadados obrigatórios do Produto
- nome
- preco_custo
- preco_venda
- estoque_minimo
- estoque_atual

Os demais campos (código de barras, descrição, data de fabricação, lote, marca, fornecedor, categoria) são opcionais.

### Metadados obrigatórios do Veículo
- nome
- tipo_combustivel (diesel ou gasolina)
- consumo_por_km (deve ser maior que 0.01 L/km)

### Metadados obrigatórios para Criar Rota
- enderecos_destino (lista de endereços)
- produtos_quantidades (lista com produto_id e quantidade)

### Metadados opcionais para Criar Rota
- nome_motorista (string, opcional)
- veiculo_id (integer, opcional - se não informado, usa veículo padrão com consumo de 2.0 L/km)

### Metadados retornados na Rota
- **preco_combustivel_na_geracao**: Preço do combustível usado no cálculo da rota (R$/L)
- **valor_rota**: Custo total da rota calculado com o preço do combustível da época
- **distancia_total_km**: Distância total da rota otimizada
- **tempo_estimado_minutos**: Tempo estimado para completar a rota

### Dependências Adicionais
O sistema de rotas requer as seguintes bibliotecas Python:
- osmnx (para geocodificação e análise de redes)
- networkx (para algoritmos de grafos)
- ortools (para otimização TSP)
- requests (para APIs externas)

### API de Preços de Combustível
O sistema integra com a API `combustivelapi.com.br` para obter preços atualizados de combustível:
- **Endpoint:** `GET /api/rotas/precos-combustivel/`
- **Fonte:** https://combustivelapi.com.br
- **Fallback:** Valores padrão caso a API esteja indisponível
- **Mapeamento:** Diesel (diesel, diesel_s10) e Gasolina (gasolina_comum, gasolina_aditivada)

### Veículo Padrão
Quando nenhum veículo é especificado na criação da rota:
- **Consumo padrão:** 2.0 L/km
- **Tipo de combustível:** Gasolina
- **Nome exibido:** "Veículo Padrão"
- **Cálculo:** Usa preço da gasolina atual para calcular o valor da rota
