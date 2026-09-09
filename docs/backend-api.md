# IF-Arbitra — contrato HTTP do backend

Este documento descreve a API implementada no backend do IF-Arbitra. O contrato executável também está disponível no OpenAPI da aplicação.

## Acesso rápido

| Recurso | Caminho |
| --- | --- |
| API | `/api` |
| OpenAPI JSON | `/openapi.json` |
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |
| Verificação de processo | `/health` |
| Verificação de banco e migrations | `/ready` |

## Convenções

- Os corpos de requisição e resposta usam JSON.
- Identificadores são UUIDs representados como strings.
- Datas e horas usam ISO 8601/RFC 3339 com fuso horário. O backend e o banco são a autoridade temporal.
- Campos desconhecidos nos corpos de entrada são rejeitados.
- A autenticação usa o cookie `if_arbitra_session`, criado no login como `HttpOnly`.
- Clientes web devem enviar credenciais, por exemplo `credentials: "include"` no `fetch`.
- Toda mutação (`POST`, `PUT`, `PATCH` ou `DELETE`) exige que o cabeçalho `Origin` seja exatamente igual ao `FRONTEND_URL` configurado no backend. Isso também se aplica ao login.
- O tamanho máximo do corpo de uma requisição é 64 KiB.
- Todas as respostas incluem `X-Request-ID` e `Cache-Control: no-store`.
- A API aceita os papéis globais `STUDENT` e `ADMIN`.

Exemplo de chamada autenticada:

```ts
const response = await fetch(`${API_URL}/api/rounds`, {
  credentials: "include",
});
```

Exemplo de mutação:

```ts
const response = await fetch(`${API_URL}/api/sextets/${sextetId}/preferences`, {
  method: "PUT",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    staff_ids: orderedStaffIds,
    expected_version: currentVersion,
  }),
});
```

## Erros

Erros tratados usam sempre este formato:

```json
{
  "code": "PREFERENCE_VERSION_CONFLICT",
  "message": "As preferências foram alteradas em outra aba. Recarregue antes de salvar.",
  "request_id": "c50fe349-b380-4299-94e5-2c805bea9c41"
}
```

O cliente deve usar `code` para decidir o comportamento e `message` para apresentar a orientação em português. O `request_id` deve ser guardado ao reportar uma falha à administração.

| HTTP | Uso principal |
| --- | --- |
| `400` | Tamanho declarado da requisição inválido |
| `401` | Sessão ausente/expirada ou credenciais inválidas |
| `403` | Papel, liderança ou origem sem permissão |
| `404` | Recurso inexistente ou ocultado por autorização |
| `409` | Conflito de estado, concorrência, idempotência ou versão |
| `413` | Corpo maior que 64 KiB |
| `422` | Corpo, datas, composição ou ranking inválido |
| `429` | Limite de tentativas de login excedido |
| `500` | Falha interna inesperada |
| `503` | Banco indisponível, migration incorreta ou serviço ocupado |

## Resumo das rotas

| Método | Rota | Acesso | Resposta |
| --- | --- | --- | --- |
| `POST` | `/api/auth/login` | Público com `Origin` permitido | `User` |
| `GET` | `/api/auth/me` | Autenticado | `User` |
| `POST` | `/api/auth/logout` | Autenticado | Sem corpo (`204`) |
| `GET` | `/api/students` | Autenticado | `StudentSearch[]` |
| `POST` | `/api/admin/students` | Admin | `User` (`201`) |
| `GET` | `/api/staff` | Autenticado | `Staff[]` |
| `POST` | `/api/admin/staff` | Admin | `Staff` (`201`) |
| `PUT` | `/api/admin/staff/{staff_id}` | Admin | `Staff` |
| `GET` | `/api/rounds` | Autenticado | `Round[]` |
| `GET` | `/api/rounds/{round_id}` | Autenticado | `Round` |
| `POST` | `/api/admin/rounds` | Admin | `Round` (`201`) |
| `PUT` | `/api/admin/rounds/{round_id}` | Admin | `Round` |
| `POST` | `/api/admin/rounds/{round_id}/transition` | Admin | `Round` |
| `GET` | `/api/rounds/{round_id}/my-sextet` | Autenticado | `Sextet` ou `null` |
| `POST` | `/api/rounds/{round_id}/sextets` | Aluno líder | `Sextet` (`201`) |
| `GET` | `/api/sextets/{sextet_id}` | Membro ou admin | `Sextet` |
| `PUT` | `/api/sextets/{sextet_id}/preferences` | Líder do Trio A | `PreferenceSubmission` |
| `GET` | `/api/admin/rounds/{round_id}/sextets` | Admin | `SextetSummary[]` |
| `POST` | `/api/admin/rounds/{round_id}/allocate` | Admin | `AllocationRunSummary` |
| `GET` | `/api/rounds/{round_id}/results` | Autenticado | `Results` |
| `GET` | `/api/admin/runs/{run_id}` | Admin | `AllocationRunDetail` |
| `GET` | `/api/admin/audit` | Admin | `AuditPage` |
| `GET` | `/health` | Público | Estado do processo |
| `GET` | `/ready` | Público | Estado do banco/migrations |

## Autenticação

### `POST /api/auth/login`

Abre uma sessão e grava o cookie de autenticação.

Corpo:

```json
{
  "login": "20260001",
  "password": "senha-do-usuario"
}
```

Regras:

- `login`: de 2 a 160 caracteres; normalizado para minúsculas antes da busca.
- `password`: de 1 a 256 caracteres.
- Há limites persistentes por identificador e por IP em uma janela de 15 minutos.

Resposta `200`:

```json
{
  "id": "a1ce8ae8-0cbe-45cd-ac21-58e945c2a75c",
  "name": "Aluno Exemplo",
  "login": "20260001",
  "role": "STUDENT"
}
```

Erros principais: `INVALID_CREDENTIALS` (`401`), `RATE_LIMITED` (`429`) e `ORIGIN_REJECTED` (`403`).

### `GET /api/auth/me`

Retorna o usuário da sessão atual no formato `User` acima.

Erro principal: `AUTH_REQUIRED` (`401`).

### `POST /api/auth/logout`

Revoga a sessão atual, remove o cookie e responde com `204 No Content`.

Erros principais: `AUTH_REQUIRED` (`401`) e `ORIGIN_REJECTED` (`403`).

## Alunos

### `GET /api/students?q={texto}`

Pesquisa alunos ativos por nome ou login. Retorna no máximo 20 registros, ordenados por nome.

Parâmetros:

| Nome | Tipo | Regra |
| --- | --- | --- |
| `q` | string | Obrigatório, de 2 a 100 caracteres |

Resposta `200`:

```json
[
  {
    "id": "e28f74e6-a5b9-4ca8-b646-173625ff6247",
    "name": "Ana Souza",
    "login": "20260002",
    "occupied": false
  }
]
```

`occupied` informa se o aluno já pertence a um sexteto ativo, inclusive de outra rodada ainda ativa.

### `POST /api/admin/students`

Cria um aluno. Exige `ADMIN`.

Corpo:

```json
{
  "name": "Ana Souza",
  "login": "20260002",
  "password": "senha-inicial-segura"
}
```

Regras:

- `name` e `login`: de 2 a 160 caracteres.
- `password`: de 12 a 256 caracteres.
- O login é normalizado para minúsculas e deve ser único.

Resposta `201`: `User`.

Erros principais: `ADMIN_REQUIRED` (`403`) e `LOGIN_ALREADY_EXISTS` (`409`).

## Servidores institucionais

Neste contrato, “servidor” significa uma pessoa da instituição, não infraestrutura.

### `GET /api/staff`

Lista todos os servidores institucionais, inclusive inativos, ordenados por nome.

Resposta `200`:

```json
[
  {
    "id": "aed1e3bd-a9ab-409a-a347-4395bfad464b",
    "name": "Anderson Aparecido Lima da Silva",
    "active": true,
    "order": null
  }
]
```

### `POST /api/admin/staff`

Cria um servidor institucional. Exige `ADMIN`.

### `PUT /api/admin/staff/{staff_id}`

Atualiza nome e estado ativo de um servidor institucional. Exige `ADMIN`.

Corpo das duas operações:

```json
{
  "name": "Anderson Aparecido Lima da Silva",
  "active": true
}
```

`name` deve ter de 2 a 160 caracteres. `active` é opcional na criação e assume `true`.

Resposta: `Staff`. A criação usa `201`; a atualização usa `200`.

Erro específico da atualização: `STAFF_NOT_FOUND` (`404`).

## Rodadas

Estados possíveis:

```text
DRAFT -> OPEN -> PROCESSED -> PUBLISHED -> ARCHIVED
```

Transições não podem pular etapas. Depois que uma rodada é aberta, seus prazos e servidores ficam congelados. Ao arquivar, as participações deixam de contar como ativas para a exclusividade do aluno.

### Formato `Round`

```json
{
  "id": "560621c2-b96b-4131-aa65-044641958794",
  "name": "Processo 2026",
  "status": "OPEN",
  "registration_opens_at": "2026-09-01T08:00:00-03:00",
  "registration_closes_at": "2026-09-10T18:00:00-03:00",
  "preferences_open_at": "2026-09-01T08:00:00-03:00",
  "preferences_close_at": "2026-09-12T18:00:00-03:00",
  "server_now": "2026-09-05T15:30:00-03:00",
  "registration_open": true,
  "preferences_open": true,
  "can_process": false,
  "staff": [
    {
      "id": "aed1e3bd-a9ab-409a-a347-4395bfad464b",
      "name": "Anderson Aparecido Lima da Silva",
      "active": null,
      "order": 0
    }
  ],
  "registered": 8,
  "with_preferences": 6,
  "repechage": 2,
  "capacity": 14,
  "shortfall": 0
}
```

Os campos calculados permitem que a interface use o relógio e as decisões do backend:

- `server_now`: horário oficial observado pelo banco.
- `registration_open`: a confirmação de sexteto está autorizada agora.
- `preferences_open`: o envio de preferências está autorizado agora.
- `can_process`: a administração já pode executar a alocação.
- `registered`: total de sextetos confirmados.
- `with_preferences`: total com ranking válido.
- `repechage`: total sem ranking, destinado à repescagem.
- `capacity`: quantidade de servidores elegíveis.
- `shortfall`: quantidade de sextetos além da capacidade exclusiva.

### `GET /api/rounds`

Lista até 100 rodadas, da mais recente para a mais antiga. Alunos não recebem rodadas em `DRAFT`; administradores recebem todos os estados.

### `GET /api/rounds/{round_id}`

Retorna uma rodada. Uma rodada `DRAFT` é ocultada de alunos como `ROUND_NOT_FOUND` (`404`).

### `POST /api/admin/rounds`

Cria uma rodada em `DRAFT`. Exige `ADMIN`.

### `PUT /api/admin/rounds/{round_id}`

Substitui os dados configuráveis de uma rodada. Só funciona em `DRAFT` e exige `ADMIN`.

Corpo de criação/edição:

```json
{
  "name": "Processo 2026",
  "registration_opens_at": "2026-09-01T08:00:00-03:00",
  "registration_closes_at": "2026-09-10T18:00:00-03:00",
  "preferences_open_at": "2026-09-01T08:00:00-03:00",
  "preferences_close_at": "2026-09-12T18:00:00-03:00",
  "staff_ids": [
    "aed1e3bd-a9ab-409a-a347-4395bfad464b"
  ]
}
```

Regras:

- Todas as datas devem incluir fuso horário.
- `registration_opens_at < registration_closes_at <= preferences_close_at`.
- `preferences_open_at < preferences_close_at`.
- `staff_ids` deve conter de 1 a 500 UUIDs únicos de servidores ativos existentes.

Erros principais: `ROUND_NOT_FOUND` (`404`), `ROUND_FROZEN` (`409`) e `STAFF_NOT_ELIGIBLE` (`422`).

### `POST /api/admin/rounds/{round_id}/transition`

Executa uma transição de estado. Repetir uma transição já concluída retorna o estado atual sem criar outra mudança.

Corpo:

```json
{ "action": "open" }
```

Valores aceitos:

| Ação | Estado necessário | Novo estado |
| --- | --- | --- |
| `open` | `DRAFT` | `OPEN` |
| `publish` | `PROCESSED` | `PUBLISHED` |
| `archive` | `PUBLISHED` | `ARCHIVED` |

Erros principais: `ROUND_NOT_FOUND` (`404`), `INVALID_ROUND_TRANSITION` (`409`) e `ROUND_EXPIRED` (`409`).

## Sextetos

### Organização dos integrantes

O array `members` possui exatamente seis UUIDs e a posição tem significado de domínio:

| Índice | Papel |
| --- | --- |
| `0` | Líder do Trio A e líder administrativo do sexteto |
| `1` | Membro A2 |
| `2` | Membro A3 |
| `3` | Líder do Trio B |
| `4` | Membro B2 |
| `5` | Membro B3 |

### Formato `Sextet`

```json
{
  "id": "78d0723f-74c5-49b9-976f-202d35763325",
  "name": "Sexteto Aurora",
  "round_id": "560621c2-b96b-4131-aa65-044641958794",
  "leader_id": "a1ce8ae8-0cbe-45cd-ac21-58e945c2a75c",
  "registration_completed_at": "2026-09-05T18:31:24.145000Z",
  "priority_sequence": 31,
  "members": [
    {
      "slot": 0,
      "id": "a1ce8ae8-0cbe-45cd-ac21-58e945c2a75c",
      "name": "Aluno líder"
    }
  ],
  "preferences": [],
  "preference_version": 0,
  "preferences_submitted_at": null
}
```

`members` contém os seis registros; o exemplo foi abreviado. `slot` varia de `0` a `5`.

### `GET /api/rounds/{round_id}/my-sextet`

Retorna o sexteto do usuário autenticado naquela rodada ou `null` se ele não participa de um.

### `POST /api/rounds/{round_id}/sextets`

Confirma atomicamente a composição completa e estabelece a prioridade temporal. O aluno autenticado deve estar no índice `0`.

Corpo:

```json
{
  "name": "Sexteto Aurora",
  "members": [
    "a1ce8ae8-0cbe-45cd-ac21-58e945c2a75c",
    "e28f74e6-a5b9-4ca8-b646-173625ff6247",
    "18488ad5-e29b-4a0c-928a-9a1206abdd9b",
    "5e07f59f-a8bd-4826-90d2-b56c9a6331b0",
    "2ae78139-ccf8-4c15-89d5-5d8ea352b590",
    "da72d9e6-fdf8-4590-a3a3-1cb0f8d18336"
  ],
  "idempotency_key": "7f084ca3-213f-414a-b1fb-1ec230eb3045"
}
```

Regras:

- A rodada deve estar `OPEN` e o banco deve observar `registration_opens_at <= agora < registration_closes_at`.
- Os seis UUIDs devem ser distintos e pertencer a alunos ativos.
- O aluno autenticado deve ser o primeiro integrante e possuir papel `STUDENT`.
- Um aluno pode pertencer a no máximo um sexteto ativo em todo o sistema.
- `idempotency_key` deve ser gerado uma vez pelo cliente e reutilizado somente ao repetir exatamente a mesma confirmação.
- A prioridade é `(registration_completed_at, priority_sequence)`, ambos produzidos pelo backend/banco.

Erros principais: `ROUND_NOT_FOUND`, `REGISTRATION_WINDOW_CLOSED`, `NOT_SEXTET_LEADER`, `DUPLICATE_MEMBER`, `INVALID_SEXTET_COMPOSITION`, `STUDENT_ALREADY_IN_SEXTET` e `IDEMPOTENCY_CONFLICT`.

### `GET /api/sextets/{sextet_id}`

Retorna `Sextet` para qualquer integrante do grupo ou para um administrador. Para outros alunos, responde `SEXTET_NOT_FOUND` (`404`) para não revelar o grupo.

### `GET /api/admin/rounds/{round_id}/sextets`

Lista até 500 sextetos na ordem oficial de prioridade.

Resposta `200`:

```json
[
  {
    "id": "78d0723f-74c5-49b9-976f-202d35763325",
    "name": "Sexteto Aurora",
    "registration_completed_at": "2026-09-05T18:31:24.145000Z",
    "priority_sequence": 31
  }
]
```

## Preferências

### `PUT /api/sextets/{sextet_id}/preferences`

Cria ou substitui o ranking completo. Somente o líder do Trio A pode executar esta operação.

Corpo:

```json
{
  "staff_ids": [
    "aed1e3bd-a9ab-409a-a347-4395bfad464b",
    "d32d5532-2da6-4620-b5af-27a0ceda88a5"
  ],
  "expected_version": 0
}
```

Regras:

- O primeiro UUID é a maior preferência.
- A lista deve ser uma permutação completa dos servidores elegíveis da rodada: todos exatamente uma vez, sem itens extras.
- A rodada deve estar `OPEN` e o banco deve observar `preferences_open_at <= agora < preferences_close_at`.
- Na primeira gravação, envie `expected_version: 0`.
- Em uma edição, envie o `preference_version` mais recente retornado por `Sextet`.
- Uma repetição idêntica da última requisição aceita é idempotente.
- Um rascunho antigo com conteúdo diferente é rejeitado para evitar sobrescrita entre abas.
- O horário do envio não altera a prioridade estabelecida na confirmação do sexteto.

Resposta `200`:

```json
{
  "version": 1,
  "submitted_at": "2026-09-05T18:45:10.288000Z"
}
```

Erros principais: `SEXTET_NOT_FOUND` (`404`), `NOT_SEXTET_LEADER` (`403`), `PREFERENCE_WINDOW_CLOSED` (`409`), `INVALID_PREFERENCE_RANKING` (`422`) e `PREFERENCE_VERSION_CONFLICT` (`409`).

## Alocação e resultados

### `POST /api/admin/rounds/{round_id}/allocate`

Executa a alocação oficial. Exige `ADMIN`.

Regras:

- A rodada deve estar `OPEN`.
- O banco deve observar `agora >= preferences_close_at`.
- A operação é serializada no PostgreSQL.
- Se já existe uma execução concluída, a rota retorna essa execução e não recalcula o resultado.
- Sextetos com ranking completo participam primeiro, em ordem de prioridade.
- Sextetos sem ranking participam depois, como `REPECHAGE`, também em ordem de prioridade.
- Cada sexteto recebe a primeira opção ainda disponível.
- Um servidor pode ser alocado a no máximo um sexteto na rodada.
- Se a capacidade acabar, o sexteto recebe `UNALLOCATED`.
- Ao concluir, a rodada passa para `PROCESSED`.

Resposta `200`:

```json
{
  "id": "2cc69d80-aecb-4038-a923-b5bfbec1b2d7",
  "status": "COMPLETED",
  "input_fingerprint": "55d40c6c9d97c93d33741f82fc17515ac969294a85c70c16137d0783d3c38518"
}
```

Erros principais: `ROUND_NOT_FOUND` (`404`) e `ALLOCATION_NOT_READY` (`409`).

### `GET /api/rounds/{round_id}/results`

Retorna os resultados de uma rodada.

Visibilidade:

- Antes de `PUBLISHED`, alunos recebem `{ "published": false, "allocations": [] }`.
- Depois de `PUBLISHED` ou em `ARCHIVED`, alunos recebem somente a alocação do próprio sexteto.
- Administradores podem consultar todos os resultados antes da publicação.
- A trilha de um aluno não revela qual sexteto ocupou uma opção anterior; `unavailable` é restrito à administração.

Resposta `200`:

```json
{
  "published": true,
  "allocations": [
    {
      "id": "57e18454-d759-466e-a0e6-dc92ab5bbeb1",
      "sextet_id": "78d0723f-74c5-49b9-976f-202d35763325",
      "sextet_name": "Sexteto Aurora",
      "staff_name": "Anderson Aparecido Lima da Silva",
      "staff_id": "aed1e3bd-a9ab-409a-a347-4395bfad464b",
      "run_id": "2cc69d80-aecb-4038-a923-b5bfbec1b2d7",
      "status": "ALLOCATED",
      "kind": "MAIN",
      "preference_position": 1,
      "trace": {
        "processing_order": 1,
        "registration_completed_at": "2026-09-05T18:31:24.145000Z",
        "priority_sequence": 31,
        "ranking": ["aed1e3bd-a9ab-409a-a347-4395bfad464b"],
        "fallback_order": [],
        "unavailable": null,
        "chosen": "aed1e3bd-a9ab-409a-a347-4395bfad464b",
        "reason": "FIRST_AVAILABLE"
      }
    }
  ]
}
```

Valores relevantes:

| Campo | Valores |
| --- | --- |
| `status` | `ALLOCATED`, `UNALLOCATED` |
| `kind` | `MAIN`, `REPECHAGE` |
| `trace.reason` | `FIRST_AVAILABLE`, `CAPACITY_EXHAUSTED` |

Em uma alocação `UNALLOCATED`, `staff_id`, `staff_name`, `preference_position` e `trace.chosen` são `null`.

### `GET /api/admin/runs/{run_id}`

Retorna a execução imutável usada para auditoria. Exige `ADMIN`.

Resposta `200`:

```json
{
  "id": "2cc69d80-aecb-4038-a923-b5bfbec1b2d7",
  "status": "COMPLETED",
  "algorithm_version": "serial-priority-v1",
  "input_fingerprint": "55d40c6c9d97c93d33741f82fc17515ac969294a85c70c16137d0783d3c38518",
  "snapshot": {},
  "started_at": "2026-09-12T21:00:02.102000Z",
  "finished_at": "2026-09-12T21:00:02.145000Z"
}
```

`snapshot` contém a rodada, a ordem de servidores, os nomes congelados e a ordem/prioridade/ranking dos sextetos usados na execução.

Erro específico: `RUN_NOT_FOUND` (`404`).

## Auditoria

### `GET /api/admin/audit`

Lista eventos em ordem decrescente de ID, com até 50 itens por página. Exige `ADMIN`.

Filtros opcionais:

| Parâmetro | Tipo | Observação |
| --- | --- | --- |
| `event` | string | Tipo exato do evento, até 80 caracteres |
| `entity_type` | string | Tipo exato da entidade, até 40 caracteres |
| `entity` | string | ID textual exato da entidade, até 80 caracteres |
| `actor` | UUID | Usuário responsável |
| `request_id` | UUID | Correlação de uma requisição |
| `before_id` | inteiro positivo | Cursor para a página seguinte |
| `since` | datetime ISO 8601 | Limite inicial inclusivo |
| `until` | datetime ISO 8601 | Limite final inclusivo |

Paginação:

1. Faça a primeira chamada sem `before_id`.
2. Se `next_cursor` não for `null`, faça a próxima chamada com `before_id={next_cursor}`.
3. Repita até `next_cursor` ser `null`.

Resposta `200`:

```json
{
  "next_cursor": 150,
  "events": [
    {
      "id": 201,
      "event_type": "PREFERENCE_SUBMITTED",
      "occurred_at": "2026-09-05T18:45:10.288000Z",
      "actor_name": "Aluno líder",
      "actor_user_id": "a1ce8ae8-0cbe-45cd-ac21-58e945c2a75c",
      "entity_type": "SEXTET",
      "entity_id": "78d0723f-74c5-49b9-976f-202d35763325",
      "request_id": "c50fe349-b380-4299-94e5-2c805bea9c41",
      "payload": {},
      "previous_state": {
        "ranking": [],
        "version": 0
      },
      "resulting_state": {
        "ranking": ["aed1e3bd-a9ab-409a-a347-4395bfad464b"],
        "version": 1
      }
    }
  ]
}
```

Eventos conhecidos:

```text
AUTH_LOGIN_SUCCESS
AUTH_LOGIN_FAILED
AUTH_LOGOUT
SEXTET_CREATION_ATTEMPT
SEXTET_CREATED
PREFERENCE_SUBMISSION_ATTEMPT
PREFERENCE_SUBMITTED
PREFERENCE_UPDATED
OPERATION_REJECTED
ALLOCATION_STARTED
ALLOCATION_GROUP_PROCESSED
ALLOCATION_FINISHED
ALLOCATION_FAILED
ADMIN_ACTION
```

Tipos de entidade conhecidos:

```text
USER
INSTITUTIONAL_STAFF
ALLOCATION_ROUND
SEXTET
ALLOCATION_RUN
```

Erro específico: `INVALID_DATE` (`422`).

## Operação

### `GET /health`

Informa que o processo HTTP está vivo. Não consulta o banco.

Resposta `200`:

```json
{ "status": "alive" }
```

### `GET /ready`

Confere a conexão com PostgreSQL e exige a migration `0003_audit_context` aplicada.

Resposta pronta (`200`):

```json
{ "status": "ready" }
```

Resposta indisponível (`503`):

```json
{ "status": "not_ready" }
```

## Observações para integração

- Trate `server_now`, `registration_open`, `preferences_open` e `can_process` como autoridade para habilitar ações; uma contagem regressiva no navegador é apenas informativa.
- Gere e preserve uma `idempotency_key` por tentativa lógica de confirmação de sexteto. Reenvios de rede devem reutilizar a mesma chave e o mesmo corpo.
- Após salvar preferências, atualize a versão local com `version`. Antes de editar em outra tela, recarregue o sexteto para obter `preference_version`.
- Não derive a prioridade do horário exibido. Use `registration_completed_at` e `priority_sequence` retornados pelo backend.
- Diferencie “sem publicação” de “sem alocação” pelos campos `published` e `status`.
- Como a sessão está em cookie, configure o cliente HTTP para enviar credenciais em todas as chamadas autenticadas.
- Em desenvolvimento, ajuste `FRONTEND_URL` no backend para a origem exata usada pelo cliente, incluindo esquema e porta.

## Fonte executável do contrato

O arquivo `/openapi.json` é gerado pelos modelos e roteadores da aplicação. Use-o para gerar tipos ou clientes, mantendo este documento como referência das regras de negócio e de autorização que acompanham cada rota.
