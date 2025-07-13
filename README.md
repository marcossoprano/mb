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
    "endereco": "Rua Exemplo, 123",
    "password": "senhaSegura123"
  }
  ```



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

## API Endpoints Completos

### 🔐 **Autenticação e Usuários**

#### Renovar Token
- **Endpoint:** `POST http://127.0.0.1:8000/api/usuarios/token/refresh/`
- **Headers:** `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
    "refresh": "SEU_REFRESH_TOKEN_AQUI"
  }
  ```

### 📦 **Produtos**

#### Listar Categorias
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/categorias/`
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

#### Listar Fornecedores
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/fornecedores/`
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

#### Listar Produtos
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`



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

#### Teste sem Autenticação (REMOVER EM PRODUÇÃO)
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/teste/`
- **Headers:** Nenhum

### 🔍 **Filtros e Busca**

#### Filtrar Produtos por Categoria
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/?categoria=1`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

#### Buscar Produtos por Nome ou Marca
- **Endpoint:** `GET http://127.0.0.1:8000/api/produtos/?search=smartphone`
- **Headers:** `Authorization: Bearer SEU_ACCESS_TOKEN_AQUI`

---

## 📋 **Ordem Sugerida de Testes**

1. **Registrar usuário** (POST `/api/usuarios/register/`)
2. **Login** (POST `/api/usuarios/login/`) - Guarde o token
3. **Criar categoria** (POST `/api/produtos/categorias/criar/`)
4. **Criar fornecedor** (POST `/api/produtos/fornecedores/`)
5. **Cadastrar produto** (POST `/api/produtos/cadastrar-com-categoria/`)
6. **Listar produtos** (GET `/api/produtos/`)
7. **Testar outros endpoints**

**💡 Dica:** Use as variáveis do Postman para armazenar o token e reutilizar nos outros requests!

---

## Observações
- **Nunca commite o arquivo `DBCREDENTIALS.env`!**
- Todos os endpoints de produtos requerem autenticação
- Código de barras deve ter exatamente 13 dígitos numéricos
- Preço de venda não pode ser menor que o preço de custo
- Categorias e fornecedores são únicos por usuário
- Fornecedores não podem ter o mesmo nome para o mesmo usuário
