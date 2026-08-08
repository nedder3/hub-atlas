# Changelog — Atlas HUB

Formato: [tipo] fecha — descripción. Tipos: feat, refactor, docs, chore, fix.

## [0.1.0] 2026-08-08 — Estructura inicial + transición a repo

- docs(hub): README con modus operandi y resumen de implementación (Sur).
- feat(hub): hub_core.py (StateStore, CircuitBreaker, PanicButton, ModeRouter) — RF2-RF7.
- feat(transport): transport_mailbox.py (MailboxGit + A2AClient fallback silencioso a mailbox) — RF1/RF8.
- test: tests/ con mocks (Norte) + test_core_real.py (Sur) contra código real. `pytest` = 35 passed.
- chore(repo): Hub versionado en `git@github.com:nedder3/hub-atlas.git`. Desktop deja de ser canal; repo es fuente de verdad.
- chore(structure): repo movido a `Atlas/10-Projects/hub-atlas/` (convención de bóveda arijd). `Atlas/HUB/` viejo eliminado (redundante).
- note: Sur rediseñará el Hub para Windows; Norte hará el port Mac cuando quede operativo en Windows.

## [0.1.1] 2026-08-08 — Estrategia de sincronización + higiene

- chore(repo): Sur corrige higiene — `git rm --cached` de `.processing/`, `.seen/`,
  `.seen.log`, `__pycache__` y alinea `.gitignore` (agrega `.seen/`). Commit `f542a3a`.
- decision(sync): Norte trabaja DIRECTO sobre el repo local (Mac); Sur SIEMPRE pushea
  todo lo que toque. NO ping-pong de pull cada rato. Un solo pusher (Sur) evita
  conflictos de merge.
- decision(comms): Norte↔Sur se comunican vía CHANGELOG + `consensos/`, no push/pull
  constante ni Desktop. Mensajes y decisiones van al CHANGELOG.
- next: orquestador de modos + TDD loop (#2 blueprint) — conectar ModeRouter al loop
  real (briefs -> enrute por modo -> CircuitBreaker en TDD A diseña/test -> B
  implementa -> A verifica -> itera max 3). UI Tauri (#3) espera al loop en CLI.
  **TDD estricto**: Norte escribe los tests, Sur implementa (ver `todo` abajo).

## [todo] 2026-08-08 — Norte: tests del orquestador de modos + TDD loop

Sur se detiene aquí (TDD: Norte tests, Sur código). Norte debe dejar en
`tests/` los tests del orquestador ANTES de que Sur implemente. Cobertura
requerida (mismos tipos que el andamiaje actual):

- **Unitarios** (`test_orchestrator_unit.py`):
  - `Orchestrator` lee `briefs/`, enruta por modo (chat 1-1-1 / brainstorm split).
  - Circuit Breaker se aplica en el loop TDD: A diseña+test -> B implementa ->
    A verifica -> itera max 3 (RF3). Si falla 3 -> handoff humano.
  - ModeRouter conectado al loop (no suelto): `route()` decide target y modo.
  - PanicButton detiene el loop (RF5).
  - @mentions fuerzan nodo (RF7).
- **Integración** (`test_orchestrator_integration.py`):
  - Loop end-to-end con mocks de A2A/Mailbox: un brief recorre A->B->A y produce
    `consens_<agente>_*.md` con `author:` (RF2).
  - Brainstorm: ambos agentes tiran propuesta en paralelo; humano elige
    (elegir/re-evaluar/descartar) vía `options_brainstorm()` (RF6).
  - Mailbox fallback cuando A2A no cruza (RF1/RF8).
- **Documentación** (`test_orchestrator_docs.py`):
  - Trazabilidad RF->test del orquestador (al estilo `test_docs.py`).
  - Tabla en `requirements_sur.md` ampliada con los RF del orquestador (RF9-RF12).

Contratos sugeridos (Norte define la interfaz final; Sur la implementa):
`Orchestrator.run(brief_id)`, `Orchestrator.step()`, `TDDLetter` (A/B roles),
`Orchestrator.panic()`. Sur respeta la interfaz que Norte fije en los mocks.

Cuando Norte deje los tests y pushee, Sur implementa `orchestrator.py` y corre
`pytest tests/` (debe quedar en verde). Luego Norte audita.

## [0.2.0] 2026-08-08 — Norte deja tests del orquestador (TDD: paso 1 de 2)

- test(Norte): `tests/test_orchestrator_unit.py` — 7 tests sobre la interfaz del
  orquestador (run/step, CircuitBreaker en loop RF3, PanicButton RF5, ModeRouter
  conectado RF6, @mentions RF7, TDDLetter).
- test(Norte): `tests/test_orchestrator_integration.py` — 4 tests end-to-end con
  mocks A2A/Mailbox (loop A->B->A produce consenso con author RF2; brainstorm
  split + options RF6; mailbox fallback RF1/RF8).
- test(Norte): `tests/test_orchestrator_docs.py` — 2 tests de trazabilidad RF9-RF12.
- docs(Norte): `requirements_sur.md` ampliado con RF9 (orquestador loop TDD A->B->A),
  RF10 (Circuit Breaker en loop), RF11 (brainstorm split + elección), RF12 (panic
  detiene loop). Interfaces fijadas por Norte.
- **Estado TDD**: `test_orchestrator_docs.py` = 2 passed (tabla ya ampliada).
  `test_orchestrator_unit/integration` = rojos por ` ModuleNotFoundError:
  orchestrator` (ausente): Sur debe implementar `orchestrator.py`.
- **Pendiente (Sur)**: implementar `orchestrator.py` según contratos en
  `requirements_sur.md`; correr `pytest tests/` y dejar todo en verde; luego push.
- **Nota (Norte, sin push)**: Norte NO pushea. Sur maneja push (app Windows-based).
  Norte trabaja sobre la PC de Sur vía SSH; deja los tests y la spec ampliada ahí.

## [0.2.1] 2026-08-09 — Sur implementa `orchestrator.py` (TDD: paso 2 de 2)

- feat(Sur): `orchestrator.py` — `Orchestrator` + `TDDLetter` cumpliendo la
  interfaz fijada por Norte en `requirements_sur.md` / `test_orchestrator_*.py`.
  - `run(brief_id)`: loop TDD A diseña/test -> B implementa -> A verifica,
    itera max 3 con CircuitBreaker (RF9+RF10); verificacion OK escribe
    `consens_<agente>_*.md` con `author:` (RF2).
  - `step()`: un paso del loop; rol actual en `.current_role`.
  - `panic()`: presiona PanicButton y frena el loop (RF12).
  - `brainstorm_proposals(brief_id)`: dict {norte, sur} (RF11).
  - `send_to(peer, msg)`: usa A2AClient; si no cruza, cae a MailboxGit y
    devuelve `ACK(mailbox):...` (RF1/RF8).
  - Reusa `hub_core.StateStore/CircuitBreaker/PanicButton/ModeRouter` ya
    aprobados; `.verify` es atributo reasignable (los tests lo sobreescriben).
- test: `pytest tests/` = **48 passed** (35 previos + 7 unit + 4 integration
  + 2 docs de Norte). Todo verde SIN modificar los tests de Norte.
- **Estado TDD**: paso 2/2 completo. `orchestrator.py` pasa los contratos de
  Norte. Pendiente: **Norte audita** la implementacion (acordado en modus operandi).

## Pendiente

- Sur: rediseño Windows-first del Hub (estructura puede cambiar) + orquestador de modos.
- Norte: port Mac tras versión Windows-operativa; trabaja directo en repo, Sur pushea.
- CHANGELOG se actualiza por cada cambio de versión/estructura (no solo README).
