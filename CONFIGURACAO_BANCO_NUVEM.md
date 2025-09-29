# Configuração PostgreSQL na Nuvem - Guia de Correção

## Problema Identificado
O erro `"could not translate host name"` indica que:
1. A senha estava incorreta (estava usando o hostname como senha)
2. O hostname não estava completo (faltava o domínio da nuvem)

## Correções Realizadas

### 1. Settings.py
✅ Adicionada configuração SSL (`sslmode: require`) necessária para bancos na nuvem

### 2. DBCREDENTIALS.env
✅ Corrigida estrutura do arquivo - agora você precisa:

## Próximos Passos

### 1. Complete as Credenciais
Edite o arquivo `DBCREDENTIALS.env` e configure:

```env
DB_NAME=milodb
DB_USER=milodb_user
DB_PASSWORD=SUA_SENHA_REAL_AQUI
DB_HOST=hostname_completo_do_render
DB_PORT=5432
```

### 2. Encontre as Credenciais Corretas
No painel do Render (ou sua plataforma de nuvem):
- **External Database URL** ou **Connection String**
- Formato geralmente: `postgresql://usuario:senha@hostname:5432/database`

Exemplo de hostname completo do Render:
- `dpg-d3da1lqli9vc73e8mmd0-a.oregon-postgres.render.com`
- `dpg-d3da1lqli9vc73e8mmd0-a.frankfurt-postgres.render.com`

### 3. Teste a Conexão
Após configurar as credenciais corretas:
```bash
python manage.py check
python manage.py migrate
```

## Dicas de Troubleshooting

### Se ainda houver erro de DNS:
1. Verifique se o hostname está completo com o domínio
2. Teste conectividade: `ping hostname_completo`
3. Verifique se o banco está ativo na plataforma

### Se houver erro de SSL:
- Confirme que o banco requer SSL
- Se não requer, remova a linha `'sslmode': 'require'` do settings.py

### Se houver erro de autenticação:
- Confirme usuário e senha no painel da plataforma
- Verifique se o usuário tem permissões adequadas

## Exemplo de Configuração Completa (Render)
```env
DB_NAME=milodb
DB_USER=milodb_user  
DB_PASSWORD=abc123xyz789
DB_HOST=dpg-d3da1lqli9vc73e8mmd0-a.oregon-postgres.render.com
DB_PORT=5432
```