# Arquitetura do backend

## Responsabilidades

`app/api/routes` contém roteadores por assunto: autenticação, alunos, servidores, rodadas, sextetos, preferências, alocação e auditoria. O prefixo `/api`, os payloads de sucesso e as permissões existentes foram preservados. `api/schemas/` agrupa entrada e saída por assunto; `api/presenters.py` monta consultas de apresentação sem expor hashes ou sessões.

`app/services` concentra as operações críticas e recebe a sessão da transação. Na autenticação, o serviço coordena transações separadas de limitação de tentativas, login e auditoria; a rota cuida do cookie HTTP. O roteador abre `SessionFactory.begin()`, chama o serviço e monta a resposta antes do commit. Uma falha na operação, na serialização antecipada ou nos constraints diferidos causa rollback. Operações administrativas simples de alunos e servidores permanecem junto de seus roteadores, sem criar camadas vazias de repositórios.

`app/domain/allocation.py` é independente de FastAPI e PostgreSQL: recebe candidatos e a ordem congelada de servidores e produz escolhas e explicações. Ele rejeita entradas inconsistentes. Não usa sorteio, nome de servidor ou ordem de iteração de conjuntos para desempatar.

`app/db/models/` separa usuários, servidores, rodadas, sextetos, preferências, alocações e auditoria, registrando tudo em uma única `Base` e `app/db/session.py` configura pool, timeouts e o relógio oficial. As migrations também incluem triggers que não aparecem integralmente nos modelos ORM. Não substituir migrations por `create_all()`.

`app/core` reúne configuração, hashing, erros de domínio, caminhos de implantação e gravação da auditoria. A autorização HTTP fica em `api/dependencies.py`; autenticação e rate limit persistente ficam em `services/auth.py`. `app/main.py` contém a fábrica `create_app()` e monta a aplicação. Middleware, handlers de erro e health/readiness têm módulos próprios. Os comandos `app.commands.users`, `app.commands.seed`, `app.commands.deploy` e `app.commands.verify_run` são pontos de entrada de operação.

## Integridade e concorrência

Os escritores críticos bloqueiam primeiro a rodada no PostgreSQL. O cadastro também bloqueia os alunos em ordem de UUID, permitindo concorrência entre rodadas sem inverter a ordem dos locks. O índice parcial `uq_student_active_sextet` é a barreira final contra participação dupla. Constraints diferidos exigem a quantidade declarada de três a seis integrantes e ranking completo no commit.

`clock_timestamp()` decide janelas após esperar pelos locks. Abertura é inclusiva; fechamento, exclusivo. A confirmação produz prioridade imutável e preferências não a alteram. Chaves de idempotência são vinculadas ao criador e não podem ser reutilizadas com conteúdo diferente.

O cálculo inteiro, suas alocações, eventos e transição para `PROCESSED` fazem parte de uma transação. Falhas fazem rollback e uma tentativa `FAILED` é registrada separadamente. Repetições devolvem a execução oficial `COMPLETED`. A migration `0004_run_history` impede alteração e exclusão de execuções finalizadas e truncamento do histórico. A reprodução com `app.commands.verify_run` confere fingerprint, versão suportada, resultados e trilhas sem escrever no banco.

O estado `PROCESSING` participa da mesma transação: ele não é um indicador de progresso público em tempo real. Os gatilhos e privilégios protegem a conta da aplicação; o proprietário/superusuário do banco continua sendo uma função operacional privilegiada.

## Integração com o frontend

O cliente deve usar cookies com `credentials: "include"`, enviar datas com fuso, manter `idempotency_key` durante uma repetição da mesma confirmação e usar `expected_version` para editar preferências. Não calcular a elegibilidade de prazo pelo relógio do navegador: usar `server_now`, `registration_open` e `preferences_open` retornados pela API.

O código de erro orienta o comportamento. Em `409`, recarregar o estado antes de reenviar dados diferentes; em `401`, solicitar login; em `503`, tentar novamente com espera limitada. Guardar `request_id` para suporte. Resultados só se tornam visíveis ao aluno depois da publicação, limitados ao seu sexteto.

As mudanças desta revisão exigem configuração explícita de `DATABASE_URL`. A auditoria recusa datas sem fuso e intervalos invertidos com `INVALID_DATE`. A abertura revalida servidores ativos. Erros precoces de tamanho e origem também têm correlação; erros de tamanho permanecem legíveis pelo frontend autorizado via CORS.

## Evolução

Adicionar uma rota ao módulo do assunto, sua entrada/saída tipada e seus testes. Regras que afetam prioridade, integrantes, capacidade ou publicação precisam constar na revisão de requisitos. Alterações de dados exigem nova migration; não reescrever migrations já aplicadas. Atualizar `docs/backend-api.md` e regenerar `docs/openapi.json` após mudar o contrato. Segredos, bancos e ambientes virtuais não pertencem ao repositório.

## Organização física e dependências

O pacote instalável está em `backend/src/app`. `config/` contém o Alembic; `database/` reúne migrations e inicialização SQL; `deploy/` contém o Dockerfile; `requirements/` reúne as versões fixadas. O [mapa do backend](../backend/README.md) descreve cada pasta e os comandos.

As camadas têm limites verificados em `tests/unit/test_architecture.py`: o domínio não importa HTTP, banco ou infraestrutura; serviços não importam a API ou FastAPI; infraestrutura e persistência não dependem das rotas ou serviços. Evitar importações circulares e manter regras de negócio fora dos roteadores. A fachada `db/models/__init__.py` registra todos os modelos sem duplicar tabelas ou metadados.

Testes PostgreSQL ficam em `tests/integration`, separados em autenticação, rodadas, sextetos, preferências, alocação, auditoria e operação. `tests/support.py` reúne helpers de cenários e `conftest.py` controla fixtures. Testes sem banco e verificações da arquitetura ficam em `tests/unit`.

Os comandos administrativos ficam exclusivamente em `app.commands`. A ferramenta de demonstração só executa seu trabalho ao chamar `main()`, permitindo importação sem criar contas. Caminhos de migrations são resolvidos centralmente em `db/migrations.py` e `core/paths.py`, inclusive fora do diretório de execução habitual.
