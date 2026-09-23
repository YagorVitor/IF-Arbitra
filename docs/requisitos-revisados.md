# IF-Arbitra - revisão dos requisitos do backend

## Base examinada

Revisão do documento `IF-Arbitra-Levantamento-de-Requisitos.pdf`, baseline 1.0 de 09/09/2026, comparada ao ZIP e ao projeto local `C:\Users\yagor\Downloads\IF-Arbitra`. A pasta e o ZIP tinham conteúdo idêntico, sem alterações locais, no commit `a90d4b6` do repositório `YagorVitor/IF-Arbitra`. O acesso ao repositório foi confirmado pela integração GitHub.

O PDF é uma baseline para validação institucional. Seus rótulos “Implementado” foram tratados como afirmações a verificar no código e nos testes, não como comprovação automática de atendimento nem autorização para decidir políticas ainda indefinidas. Esta entrega cobre o backend e a documentação para integração; não implementa frontend.

## Resultado da revisão

O fluxo essencial já existia: autenticação local, cadastros, rodadas, sextetos, preferências versionadas, alocação, repescagem, publicação e auditoria. Não faltava um novo módulo inteiro desse fluxo. As lacunas estavam na organização, em controles de borda, em evidência de operação e na cobertura de alguns cenários. Foram feitas as seguintes correções:

| Lacuna observada | Correção | Requisitos relacionados |
| --- | --- | --- |
| Rotas concentradas em `api.py`; serviços e infraestrutura pouco separados | Pacotes `api/routes`, `services`, `domain`, `db` e `core`; administração de rodadas em serviço transacional | RNF-015 |
| Limite de corpo dependia apenas de `Content-Length` | Contagem dos bytes efetivos, incluindo transferência sem tamanho declarado | RNF-004, RNF-006; seção 07 |
| Falhas precoces de tamanho não passavam pelo CORS interno | Envelope, correlação e CORS legíveis pela origem autorizada também nas rejeições precoces | RNF-009, RNF-014 |
| Esgotamento do pool não tinha tratamento específico | HTTP 503 `SERVICE_BUSY`; timeout de conexão explícito | RNF-008, RNF-010 |
| URL de banco possuía credencial local implícita | `DATABASE_URL` obrigatória, com exemplo e instruções de configuração | RNF-012 |
| Auditoria aceitava datas sem fuso e intervalo invertido | Rejeição `INVALID_DATE`/422, preservando o código de erro do contrato | RF-037, RNF-014 |
| Edição de rodada não registrava servidores anteriores | Auditoria com `staff_ids` antes e depois | RF-008, RF-036, RNF-007 |
| Servidor podia ser inativado entre a configuração e a abertura | Revalidação de elegibilidade sob lock ao abrir a rodada | RF-007, RF-009 |
| Busca não escapava barra invertida antes dos curingas SQL | Busca literal de barra, `%` e `_` | RF-012 |
| Concorrência entre rodadas precisava de cobertura própria | Lock dos alunos em ordem estável e teste de exclusividade entre rodadas | RF-016, RNF-002 |
| Contadores de login faziam limpeza global dentro do caminho crítico | Incremento/reset atômico por chave; auditoria de falha após liberar a transação de login | RF-003, RNF-002 |
| Snapshot/fingerprint de execução finalizada não tinham proteção própria | Migration `0004_run_history` protege finalização e histórico; verificador de reprodução somente leitura | RF-035, RNF-007 |
| Readiness fixava uma revisão literal no código | Comparação das versões aplicadas com os heads distribuídos | RF-038 |
| Erros HTTP de recurso/método podiam sair do envelope | Tratamento padronizado de 404/405 e documentação dos erros globais no OpenAPI | RNF-014 |
| README não orientava instalação/manutenção | README, arquitetura, operação, revisão rastreável e contrato OpenAPI exportado/verificado no CI | RNF-013, RNF-014, RNF-015 |
| Backup/restauração dependiam de procedimento externo não documentado | Runbook e ensaio de dump/restauração com comparação e reprodução do resultado | RNF-016, parcialmente dependente do provedor |

Não foram alterados a ordem de prioridade, os papéis no sexteto, as janelas semiabertas, a regra de um sexteto por servidor, a repescagem ou a publicação administrativa.

## Rastreabilidade funcional

| Requisitos | Situação nesta entrega | Evidência principal |
| --- | --- | --- |
| RF-001 a RF-003 | Implementados; autenticação, sessão e limite persistente verificados | `test_auth_csrf_and_privacy`, `test_login_limit_resets_at_deadline_and_survives_new_clients` |
| RF-004 a RF-006 | Cadastro/gestão preservados; validação administrativa e seed verificados | `api/routes/students.py`, `api/routes/staff.py`, `test_seed_idempotent_and_names_preserved`, `test_round_lifecycle_and_staff_before_after` |
| RF-007 a RF-011 | Ciclo e apresentação preservados; auditoria e elegibilidade corrigidas | `services/rounds.py`, `api/presenters.py`, teste de ciclo de vida |
| RF-012 a RF-019 | Implementados; composição, autoridade, atomicidade e concorrência verificados | Testes de composição, prazo, busca e concorrência |
| RF-020 e RF-021 | Não implementados: política de alteração/cancelamento não definida | Decisões D-03 e D-04 abaixo |
| RF-022 a RF-027 | Implementados; ranking, versão, prazo e prioridade verificados | `test_ranking_validation_version_deadline_and_priority`, `test_ranking_db_constraint_rejects_partial_submission` |
| RF-028 a RF-035 | Implementados sob capacidade atual; integridade histórica ampliada | Testes do algoritmo, alocação concorrente, rollback, publicação, migration e `app.commands.verify_run` |
| RF-036 e RF-037 | Implementados; filtros, cursor, datas e estados antes/depois verificados | Testes de auditoria e `core/audit.py` |
| RF-038 | Implementado; banco indisponível e revisão incorreta verificados | Testes de liveness/readiness |

## Critérios de aceite

| Critério | Verificação |
| --- | --- |
| CA-01, CA-02, CA-04 | `test_composition_authority_idempotency_and_constraints`; rejeição de grupo incompleto com rollback |
| CA-03 | `test_concurrent_student_overlap`, `test_different_rounds_still_enforce_student_exclusivity`, `test_burst_50_requests` |
| CA-05 | Liderança da confirmação no serviço; teste de recusa do líder do Trio B ao enviar preferências |
| CA-06, CA-07 | Ranking inválido, versão obsoleta e constraint diferido do banco |
| CA-08 | Fechamento exato de cadastro e preferências, com relógio do banco isolado nos testes de fronteira |
| CA-09, CA-10, CA-11, CA-12 | Algoritmo, permutações da entrada, primeira opção livre, repescagem e excesso de capacidade |
| CA-13, CA-14, CA-15 | Publicação administrativa, consulta limitada, trilha de indisponibilidades e reprodução da execução |
| CA-16 | `/health` vivo com banco indisponível; `/ready` 503 para banco/revisão inválidos |

## Evidências executadas

- **59 testes aprovados**, sem testes ignorados, em PostgreSQL 18.6 real e Python 3.12. Os testes usam uma base descartável e migrations completas. A execução final da suíte durou aproximadamente 12 segundos.
- **50 confirmações simultâneas:** 1 sucesso, 49 conflitos esperados, zero erros internos; seis vínculos persistidos. Nessa execução local: mediana 631 ms, p95 913 ms e máximo 937 ms. Não são metas de latência garantidas em produção.
- Testes entre rodadas, ranking parcial no banco, restrições de histórico, rollback de alocação, arquivamento e liberação de participantes aprovados.
- Migration nova aplicada em banco vazio e sequência `0004 → 0003 → head` verificada mantendo dados existentes.
- Fluxo adicional com login, criação/abertura de rodada, sexteto, ranking, fechamento pelo relógio real, alocação, publicação e resultado do aluno executado para o ensaio de backup.
- Dump PostgreSQL restaurado em outro banco descartável; contagens de todas as tabelas iguais, head e triggers presentes, fingerprint e alocação reproduzidos pelo verificador.
- Ruff e consistência do OpenAPI verificados. Duas advertências de depreciação vieram das dependências de teste Starlette/httpx/AnyIO; não representam falhas da suíte.

Esses testes de concorrência usam requisições simultâneas via cliente ASGI e transações PostgreSQL independentes. Não equivalem a ensaio distribuído com múltiplas máquinas e o proxy de produção. A validação de staging continua necessária.

## Decisões institucionais pendentes

| Decisão | Regra mantida | O que precisa ser definido |
| --- | --- | --- |
| D-01 - capacidade | Um sexteto por servidor por rodada; excesso `UNALLOCATED` | Confirmar exclusividade ou aprovar capacidade múltipla |
| D-02 - participantes | 14 servidores permitem 14 sextetos, total de 84 alunos | Número real de participantes e procedimento para excedentes |
| D-03 - alteração | Composição e prioridade imutáveis | Prazo, autorização, nova prioridade e efeitos sobre ranking/alocação |
| D-04 - cancelamento | Sem cancelamento; arquivamento libera todos os membros da rodada | Quem pode cancelar, quando e como preservar histórico |
| D-05 - identidade | Login local, senha Argon2 e sessão em cookie | Provedor e contrato de SSO, se houver |
| D-06 - publicação | Ato administrativo explícito após processamento | Responsável e procedimento institucional |

Essas pendências são requisitos de negócio ainda indefinidos, não funcionalidades silenciosamente consideradas concluídas. Também seguem externos à aplicação: contratação/configuração do banco gerenciado, retenção/PITR, metas de recuperação, domínios, HTTPS e confiança no proxy. O procedimento de backup local está verificado; a infraestrutura de produção não foi implantada por esta revisão.

## Entrega para a equipe frontend

Consultar `docs/backend-api.md` e `docs/openapi.json`. O frontend deve implementar experiência e apresentação consumindo o contrato atual; validação de papel, janelas, exclusividade, prioridade e publicação continua no backend. Nenhum token de sessão deve ser lido por JavaScript. Para atualização de instalação existente, aplicar a migration nova e fornecer `DATABASE_URL` explicitamente, conforme `docs/operacao.md`.

## Revisão posterior: organização e modularização

A pedido do responsável pelo projeto, o backend foi reorganizado novamente para separar código, configuração, recursos de banco, implantação, dependências e testes. O código instalável está em `backend/src/app`; comandos administrativos ficam em `app.commands`. Modelos e contratos HTTP agora são módulos por assunto; a autenticação transacional, as dependências de autorização HTTP, o middleware, os handlers de erro e as sondas têm responsabilidades separadas. O `main.py` concentra apenas a montagem da aplicação.

Os 59 testes existentes passaram após essa mudança, incluindo a concorrência de 50 confirmações (1 sucesso e 49 conflitos). Outros 6 testes passaram para validar dependências entre camadas e resolução dos recursos de migrations: total de **65 casos aprovados**. O OpenAPI permaneceu exatamente igual ao contrato anterior. O pacote wheel foi construído e instalado separadamente, e seus 59 módulos foram importados sem executar comandos administrativos. Os recursos de migrations foram localizados corretamente na instalação desse pacote.

Não houve alteração de regras de negócio nem nova migration nesta reorganização. As versões e os arquivos existentes de migration foram preservados. Dockerfile, Compose, CI e instruções foram atualizados; o Docker não está disponível nesta máquina, portanto o contêiner não foi executado aqui. A instalação do pacote e os testes com PostgreSQL real foram executados. Consulte o [mapa completo](../backend/README.md) antes de usar os comandos antigos: é necessário reinstalar a instalação editável para reconhecer `src/app`.
