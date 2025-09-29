# Migração MySQL → PostgreSQL - Instruções

## Alterações Realizadas

✅ **Concluído:**
1. Atualizado `requirements.txt`: substituído `mysqlclient` por `psycopg2-binary`
2. Modificado `settings.py`: alterado ENGINE de MySQL para PostgreSQL
3. Instaladas as novas dependências Python

## Próximos Passos

### 1. Configurar PostgreSQL
- Instale o PostgreSQL em seu sistema se ainda não tiver
- Crie um banco de dados para sua aplicação
- Crie um usuário com permissões adequadas

### 2. Configurar Variáveis de Ambiente
- Renomeie `DBCREDENTIALS.env.example` para `DBCREDENTIALS.env`
- Configure as seguintes variáveis:
  ```
  DB_NAME=nome_do_seu_banco
  DB_USER=seu_usuario_postgres
  DB_PASSWORD=sua_senha
  DB_HOST=localhost
  DB_PORT=5432
  ```

### 3. Executar Migrações
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Migrar Dados (se necessário)
Se você tem dados no MySQL que precisa migrar:
1. Exporte os dados do MySQL
2. Importe para o PostgreSQL
3. Ou use ferramentas como `pgloader` para migração automática

## Principais Diferenças MySQL vs PostgreSQL

### Tipos de Dados
- **MySQL:** Alguns tipos específicos como `TINYINT`
- **PostgreSQL:** Tipos mais rigorosos, como `BOOLEAN` ao invés de `TINYINT(1)`

### Sintaxe SQL
- **PostgreSQL** é mais rigoroso com padrões SQL
- Aspas duplas para identificadores, aspas simples para strings
- Case-sensitive por padrão

### Performance
- **PostgreSQL:** Melhor para consultas complexas e transações ACID
- **MySQL:** Tradicionalmente mais rápido para operações simples de leitura

## Verificação
Após configurar tudo, teste a conexão:
```bash
python manage.py check
python manage.py dbshell
```

## Observações
- A estrutura dos modelos Django permanece a mesma
- O ORM do Django abstraí as diferenças entre os bancos
- Todas as funcionalidades devem continuar funcionando normalmente