# Backend IF-Arbitra

## Onde fica cada coisa

```text
backend/
├── src/app/                 Código Python instalável
│   ├── main.py             Composição da aplicação FastAPI
│   ├── api/                Camada HTTP
│   │   ├── dependencies.py Sessão e permissões de acesso
│   │   ├── errors.py       Respostas padronizadas de erro
│   │   ├── middleware.py   Origem, tamanho, correlação e logs
│   │   ├── presenters.py   Dados para as respostas
│   │   ├── router.py       Registro das rotas
│   │   ├── routes/         Rotas por assunto, incluindo health/readiness
│   │   └── schemas/        Entradas e saídas por assunto
│   ├── services/           Autenticação e operações transacionais
│   ├── domain/             Algoritmo puro de alocação
│   ├── db/                 Conexões e configuração de migrations
│   │   └── models/         Modelos por assunto, com uma única Base
│   ├── core/               Configuração, criptografia, auditoria e caminhos
│   └── commands/           Operações administrativas e de desenvolvimento
├── config/alembic.ini      Configuração da ferramenta de migrations
├── database/
│   ├── migrations/         Histórico de versões e triggers
│   └── init/               Inicialização do PostgreSQL do Compose
├── deploy/Dockerfile       Construção e execução do contêiner
├── requirements/           Versões fixadas das dependências
├── tests/
│   ├── unit/               Testes sem PostgreSQL e limites entre módulos
│   ├── integration/        Cenários PostgreSQL separados por assunto
│   ├── conftest.py         Preparação/limpeza do banco descartável
│   └── support.py          Helpers de cenários compartilhados
├── .env.example            Exemplo de configuração local
└── pyproject.toml          Pacote, dependências e ferramentas
```

As pastas de modelos, contratos, serviços e testes usam os mesmos assuntos sempre que aplicável: usuários/autenticação, servidores, rodadas, sextetos, preferências, alocação e auditoria. Não há pastas genéricas `utils`, `misc` ou arquivos de operação soltos dentro de `app`.

## Comandos

Instale o pacote com `pip install -c requirements/constraints.txt -e ".[dev]"` dentro de `backend/`. Configure o PostgreSQL em `.env` a partir de `.env.example`. Antes do seed, defina `IF_ARBITRA_ROSTER_PATH` com o caminho do JSON privado ou `IF_ARBITRA_ROSTER_JSON` com seu conteúdo; o cadastro não está no Git. Em seguida:

```sh
alembic -c config/alembic.ini upgrade head
python -m app.commands.seed
python -m app.commands.users seu.login "Seu nome" --admin
uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

| Comando | Responsabilidade |
| --- | --- |
| `python -m app.commands.users` | Criar conta ou redefinir senha |
| `python -m app.commands.seed` | Carregar cadastro privado indicado por `IF_ARBITRA_ROSTER_PATH` ou `IF_ARBITRA_ROSTER_JSON`, sem sobrescrever correções ou remoções |
| `python -m app.commands.deploy` | Migrar, preparar seed e aplicar permissões de produção |
| `python -m app.commands.verify_run UUID` | Reproduzir e conferir uma execução sem escrever no banco |
| `python -m app.commands.export_openapi --check` | Conferir o contrato versionado em `docs/openapi.json` |
| `python -m app.commands.prepare_demo` | Preparar dados exclusivamente em banco de desenvolvimento terminado em `_test` |

O comando de demonstração exige `DATABASE_URL` e `BROWSER_FIXTURE_OUTPUT`, que aponta para um arquivo local fora do Git onde serão salvas credenciais temporárias. Os comandos não executam operações só por serem importados.

## Ao atualizar a cópia anterior

Reinstale o pacote editável porque o código mudou de `app/` para `src/app/`. Os antigos comandos `app.cli`, `app.seed`, `app.deploy` e `app.verify_run` agora estão em `app.commands`. Não foram deixados arquivos de compatibilidade espalhados na raiz. O endereço de inicialização HTTP permanece `app.main:app`. O contrato atual tem 28 operações HTTP e exige as migrations até `0009_group_slots`.

As migrations mudaram de pasta, mantendo identificadores e conteúdo. Use a opção `-c config/alembic.ini`. Em uma instalação não editável, distribua também `config/` e `database/` e defina `IF_ARBITRA_BACKEND_DIR` para a pasta que contém esses recursos. O Dockerfile já faz isso.

Consulte [instalação e operação](../docs/operacao.md), [arquitetura](../docs/arquitetura.md) e [contrato HTTP](../docs/backend-api.md).
