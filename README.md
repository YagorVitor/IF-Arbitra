# IF-Arbitra

Aplicação para formação de grupos com seis integrantes obrigatórios e um sétimo opcional, registro de prioridade temporal, preferências por servidores institucionais e alocação determinística. O backend usa Python 3.11+, FastAPI, SQLAlchemy e PostgreSQL. O frontend React/Vite está em `frontend/` e deve consumir o contrato atual da API.

## Início com Docker

Na raiz do repositório, com Docker Compose disponível, coloque o cadastro privado em
`backend/src/app/data/initial_roster.json` antes de iniciar. O arquivo contém os 83 alunos e 14 servidores iniciais e não é versionado nem incluído na imagem Docker.

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
  deploy/           # Roteiros de implantação
  requirements/     # Versões fixadas de dependências
  tests/
    unit/           # Testes independentes do banco e regras de arquitetura
    integration/    # Testes PostgreSQL separados por assunto
  README.md         # Mapa detalhado e comandos do backend
  pyproject.toml    # Pacote e ferramentas
docs/               # Requisitos, arquitetura, operação e contrato do frontend
frontend/           # Aplicação React/Vite
Dockerfile          # Imagem do backend; detectada pelo Railway na raiz
```

Veja o [mapa completo do backend](backend/README.md), incluindo os novos comandos em `app.commands`.

## Railway

Conecte o repositório pela raiz (`/`). O `Dockerfile` da raiz constrói apenas o backend. No serviço da API, configure `DATABASE_URL` como referência `${{Postgres.DATABASE_URL}}`. Em **Settings → Deploy**, configure o comando anterior à implantação como `python -m alembic -c config/alembic.ini upgrade head` e a verificação HTTP como `/ready`. Serviços novos do Railway não aplicam automaticamente as opções do `railway.json` legado; confira essas duas opções no painel. O endpoint `/ready` só retorna `ready` depois que o banco está acessível e as migrations foram aplicadas.

Antes de usar com alunos, configure também HTTPS, `FRONTEND_URL`, `COOKIE_SECURE=true` e SMTP; veja [operação](docs/operacao.md). O cadastro privado não está no Git nem na imagem e precisa ser fornecido separadamente.


## Documentação

- [Revisão dos requisitos e decisões pendentes](docs/requisitos-revisados.md)
- [Contrato para a equipe frontend](docs/backend-api.md)
- [Arquitetura e regras de contribuição](docs/arquitetura.md)
- [Operação e verificação](docs/operacao.md)

## Regras atuais

O administrador pode adicionar ou remover alunos e servidores do cadastro inicial. Quando aciona o disparo de credenciais, cada aluno pendente recebe por e-mail seu login (o próprio e-mail) e uma senha individual de oito caracteres. A rodada deve ser aberta depois da conferência das entregas.

Nas novas rodadas (`GROUPS`), o capitão é o aluno autenticado que cadastra o grupo e ocupa a posição 0 entre os seis integrantes obrigatórios. O sétimo integrante é opcional. Cada rodada admite até oito grupos de sete e três grupos de seis, totalizando 11 grupos e 74 alunos. A validação das quotas usa o bloqueio da rodada, inclusive em confirmações simultâneas.

Um aluno participa de no máximo um grupo ativo, inclusive entre rodadas. A prioridade usa horário do banco e sequência imutável. A alocação avalia a primeira preferência de todos antes da segunda e assim por diante; a confirmação desempata as disputas. Grupos sem ranking entram na repescagem. Cada servidor recebe um grupo. O administrador publica os resultados e pode ajustar as atribuições pelo painel, com justificativa, auditoria e proteção contra sobrescrever outra revisão. Rodadas históricas mantêm seu formato e cálculo originais.

A lista de servidores vigente em 01/10/2026 é Anderson, Carina, Carol Barra, Dione, Guilherme, Jurandyr, Mauro, Raphael Zambon, Renata, Rita e Rosana. Os cadastros antigos que não constam nesta lista ficam inativos para novas rodadas; as referências históricas são preservadas. Servidores podem ser cadastrados sem e-mail quando essa informação ainda não foi fornecida.

Alteração/cancelamento de sextetos, capacidade maior que um e SSO dependem das decisões institucionais registradas na revisão. Nenhuma dessas políticas foi presumida nesta entrega.


### Acesso dos capitães

Somente a administração e alunos identificados como capitães podem entrar. Os demais alunos constam na lista de integrantes, mesmo sem credenciais, e não podem abrir sessões. Capitães não aparecem na busca de integrantes e a API rejeita sua inclusão no grupo de outro capitão. Os grupos continuam com seis integrantes obrigatórios, incluindo o capitão, e um sétimo opcional.

Em **Cadastros**, marque o capitão ao criar um aluno ou use **Definir capitão** num cadastro existente. Apenas capitães podem receber credenciais. A alteração dessa função invalida senhas e sessões anteriores e exige gerar um novo acesso. Não é permitida a alteração da função durante participação em grupo ativo.

A migration `0013_captain_access` deixa alunos existentes como integrantes e encerra suas sessões. A administração deve identificar os capitães antes de entregar seus acessos. O cadastro administrativo e o histórico das rodadas são preservados.
