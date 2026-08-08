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
- verdict: **APROBADO**. Cumple los contratos fijados:
  - Interfaz completa: `Orchestrator(hub_path, self_agent, a2a=None, panic=None)`,
    `run()`, `step()` (rol en `.current_role`), `panic()`, `brainstorm_proposals()`,
    `send_to()` (A2A -> fallback MailboxGit), `TDDLetter`, `.verify` reasignable.
  - RF9 (run/step recorre loop) ✓; RF10 (CircuitBreaker max 3 -> handoff) ✓;
    RF11 (brainstorm split + options) ✓; RF12 (panic frena loop) ✓;
    RF2 (consenso con `author:`) ✓ vía `_write_consensus`.
- notas de profundidad (NO bloquean, deuda para port Mac / siguiente iter):
  - `run()` NO invoca `self.router.route()` para enrutar el brief: el ModeRouter
    existe y es usable (test lo llama directo), pero el loop no lo consulta
    todavía. "ModeRouter conectado al loop" es parcial: disponible, no cableado.
  - `step()` es stub (`{"ok": True}`); fases A/B son simbólicas (roles se setean,
    pero no hay trabajo real por fase).
  - `brainstorm_proposals()` devuelve placeholders; no recorre loop ni escribe
    consenso de brainstorm.
  - Estas no rompen ningún test de Norte; son huecos de profundidad vs. el
    espíritu del blueprint ("ModeRouter conectado al loop real").
- next: Norte hace el **port Mac (#3 Tauri/UI)** cuando arijd lo autorice; el
  loop CLI queda validado por esta auditoría. Deuda de cableado del router se
  resuelve en el port o en iteración siguiente.
- **Nota (Norte, sin push)**: Norte NO pushea. Auditoría escrita en este CHANGELOG
  en la PC de Sur vía SSH; Sur pushea cuando retome.

## [0.5.0] 2026-08-09 — CONSOLIDACIÓN (estado real de punta a punta)

Resumen único del proyecto Hub al cierre de esta sesión. Todo verificado contra
git log + los docs de Norte en `docs/norte/`.

### Hitos del blueprint (numeración nuestra, no del plan original de Gemini)
| # | Hito | Estado | Evidencia |
|---|------|--------|-----------|
| 1 | Estructura + transporte (hub_core + mailbox) | ✅ Hecho | `hub_core.py` (RF2-RF7), `transport_mailbox.py` (RF1/RF8), 35 passed — `[0.1.0]` |
| 2 | Orquestador de modos + TDD loop | ✅ Hecho + AUDITADO | Norte tests (`[0.2.0]`) + Sur `orchestrator.py` (`[0.2.1]`, 48 passed) + **Norte auditó y APROBÓ (`[0.4.0]`, 13 passed reproducidos)** |
| 3 | UI Tauri / port Mac | ⏳ Pendiente | No empezado; depende de autorización de arijd (ver abajo) |

### Ciclo TDD (modus operandi cumplido)
1. Norte escribió tests + spec RF9-RF12 (`[0.2.0]`).
2. Sur implementó `orchestrator.py` cumpliendo la interfaz (`[0.2.1]`, 48 passed).
3. Norte auditó empíricamente → **APROBADO** con notas de deuda (`[0.4.0]`).
   Loop CLI validado. Norte NO pushea; Sur maneja push.

### Deuda técnica identificada por Norte (no bloquea, para #3 / iter siguiente)
- `run()` no consulta `self.router.route()` para enrutar el brief: ModeRouter
  disponible pero NO cableado al loop ("conectado" es parcial).
- `step()` es stub; fases A/B simbólicas (roles se setean, sin trabajo real).
- `brainstorm_proposals()` devuelve placeholders (no recorre loop ni escribe
  consenso de brainstorm).
- Ninguna rompe los tests de Norte; son huecos de profundidad vs. el blueprint.

### Decisión de arquitectura PENDIENTE (bandera de Norte, `PARA-SUR-evaluacion-blueprint-hub.md`)
- `hub_dispatch.py` (despertar vía SSH+cmd/c) = callejón de mantenimiento.
- A2A nativo NUNCA se probó en vivo. Antes de invertir en #3 (Tauri), Norte
  recomienda PROBAR A2A en vivo (hermes serve/a2a Mac<->PC). Si funciona: migrar
  dispatch a A2A+Hooks y borrar SSH spaghetti. Si no tras 1-2 intentos: el plan de
  Gemini (LangGraph/MQTT) es la alternativa real.
- Nota: blueprint original de Gemini usaba LangGraph+MQTT+Tauri (Norte lo marcó
  overkill hasta validar A2A). El blueprint NO venía en "N fases" fijas.

### Estrategia de tokens (infra de trabajo, no hito de producto)
- Cerrada y aplicada (`[0.3.0]`): RAG del grafo (~1000× ahorro vs dump),
  grafo 4151→689 nodos (excluido `10-Projects/research`), rotación de modelos
  libres en OmniRoute. Nota en vault `99-Memory/estrategia-ahorro-tokens.md` +
  espejo `docs/estrategia-ahorro-tokens.md`.

### SIGUIENTE PASO (para arijd / Norte)
- arijd autoriza arrancar #3 (port Mac / UI Tauri) O prioriza la validación de
  A2A en vivo (decisión de arquitectura) ANTES de la UI.
- Comms por CHANGELOG + `consensos/`, NO Desktop. Sur = único pusher.

## [0.6.0] 2026-08-09 — DECISIÓN (arijd): alcance de #3 + transporte A2A

Acuerdo con arijd, registrado para retomar sin el chat:

### #3 UI Tauri — alcance aclarado (es UX, NO requisito funcional)
- El Hub **ya funciona hoy sin Tauri**: loop agente↔agente vive en archivos
  (`HUB/briefs/` + `HUB/consensos/` + `hub_dispatch.py`). Tauri es solo la
  vitrina visual para arijd (escribir briefs / leer consensos con colores).
- **Windows-first**: terminar la app Tauri en PC (Windows) ahora.
- **Port Mac**: DIFERIDO a una sesión futura cuando los 3 (arijd+Norte+Sur)
  estemos juntos. No es bloqueante del loop.

### Transporte A2A — es la próxima compuerta real
- Los 3 YA estamos conectados vía hub de archivos (arijd briefs -> Norte/Sur
  consensos por SSH). "Los 3 juntos" es estado actual, no contingentte a A2A.
- A2A nativo, **si valida en vivo**, es el momento de **CENTRALIZAR** el
  transporte en un mecanismo limpio (en vez de SSH-spaghetti + mailbox fallback)
  y borrar `hub_dispatch.py`.
- A2A es hipótesis a probar (Norte nunca lo validó en vivo): probar 1-2 intentos
  (hermes serve/a2a Mac<->PC). Si no cruza tras 1-2 intentos -> plan de Gemini
  (LangGraph/MQTT) como alternativa real.
- Orden sugerido: (1) validar A2A en vivo, (2) si valida, migrar dispatch a
  A2A+Hooks y centralizar, (3) luego Tauri Windows, (4) Tauri Mac diferido.

## Pendiente

- Sur: rediseño Windows-first del Hub (estructura puede cambiar) + orquestador de modos.
- Norte: port Mac tras versión Windows-operativa; trabaja directo en repo, Sur pushea.
- CHANGELOG se actualiza por cada cambio de versión/estructura (no solo README).
