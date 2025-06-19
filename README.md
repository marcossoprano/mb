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

#### Usando o token de acesso
- Para acessar rotas protegidas, envie o token no header:
  - **Key:** `Authorization`
  - **Value:** `Bearer SEU_TOKEN_AQUI`

---

## Observações
- **Nunca commite o arquivo `DBCREDENTIALS.env`!**
