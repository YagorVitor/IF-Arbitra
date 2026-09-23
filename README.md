# IF-Arbitra

Backend para formação de sextetos, registro de prioridade temporal, preferências por servidores institucionais e alocação determinística. Python 3.11+, FastAPI, SQLAlchemy e PostgreSQL. A implementação do frontend fica com outra equipe.

## Início com Docker

Na raiz do repositório, com Docker Compose disponível:

```sh
docker compose -f compose.backend.yaml up --build -d
docker compose -f compose.backend.yaml exec backend python -m app.commands.users seu.login "Seu nome" --admin
```

A senha é solicitada no terminal, sem credencial administrativa padrão. A composição é para desenvolvimento: banco, migrations e seed são preparados automaticamente. API em `http://localhost:8000`, documentação interativa em `http://localhost:8000/docs` e prontidão em `http://localhost:8000/ready`.

Para rodar sem Docker, siga [instalação local e operação](docs/operacao.md). `DATABASE_URL` é obrigatória; copie `backend/.env.example` para `backend/.env` e ajuste a conexão com um PostgreSQL existente.

## Organização

```text
backend/
  src/app/          # Código: API, serviços, domínio, modelos e comandos
  config/           # Configuração de migrations
  database/         # Migrations e inicialização SQL
  deploy/           # Dockerfile
  requirements/     # Versões fixadas de dependências
  tests/
    unit/           # Testes independentes do banco e regras de arquitetura
    integration/    # Testes PostgreSQL separados por assunto
  README.md         # Mapa detalhado e comandos do backend
  pyproject.toml    # Pacote e ferramentas
docs/               # Requisitos, arquitetura, operação e contrato do frontend
```

Veja o [mapa completo do backend](backend/README.md), incluindo os novos comandos em `app.commands`.


## Documentação

- [Revisão dos requisitos e decisões pendentes](docs/requisitos-revisados.md)
- [Contrato para a equipe frontend](docs/backend-api.md)
- [Arquitetura e regras de contribuição](docs/arquitetura.md)
- [Operação e verificação](docs/operacao.md)

## Regras atuais

Cada sexteto tem seis alunos; o integrante da posição 0 é o líder administrativo. Um aluno participa de no máximo um sexteto ativo, inclusive entre rodadas. A prioridade usa horário do banco e sequência imutável. Rankings completos são processados antes da repescagem; cada servidor recebe até um sexteto por rodada e excedentes ficam `UNALLOCATED`. A publicação é administrativa e separada do cálculo.

Alteração/cancelamento de sextetos, capacidade maior que um e SSO dependem das decisões institucionais registradas na revisão. Nenhuma dessas políticas foi presumida nesta entrega.
