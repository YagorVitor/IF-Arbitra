# Instalação e operação

## Desenvolvimento local sem Docker

Requisitos: Python 3.11 ou superior e PostgreSQL. A verificação desta revisão utiliza Python 3.12 e PostgreSQL 18; SQLite não substitui os testes de integridade.

No PowerShell, dentro da raiz do projeto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c backend/requirements/constraints.txt -e "./backend[dev]"
Copy-Item backend/.env.example backend/.env
```

Configure `backend/.env` com a conexão real, incluindo usuário, senha e banco. Crie `arbitra` e `arbitra_test` no PostgreSQL local. O banco com sufixo `_test` é descartável: a suíte recria seu schema em cada cenário. Não use a conexão do banco operacional em `TEST_DATABASE_URL`.

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m alembic -c config/alembic.ini upgrade head
..\.venv\Scripts\python.exe -m app.commands.seed
..\.venv\Scripts\python.exe -m app.commands.users seu.login "Seu nome" --admin
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --no-proxy-headers
```

`--reload` é somente para desenvolvimento. A senha administrativa é lida interativamente, com mínimo de 12 caracteres. Para recuperar uma conta após verificar a identidade por canal institucional, use `python -m app.commands.users seu.login --reset-password`; as sessões anteriores são revogadas. O seed preserva renomeações e ativações existentes dos 14 UUIDs.

## Configuração

| Variável | Uso |
| --- | --- |
| `DATABASE_URL` | Obrigatória, `postgresql+psycopg://...`; sem fallback embutido |
| `ENVIRONMENT` | `development`, `test` ou `production` |
| `FRONTEND_URL` | Uma origem exata, sem caminho; padrão local `http://localhost:5173` |
| `COOKIE_SECURE` | `true` em produção, com HTTPS |
| `COOKIE_SAMESITE` | `lax`, `strict` ou `none`; `none` exige cookie seguro |
| `SESSION_HOURS` | De 1 a 168; padrão 8 |
| `POOL_SIZE`, `POOL_OVERFLOW` | Por worker; padrões 5 e 5 |
| `TEST_DATABASE_URL` | Exclusivamente banco descartável terminado em `_test` |
| `IF_ARBITRA_BACKEND_DIR` | Diretório dos recursos `config/` e `database/`; definido automaticamente no Docker |
| `RUNTIME_DATABASE_ROLE` | Conta sem privilégios administrativos usada por `app.commands.deploy` |

Dimensionar conexões como `workers × (POOL_SIZE + POOL_OVERFLOW)`, mais migração, manutenção e monitoramento. Há espera limitada no pool, conexão, locks e consultas. Falhas operacionais retornam `SERVICE_BUSY`/503 sem expor SQL. O `.env` é relativo ao diretório de execução; inicie o processo em `backend/` ou injete as variáveis pelo gerenciador de serviços.

## Testes e contrato

Na raiz, usando um PostgreSQL dedicado:

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://arbitra:local-only@127.0.0.1:5432/arbitra_test'
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m ruff format --check backend
.\.venv\Scripts\python.exe -m pytest backend/tests -q -s
$env:DATABASE_URL = $env:TEST_DATABASE_URL
.\.venv\Scripts\python.exe -m app.commands.export_openapi --check
```

Sem `TEST_DATABASE_URL`, somente os testes independentes do banco são executados e os de integração são explicitamente ignorados. Isso não é evidência suficiente para aceitar uma alteração de transação. O cenário `test_burst_50_requests` requer 1 sucesso, 49 conflitos e nenhum erro interno. O cenário entre rodadas verifica exclusividade global, não apenas o lock de uma rodada.

Para regenerar o arquivo de contrato, execute `python -m app.commands.export_openapi` com `DATABASE_URL` configurada. A exportação carrega metadados da API sem consultar o banco.

## Atualização de uma instalação existente

1. Fazer backup e verificar que as credenciais de migração e execução estão separadas.
2. Instalar o código/dependências desta revisão; manter o `.env` do ambiente.
3. Executar `alembic -c config/alembic.ini upgrade head` em `backend/`. A nova migration é `0004_run_history`; ela adiciona proteções ao histórico, preservando registros existentes.
4. Executar o seed idempotente se necessário e reiniciar os workers.
5. Conferir `/ready` e um login com o domínio real do frontend.

Não é necessário apagar o banco ou recriar grupos. O retorno a `0003_audit_context` remove a proteção adicional das execuções; deve ser uma ação operacional planejada, e não o procedimento normal de atualização.

## Produção

A composição Docker fornecida é de desenvolvimento. Em produção, use PostgreSQL gerenciado, HTTPS, origem real do frontend e segredos externos ao Git. Crie uma conta proprietária para migrations e outra de execução sem `SUPERUSER`, `CREATEDB`, `CREATEROLE`, herança de conta proprietária ou privilégios concedidos por outros grupos.

No passo de release, configure `DATABASE_URL` com a conta proprietária e `RUNTIME_DATABASE_ROLE` com a conta de execução e rode `python -m app.commands.deploy`. O comando aplica migrations, seed e permissões de execução. Depois, inicie a aplicação com a conexão da conta de execução. Nenhuma senha de produção é fornecida no código.

O Dockerfile usa dois workers, usuário sem root e `--no-proxy-headers`. Se houver proxy reverso, só ative confiança em cabeçalhos encaminhados para IPs de proxies conhecidos e impeça acesso direto ao backend. Sem isso, o rate limit por IP vê o endereço do proxy. Restrinja também o tamanho e tempo do corpo no proxy para evitar conexões lentas; a aplicação verifica os bytes recebidos até 64 KiB.

`/health` indica processo vivo. `/ready` exige que o conjunto de versões aplicadas coincida com os heads das migrations distribuídas. Configuração inválida impede a inicialização. As métricas do teste local não substituem carga em staging com o provedor, proxy e limites reais.

## Backup e restauração

Responsabilidade da operação: definir retenção, RPO (perda de dados tolerável), RTO (tempo de recuperação) e acesso aos backups com dados pessoais. Usar snapshots/PITR do provedor, complementados por exportação quando necessário. Não guardar dumps no Git. Para ferramentas nativas, a conexão é PostgreSQL, sem o sufixo `+psycopg` usado pelo SQLAlchemy; preferir serviço/arquivo de senha protegido a senha na linha de comando.

Exemplo com serviços PostgreSQL configurados para a origem e um banco de restauração vazio e isolado:

```sh
pg_dump --dbname="service=arbitra_backup" --format=custom --file=arbitra-backup.dump
pg_restore --dbname="service=arbitra_restore_test" --no-owner --no-privileges --exit-on-error arbitra-backup.dump
```

O serviço `arbitra_restore_test` deve apontar explicitamente para o destino isolado; esses comandos não criam o banco. Restaurar como proprietário e reaplicar as permissões de execução pelo passo de release. Conferir versão de migrations, contagens de todas as tabelas, presença dos triggers e login em ambiente isolado. Nunca restaurar sobre o banco operacional para testar um backup.

Para cada execução concluída restaurada:

```sh
python -m app.commands.verify_run UUID_DA_EXECUCAO
```

O comando compara fingerprint, entradas, algoritmo, alocações e trilhas sem recalcular ou substituir o resultado oficial no banco. Registre data, duração, tamanho do dump, responsável e resultado da restauração. A entrega local inclui um ensaio em banco descartável; backup gerenciado, retenção e recuperação de produção precisam ser configurados no provedor escolhido.

## Mudança para a estrutura src

Ao atualizar a organização anterior, reinstale o pacote editável com `pip install -c backend/requirements/constraints.txt -e "./backend[dev]"` na raiz. O servidor continua em `app.main:app`. Os comandos operacionais foram agrupados em `app.commands`, e o Alembic agora exige `-c config/alembic.ini` ao executar dentro de `backend/`.

Para instalações não editáveis (wheel), distribua também `backend/config` e `backend/database` e configure `IF_ARBITRA_BACKEND_DIR`. A configuração da aplicação em `.env` continua relativa ao diretório de execução. O exportador aceita `--output caminho/openapi.json` quando não houver a pasta de documentação do repositório.
