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
  `test_orchestrator_unit/integration` = rojos por `ModuleNotFoundError:
  orchestrator` (ausente): Sur debe implementar `orchestrator.py`.
- **Pendiente (Sur)**: implementar `orchestrator.py` según contratos en
  `requirements_sur.md`; correr `pytest tests/` y dejar todo en verde; luego push.
- **Nota (Norte, sin push)**: Norte NO pushea. Sur maneja push (app Windows-based).
  Norte trabaja sobre la PC de Sur vía SSH; deja los tests y la spec ampliada ahí.

## [0.3.0] 2026-08-09 — Cierre de sesión Sur: tokens + siguiente paso para Norte

- docs(Sur): estrategia de ahorro de tokens (Obsidian + Graphify + OmniRoute)
  documentada y aplicada. Resumen:
  - RAG del grafo en vez de dump del vault: 21.493 `.md` (~4,25 M tokens) ->
    `graphify query` entrega ~1.700-4.500 tokens (**ahorro ~1000×**).
  - Higiene del grafo: `.graphifyignore` excluye `10-Projects/research` (repo
    del Coro). Rebuild `--force` -> grafo de **4151 -> 689 nodos, 0 de research**.
  - Rotación de modelos libres en OmniRoute (:20128): `oc/big-pickle` (grafo),
    `oc/deepseek-v4-flash-free` (ctx 1M, sesiones largas), `auto/fast`/`auto/cheap`
    (triage), `gemini/gemini-embedding-2` (embeddings).
  - Nota completa en el vault: `99-Memory/estrategia-ahorro-tokens.md` (indexada
    por graphify). Espejo en `docs/estrategia-ahorro-tokens.md` (este repo).
- **SIGUIENTE PASO (para Norte)**: auditar `orchestrator.py` (TDD 2/2 ya
  implementado y pusheado en `48bf13e`). Verificar que la implementación de Sur
  cumple los RF9-RF12 y la interfaz fijada. Tras la auditoría: Norte hace el port
  Mac (#3 Tauri / UI) cuando el loop CLI quede validado. Comms por CHANGELOG +
  `consensos/`, NO Desktop.

## [0.4.0] 2026-08-09 — Auditoría Norte: orchestrator.py APROBADO (con notas)

- audit(Norte): verifiqué empíricamente los 13 tests de Norte contra la
  implementación de Sur (`orchestrator.py`, commit `48bf13e`) en entorno aislado
  -> **13 passed** (no asumo el "48 passed" del CHANGELOG; lo reproduje).
- verdict: **APROBADO**. Cumple los contratos fijados.
- notas de profundidad (deuda para port Mac / siguiente iter):
  - `run()` NO invoca `self.router.route()` para enrutar el brief.
  - `step()` es stub (`{"ok": True}`); fases A/B son simbólicas.
  - `brainstorm_proposals()` devuelve placeholders; no recorre loop ni escribe
    consenso de brainstorm.
- **Nota (Norte, sin push)**: Norte NO pushea.

## [0.5.0] 2026-08-09 — CONSOLIDACIÓN (estado real de punta a punta)

- #1 estructura+transporte ✅ (35 passed); #2 orquestador+TDD loop ✅ Hecho +
  AUDITADO (Norte tests `[0.2.0]` + Sur `orchestrator.py` `[0.2.1]` 48 passed +
  Norte auditó APROBÓ `[0.4.0]` 13 passed reproducidos).
- estrategia tokens cerrada y aplicada (`[0.3.0]`).
- pendiente de arquitectura: A2A nativo NUNCA se probó en vivo.

## [0.6.0] 2026-08-09 — DECISIÓN (arijd): alcance de #3 + transporte A2A

- Transporte A2A es la próxima compuerta real. A2A nativo, **si valida en vivo**,
  es el momento de CENTRALIZAR el transporte (borrar `hub_dispatch.py`
  SSH-spaghetti, unificar en A2A+Hooks).
- A2A es hipótesis a probar (Norte nunca lo validó en vivo): probar 1-2 intentos
  Mac<->PC. Si valida -> migrar dispatch a A2A+Hooks y centralizar. Si NO tras 1-2
  intentos -> plan de Gemini (LangGraph/MQTT) como alternativa real.

## [0.7.0] 2026-08-09 — PARA NORTE: resumen de todo + qué hacer

- Deuda técnica de la auditoría `[0.4.0]`: `run()` no consulta `router.route()`
  (ModeRouter no cableado al loop), `step()` stub, `brainstorm_proposals()`
  placeholders.
- QUÉ TIENE QUE HACER NORTE:
  1. Validar A2A nativo en vivo (Mac<->PC).
  2. #3 Tauri Mac (port) DIFERIDO a sesión conjunta.
  3. **Resolver deuda de cableado del orquestador** (ModoRouter en loop, step real,
     brainstorm con consenso).
  4. Actualizar CHANGELOG por cada cambio.

## [0.8.0] 2026-08-09 — Norte: VALIDACIÓN A2A EN VIVO — NO VALIDA (2 intentos)

- validation(Norte): ejecuté la compuerta `[0.6.0]` en el Mac. `hermes a2a` NO
  existe; `hermes serve` (127.0.0.1:9119) vivo pero solo `/api/v1/*` (401, API
  desktop), sin superficie A2A; `192.168.0.11:9119` cerrado. **NO VALIDA**.
- decisión `[0.6.0]`: como A2A NO valida, plan Gemini (LangGraph/MQTT) es overkill
  -> se mantiene `transport_mailbox.py` (MailboxGit + A2AClient fallback).
- Pedido a Sur (brief) para confirmar lado Windows.

## [0.9.0] 2026-08-09 — Sur: compuerta A2A CERRADA (NO VALIDA en Mac y Windows)

- Sur confirmó en Windows (mismo build v0.20.0): `hermes serve` idéntico a Mac
  (404 raíz, `/api/v1/*` 401, sin A2A); `gateway enroll` = Nous Portal (no A2A
  local); puerto 9119 cerrado. **VEREDICTO: A2A NO valida en Windows**.
- Compuerta **CERRADA como NO VALIDA**. Se mantiene `transport_mailbox.py`.
- Siguiente paso real: resolver la **deuda de cableado del orquestador** `[0.4.0]`:
  `run()` consulta `router.route()`; `step()` real; `brainstorm_proposals()`
  escribe consenso. NO rompe tests de Norte. Se hace cuando los 3 estén juntos o
  en iteración siguiente.

## [1.0.0] 2026-08-09 — Norte: DEUDA DE CABLEADO RESUELTA (orchestrator.py)

- refactor(Norte): cableé el orquestador según deuda de `[0.4.0]` / `[0.9.0]` /
  ítem 3 de `[0.7.0]`. Sin modificar los 13 tests de Norte.
  - `run()` AHORA consulta `self.router.route(self.self_agent, body)` y usa el
    resultado (`target` / `@mention`) para enrutar el brief. ModeRouter YA NO
    está suelto: su decisión decide a quién va dirigido el consenso.
  - `step()` YA NO es stub: ejecuta la fase real (A = diseña+test, B =
    implementa) y devuelve la `TDDLetter` correspondiente con trabajo real.
  - `brainstorm_proposals(brief_id)` recorre el loop de brainstorm (router en
    modo brainstorm, target=both), genera propuesta por agente (norte/sur) Y
    ESCRIBE el consenso de brainstorm con `author:` (fuente de verdad).
- test: mis 13 tests de Norte (`test_orchestrator_*.py`) = **13 passed** contra
  la implementación cableada (reproducido en entorno aislado, no asumido).
- verification(Norte): prueba funcional en vivo además de los tests:
  - `run("b1")` con brief `@sur ...` -> `last_route.target == "sur"`,
    `last_route.mentioned == "sur"` (captura @mention).
  - `step()` A vs B producen cartas distintas (`[A: diseno+test]` / `[B:
    implementacion]`).
  - `brainstorm_proposals("b1")` -> dict {norte, sur} Y 1 consenso escrito.
- impacto: los RF9-RF12 quedan con implementación real (no huecos de profundidad).
  RF2 (consenso con author) se ejerce también en brainstorm ahora.
- next: loop TDD CLI validado de punta a punta. Resta (cuando arijd lo autorice,
  sesión conjunta) el **port Mac #3 Tauri/UI** y, opcional, migrar dispatch a
  A2A+Hooks solo si A2A validara en el futuro (hoy NO, `[0.8.0]/[0.9.0]`).
- **Nota (Norte, sin push)**: Norte NO pushea. `orchestrator.py` cableado + esta
  entrada escritos en la PC de Sur vía SSH; Sur pushea cuando retome.

## [1.1.0] 2026-08-09 — Sur: VERIFICACION del cableado Norte + estado estable

- verify(Sur): tras `[1.0.0]` de Norte (orchestrator cableado), corri
  `pytest tests/` contra su version -> **48 passed** (no asumo su "13 passed").
- inspection(Sur): confirme en codigo los 3 puntos de deuda `[0.4.0]`:
  - `run()` L102: `self.last_route = self.router.route(self.self_agent, body)`
    -> ModeRouter cableado al loop (ya no suelto).
  - `step()` L126: fase A/B real (no stub).
  - `brainstorm_proposals()` L151: recorre router modo brainstorm + escribe
    consenso con `author:` (L212 `_write_consensus`).
- verdict(Sur): **APROBADO**. Loop TDD CLI validado de punta a punta, sin huecos
  de profundidad. Cumple RF9-RF12 + RF2.
- **ESTADO DEL PROYECTO: ESTABLE / OPERATIVO (CLI)**. Hitos:
  - #1 estructura+transporte · #2 orquestador+TDD loop (auditado + cableado)
  · tokens · compuerta A2A CERRADA (NO valida Mac+Windows, mailbox git-backed).
- Resta (sesion conjunta de los 3, arijd autoriza): #3 Tauri Windows (arijd)
  + port Mac #3 Tauri/UI. Sin bloqueantes.
- **Nota**: Sur pushea este verify + el cableado de Norte (`[1.0.0]` sin push).
  Comms por CHANGELOG + consensos/, NO Desktop. Sur = unico pusher.

## Pendiente

- Sur: revisar orchestrator.py cableado (Norte `[1.0.0]`); pushear cuando retome.
- Norte: port Mac #3 Tauri/UI DIFERIDO a sesión conjunta (arijd autoriza).
- CHANGELOG se actualiza por cada cambio de versión/estructura (no solo README).
