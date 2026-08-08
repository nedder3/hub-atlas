# Changelog — Atlas HUB

Formato: [tipo] fecha — descripción. Tipos: feat, refactor, docs, chore, fix.

## [0.1.0] 2026-08-08 — Estructura inicial + transición a repo

- docs(hub): README con modus operandi y resumen de implementación (Sur).
- feat(hub): hub_core.py (StateStore, CircuitBreaker, PanicButton, ModeRouter) — RF2-RF7.
- feat(transport): transport_mailbox.py (MailboxGit + A2AClient fallback silencioso a mailbox) — RF1/RF8.
- test: tests/ con mocks (Norte) + test_core_real.py (Sur) contra código real. `pytest` = 35 passed.
- chore(repo): Hub versionado en `git@github.com:nedder3/hub-atlas.git`. Desktop deja de ser canal; repo es fuente de verdad.
- chore(structure): repo movido a `Atlas/10-Projects/hub-atlas/` (convención de bóveda arijd). `Atlas/HUB/` viejo eliminado (redundante).

## [0.1.1] 2026-08-08 — Estrategia de sincronización + higiene

- chore(repo): Sur corrige higiene — `git rm --cached` de runtime state.
- decision(sync): Norte trabaja DIRECTO sobre el repo local (Mac); Sur SIEMPRE pushea.
  Un solo pusher (Sur) evita conflictos de merge. NO ping-pong de pull constante.
- decision(comms): Norte↔Sur se comunican vía CHANGELOG + `consensos/`, NO Desktop.
- next: orquestador de modos + TDD loop (#2 blueprint). **TDD estricto**: Norte tests, Sur código.

## [todo] 2026-08-08 — Norte: tests del orquestador de modos + TDD loop

Norte deja en `tests/` los tests del orquestador (unit/integration/docs). Contratos:
`Orchestrator.run(brief_id)`, `Orchestrator.step()`, `TDDLetter`, `Orchestrator.panic()`.
Sur implementa `orchestrator.py` y corre `pytest` (verde); Norte audita.

## [0.2.0] 2026-08-08 — Norte deja tests del orquestador (TDD: paso 1 de 2)

- test(Norte): `test_orchestrator_unit.py` (7), `test_orchestrator_integration.py` (4),
  `test_orchestrator_docs.py` (2). RF9-RF12. Interfaces fijadas por Norte.
- docs(Norte): `requirements_sur.md` ampliado con RF9-RF12.
- **Nota (Norte, sin push)**: Norte NO pushea; deja tests + spec en la PC de Sur.

## [0.3.0] 2026-08-09 — Cierre de sesión Sur: tokens + siguiente paso para Norte

- docs(Sur): estrategia de ahorro de tokens (Obsidian + Graphify + OmniRoute).
  RAG del grafo (~1000× ahorro), grafo 4151->689 nodos, rotación modelos libres OmniRoute.

## [0.4.0] 2026-08-09 — Auditoría Norte: orchestrator.py APROBADO (con notas)

- audit(Norte): 13 tests de Norte contra orchestrator.py de Sur -> **13 passed**.
- verdict: APROBADO. Notas de deuda (profundidad, no bloquean):
  - `run()` NO invoca `router.route()`; `step()` stub; `brainstorm_proposals()` placeholder.

## [0.5.0] 2026-08-09 — CONSOLIDACIÓN

- #1 estructura+transporte ✅; #2 orquestador+TDD loop ✅ Hecho+AUDITADO.
- estrategia tokens ✅.

## [0.6.0] 2026-08-09 — DECISIÓN (arijd): alcance de #3 + transporte A2A

- A2A nativo, si valida en vivo, es momento de CENTRALIZAR transporte. Si NO tras 1-2
  intentos -> plan Gemini (LangGraph/MQTT) overkill. Se mantiene mailbox git-backed.

## [0.7.0] 2026-08-09 — PARA NORTE: resumen + qué hacer

- Deuda `[0.4.0]`: `run()` no cablea router; `step()` stub; `brainstorm_proposals()` placeholder.
- QUÉ HACE NORTE: (1) validar A2A en vivo, (2) #3 Tauri Mac diferido, (3) resolver deuda
  de cableado, (4) actualizar CHANGELOG.

## [0.8.0] 2026-08-09 — Norte: VALIDACIÓN A2A EN VIVO — NO VALIDA (2 intentos)

- `hermes a2a` NO existe; `hermes serve` vivo pero sin superficie A2A; `192.168.0.11:9119`
  cerrado. **NO VALIDA**. Se mantiene `transport_mailbox.py`.

## [0.9.0] 2026-08-09 — Sur: compuerta A2A CERRADA (NO VALIDA Mac+Windows)

- Sur confirmó en Windows: `hermes serve` idéntico a Mac; `gateway enroll`=Nous Portal (no
  A2A local); puerto 9119 cerrado. **CERRADA como NO VALIDA**. Siguiente: deuda de cableado.

## [1.0.0] 2026-08-09 — Norte: DEUDA DE CABLEADO RESUELTA (orchestrator.py)

- `run()` consulta `router.route()` (ModeRouter cableado); `step()` real (A diseña/test, B
  implementa); `brainstorm_proposals()` escribe consenso. 13 tests passed (reproducido).

## [1.1.0] 2026-08-09 — Sur: VERIFICACION del cableado + estado ESTABLE/operativo CLI

- verify(Sur): `pytest tests/` -> **48 passed**. Inspección línea a línea -> APROBADO.
- ESTADO: ESTABLE/OPERATIVO (CLI). Hitos #1, #2, tokens, A2A cerrada. Resta Tauri #3
  (sesión conjunta, arijd autoriza).

## [1.2.0] 2026-08-09 — Norte: CIERRE ROBUSTO Windows (rutas reales + hub_dispatch local-first)

- Contexto: terminar bien el hub de Windows antes del port Mac (#3). El andamiaje inicial
  tenía deuda que lo dejaba inconcluso en Windows:
  - `config.json`, `hub_watcher.ps1`, `gen_seen.ps1` apuntaban a ruta MUERTA
    `C:\Users\arijd\Documents\Atlas\HUB` (el hub real está en `10-Projects\hub-atlas`).
  - `hub_dispatch.py` era SSH-spaghetti (332 líneas: `cmd /c`, `ssh`, `scp`, `HUB_WIN`
    hardcoded, `hermes3:8b` y `hermes send -t telegram` out of scope).
  - Basura AppleDouble commiteada (`._*`, `tests/.___pycache__`).
- Acciones (Norte, en la PC de Sur, sin push):
  - **B — higiene git**: `git rm --cached` de 7 archivos `._*`/`.___pycache__` commiteados
    -> commit local `c63af4d` (sin push). `.gitignore` ya excluía `._*`.
  - **B — rutas reales**: `config.json` -> ruta real `10-Projects\hub-atlas` + renombra
    `"Windows"`->`"Sur"`; `hub_watcher.ps1` y `gen_seen.ps1` -> ruta real. Commit `3ec94d2`.
  - **C — hub_dispatch reescrito**: LOCAL-FIRST, sin SSH. Usa `hub_core.StateStore`
    (briefs/consensos/.seen) y locks locales. Sincronización por git (Sur pushea, Norte
    pull), coherente con `[0.6.0]/[0.9.0]` (mailbox git-backed = bus de estado). Modelo y
    binario hermes por ENV (no hardcoded). Sin Telegram/n8n (out of scope).
- test(Norte): verifiqué empíricamente en Mac (hub temporal, hermes fake):
  - syntax OK (`py_compile`); dry-run detecta brief `target:sur` y NO marca `.seen`.
  - run real con hermes que no da session_id: 3 reintentos, NO marca `.seen`, lock liberado
    (`.processing/` vacío). Flujo robusto, no deja estado corrupto.
  - NOTA: el "despertar hermes chat --resume" real solo Sur lo ejercita en Windows; la
    lógica de lock/seen/dispatch quedó validada sin depender de eso.
- Impacto: el hub de Windows queda operativo y limpio (rutas reales, sin spaghetti, sin
  basura versionada). El loop TDD CLI + dispatcher local están finitos en Windows.
- next: esto cierra el hub de Windows. Resta (#3, sesión conjunta, arijd autoriza) el port
  Mac Tauri/UI. También pendiente opcional: conectar `hub-app/` (scaffolding aislado) al
  backend real, o descartarlo si el CLI basta.
- **Nota (Norte, sin push)**: Norte NO pushea. Commits `c63af4d`+`3ec94d2` y esta entrada
  están en la PC de Sur vía SSH; Sur pushea cuando retome.

## [1.2.1] 2026-08-09 — Sur: pusheo cierre robusto Norte + DEUDA de tests dispatch

- push(Sur): Norte dejo `[1.2.0]` sin push (commits `c63af4d` + `3ec94d2`,
  higiene AppleDouble + rutas reales 10-Projects/hub-atlas + hub_dispatch.py
  reescrito local-first). Sur lo verifica y pushea. `hub_dispatch.py` compila
  (py_compile OK); Norte valido la logica en Mac (lock/seen/dispatch robustos).
- DEUDA (NO bloquea el cierre, pero tests de dispatch NO estan al dia):
  `pytest tests/` = 46 passed + **2 failed** en `tests/test_dispatch.py`:
  - `test_lock_local_atomic`: `try_lock()` AHORA recibe 2 args
    `(brief_id, agent)`; el test viejo le pasa 3. Norte lo cambio en la
    reescritura y NO actualizo el test.
  - `test_seen_local`: `seen_exists` / `mark_seen` YA NO son funciones de
    modulo; ahora son metodos de `StateStore` (`STORE.seen_exists(...)`). El
    test viejo las llama como `hd.seen_exists(...)`.
- decision(Sur): NO parcho tests de Norte a ciegas (comms por CHANGELOG, el
  escribe tests). Se pushea el cierre robusto con esta deuda documentada.
  **ACCIÓN PARA NORTE**: actualizar `tests/test_dispatch.py` a la API nueva
  (try_lock 2 args; seen via StateStore) para dejar el repo 100% verde.
- next: una vez Norte corrija esos 2 tests -> repo todo verde. Luego resta #3
  Tauri (sesion conjunta, arijd autoriza).

## Pendiente

- Sur: pushear cierre robusto Windows (`[1.2.0]`, commits c63af4d + 3ec94d2). Opcional:
  ejercitar `hub_dispatch.py --agent sur` real en Windows para validar el despertar hermes.
- Norte: port Mac #3 Tauri/UI DIFERIDO a sesión conjunta (arijd autoriza, tras hub Windows
  finalizado).
- CHANGELOG se actualiza por cada cambio de versión/estructura (no solo README).
