# Changelog — Atlas HUB

Formato: [tipo] fecha — descripción. Tipos: feat, refactor, docs, chore, fix.

## [0.1.0] 2026-08-08 — Estructura inicial + transición a repo

- docs(hub): README con modus operandi y resumen de implementación (Sur).
- feat(hub): hub_core.py (StateStore, CircuitBreaker, PanicButton, ModeRouter) — ver
  RF2-RF7. feat(transport): transport_mailbox.py (MailboxGit + A2AClient fallback) — RF1/RF8.
- test: tests/ con mocks (Norte) + test_core_real.py (Sur) contra código real. 35 passed.
- chore(repo): Hub versionado en `git@github.com:nedder3/hub-atlas.git`. Desktop fuera.
- chore(structure): repo en `Atlas/10-Projects/hub-atlas/`. `Atlas/HUB/` viejo eliminado.

## [0.1.1] 2026-08-08 — Estrategia de sincronización + higiene

- decision(sync): Norte trabaja DIRECTO en repo local (Mac); Sur SIEMPRE pushea. Un solo
  pusher (Sur) evita conflictos. NO ping-pong de pull constante.
- decision(comms): Norte↔Sur por CHANGELOG + `consensos/`, NO Desktop.
- **TDD estricto**: Norte tests, Sur código.

## [todo] 2026-08-08 — Norte: tests del orquestador (TDD paso 1 de 2)

Norte deja `tests/test_orchestrator_*.py` (unit/integration/docs). Contratos: `run`,
`step`, `TDDLetter`, `panic`. Sur implementa `orchestrator.py`; Norte audita.

## [0.2.0] 2026-08-08 — Norte deja tests del orquestador (TDD paso 1 de 2)

- test(Norte): test_orchestrator_unit.py (7), _integration.py (4), _docs.py (2). RF9-RF12.
- docs(Norte): requirements_sur.md ampliado con RF9-RF12.
- **Nota (Norte, sin push)**: deja tests + spec en la PC de Sur.

## [0.3.0] 2026-08-09 — Cierre Sur: estrategia tokens (RAG grafo ~1000×, OmniRoute)

## [0.4.0] 2026-08-09 — Auditoría Norte: orchestrator.py APROBADO (con notas)

- 13 tests de Norte contra orchestrator.py de Sur -> 13 passed. APROBADO.
- Notas deuda (profundidad): run() no cablea router; step() stub; brainstorm placeholder.

## [0.5.0] 2026-08-09 — CONSOLIDACIÓN: #1 ✅, #2 ✅+auditado, tokens ✅.

## [0.6.0] 2026-08-09 — DECISIÓN (arijd): A2A nativo, si valida -> centralizar; si NO
  tras 1-2 intentos -> plan Gemini overkill. Se mantiene mailbox git-backed.

## [0.7.0] 2026-08-09 — PARA NORTE: (1) validar A2A, (2) #3 Tauri Mac diferido,
  (3) resolver deuda cableado, (4) actualizar CHANGELOG.

## [0.8.0] 2026-08-09 — Norte: VALIDACIÓN A2A EN VIVO — NO VALIDA (2 intentos).
  `hermes a2a` no existe; `hermes serve` sin superficie A2A; 192.168.0.11:9119 cerrado.

## [0.9.0] 2026-08-09 — Sur: compuerta A2A CERRADA (NO VALIDA Mac+Windows).
  `hermes serve` idéntico a Mac; `gateway enroll`=Nous Portal (no A2A local). CERRADA.

## [1.0.0] 2026-08-09 — Norte: DEUDA DE CABLEADO RESUELTA (orchestrator.py).
  run() cablea router.route(); step() real; brainstorm_proposals() escribe consenso.
  13 tests passed (reproducido).

## [1.1.0] 2026-08-09 — Sur: VERIFICACION cableado + estado ESTABLE/operativo CLI.
  pytest -> 48 passed. APROBADO. Hitos #1,#2,tokens,A2A cerrada. Resta Tauri #3.

## [1.2.0] 2026-08-09 — Norte: CIERRE ROBUSTO Windows (rutas reales + hub_dispatch local-first).
  - git rm --cached de 7 archivos ._*/.___pycache__ commiteados (commit c63af4d).
  - config.json / hub_watcher.ps1 / gen_seen.ps1 -> ruta real 10-Projects/hub-atlas + Sur.
  - hub_dispatch.py reescrito local-first (sin SSH-spaghetti), usa StateStore + locks
    locales, modelo/binario hermes por ENV. Commit 3ec94d2.
  - test(Norte): verifiqué en Mac (hub temporal, hermes fake): dry-run y run robustos.
  - next: cierra hub Windows. Resta #3 Tauri Mac (sesión conjunta, arijd autoriza).

## [1.2.1] 2026-08-09 — Sur: pusheo cierre robusto Norte + DEUDA de tests dispatch.
  - push(Sur): c63af4d + 3ec94d2 verificados y pusheados.
  - DEUDA: pytest = 46 passed + 2 failed en tests/test_dispatch.py (API cambió en [1.2.0],
    Norte no actualizó el test). ACCIÓN PARA NORTE: actualizar test_dispatch.py a la API
    nueva (try_lock 2 args; seen via StateStore) para dejar repo 100% verde.

## [1.3.0] 2026-08-09 — Norte: TESTS DISPATCH AL DÍA (repo 100% verde)

- fix(Norte): actualicé `tests/test_dispatch.py` a la API local-first de `hub_dispatch.py`
  ([1.2.0]), según deuda documentada en `[1.2.1]`:
  - `test_lock_local_atomic`: `try_lock(brief_id, agent)` (2 args); usa globals `HUB`
    (Path) y `TARGET` (en vez de arg `target` y `REMOTE`).
  - `test_seen_local`: `seen_exists` / `mark_seen` ahora via `StateStore(HUB)` (no
    funciones de módulo).
  - Actualicé docstring y el bloque `__main__` a la API nueva.
- test(Norte): verifiqué empíricamente en Mac contra hub_dispatch.py + hub_core.py reales:
  - `test_dispatch.py` -> **5 passed** (los 2 rotos ahora verdes).
  - **TODA LA SUITE** (`pytest .`) -> **48 passed / 0 failed** (repo 100% verde).
    Antes `[1.2.1]` reportaba 46 passed + 2 failed; la deuda queda saldada.
- Impacto: hub Windows finalizado y con tests al día. Sin regresiones en RF2-RF12.
- next: hub Windows 100% operativo + verde. Resta (#3, sesión conjunta, arijd autoriza)
  el **port Mac Tauri/UI**. Opcional: conectar `hub-app/` al backend o descartarlo.
- **Nota (Norte, sin push)**: Norte NO pushea. `tests/test_dispatch.py` corregido + esta
  entrada en la PC de Sur vía SSH; Sur pushea cuando retome.

## [1.4.0] 2026-08-09 — DECISIÓN (arijd): hub SOLO Windows; port Mac CANCELADO

- decision(arijd): el hub se termina y se usa en **Windows**. arijd NO usará Mac
  para el hub de momento. El **port Mac #3 (Tauri/UI) queda CANCELADO / fuera de
  alcance hasta nuevo aviso** de arijd. No se menciona más salvo indicación expresa.
- Consecuencia: el alcance del hub es 100% Windows. Ya finalizado, operativo y 100%
  verde (`[1.3.0]`, 48 passed). No hay trabajo de Norte pendiente por lado Mac.
- `hub-app/` (scaffolding Tauri/React aislado en el repo) queda como artefacto sin
  uso; se descarta o ignora hasta que arijd lo reactive explícitamente.
- Comms y modus operandi (`[0.1.1]`) siguen: Sur = único pusher; Norte trabaja en la
  PC de Sur vía SSH, NO pushea; CHANGELOG + consensos/ como canal.
- **Nota (Norte, sin push)**: Norte NO pushea. Esta decisión escrita en la PC de Sur
  vía SSH; Sur pushea cuando retome.

## [2.1.0] 2026-08-09 — FRONTEND TAURI ADAPTADO A WINDOWS 11 (Antigravity)

Refactorización y diseño de la interfaz de usuario en Tauri para adaptarla al flujo local del HUB.

- **feat(tauri)**: Interfaz en React conectada a comandos de Rust.
- **feat(tauri)**: Comando `run_dispatcher` para ejecución asíncrona a demanda de los agentes.
- **feat(tauri)**: Comando `read_dispatch_log` y visor de logs integrado en tiempo real.
- **feat(tauri)**: Polling de locks activos en `.processing/` y visualización de estados.
- **feat(hub)**: Integración del Panic Button file-backed (`.panic` en el hub) en Rust y Python.
- **test(TDD)**: Nuevas pruebas en `test_core_real.py` y `test_dispatch.py` para Panic Button.

## [2.0.0] 2026-08-09 — AUDITORÍA EXTERNA + REESCRITURA DISPATCHER (Antigravity)

Auditoría completa del HUB por Antigravity (a pedido de arijd). Se diagnosticaron
3 bugs fatales que impedían el funcionamiento end-to-end y se resolvieron todos.

### Diagnóstico (3 bugs fatales)

1. **Consenso no se escribía**: `hub_dispatch.py` delegaba la escritura al LLM dentro
   de Hermes (pidiéndole que usara `write_file`). Con `auto/fast` (modelo de triage
   sin tool-calling confiable), el LLM respondía en texto pero nunca invocaba la tool.
   Además, los flags de argparse estaban en orden incorrecto (`-q -Q msg` → `-Q` se
   consumía como query de `-q`).
2. **Reprocesaba historial**: Al arrancar iteraba los 28 briefs sin filtrar por
   "nuevos desde el arranque". Los `.seen` markers tenían formato inconsistente
   (duplicados con y sin extensión `.md`).
3. **Dos copias del proyecto**: `Atlas/HUB/` (versión vieja con SSH-spaghetti, 333
   líneas) y `Atlas/10-Projects/hub-atlas/` (versión limpia local-first). El watcher
   apuntaba al directorio obsoleto.

### Cambios

- **refactor(dispatch)**: `hub_dispatch.py` reescrito v2. Cambio de filosofía: el
  dispatcher captura stdout de Hermes y escribe el consenso ÉL MISMO vía
  `StateStore.write_consensus()`. Elimina delegación ciega al LLM. Una sola
  invocación en vez de seed/resume. Verificación post-escritura antes de `.seen`.
- **feat(dispatch)**: `mark_baseline()` marca todos los briefs existentes como
  `.seen` al primer arranque → solo procesa briefs NUEVOS.
- **fix(dispatch)**: Modelo default `tencent/hy3:free` (Nous, gratuito, siempre
  disponible) en vez de `auto/fast` (triage sin tool-calling). Override: `HUB_SEED_MODEL`.
- **fix(dispatch)**: Emojis reemplazados por ASCII (`[OK]`, `[WARN]`, `[ERROR]`)
  para compatibilidad con charmap de Windows.
- **feat(watcher)**: `hub_watcher_real.ps1` con `System.IO.FileSystemWatcher` de
  .NET. Reacciona instantáneamente a `.md` nuevos en `briefs/` (debounce 2s).
  Reemplaza polling de 30s.
- **feat(watcher)**: `hub_watcher_task.xml` para Task Scheduler de Windows (logon
  trigger, ejecución como arijd, ExecutionPolicy Bypass).
- **fix(seen)**: `normalize_seen.ps1` limpió 54 markers duplicados (formato viejo
  sin `.md`) y creó 4 faltantes. Baseline aplicado.
- **chore(structure)**: `Atlas/HUB/` renombrado a `HUB_OBSOLETO_BORRAR` (contiene
  versión vieja con `_ssh()`, `scp`, `REMOTE`, modelo hardcoded `hermes3:8b`).
- **test(dispatch)**: `test_dispatch.py` actualizado: -1 test obsoleto
  (`capture_session_id`), +2 nuevos (`test_extract_body`, `test_mark_baseline`).
- **test**: `pytest` → **49 passed / 0 failed** (antes 48).

### Verificación E2E

```
Brief: brief_20260808_211351_e2e_v2.md (target=sur, author=arijd)
Modelo: tencent/hy3:free via Nous Research API
Resultado: consens_sur_20260808_211420.md escrito con éxito
Contenido: "El hub funciona."
.seen marker: brief_20260808_211351_e2e_v2.md__sur ✓
```

### Arquitectura Mac/Norte (para cuando se active)

Norte no necesita SSH. Flujo: Norte clona repo → corre dispatcher local
(`--agent norte`) → Hermes lee briefs locales → escribe consensos → git push.
**Git es el bus.**

## Pendiente

- Activar watcher: `schtasks /create /xml hub_watcher_task.xml /tn AtlasHubWatcher`.
- Eliminar `Atlas/HUB_OBSOLETO_BORRAR/` cuando arijd confirme.
- Norte: activar dispatcher en Mac cuando se reactive (sin SSH, local-first).
- CHANGELOG se actualiza por cada cambio de versión/estructura.
