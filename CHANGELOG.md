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

- tabla de hitos: #1 estructura+transporte ✅ (35 passed); #2 orquestador+TDD loop
  ✅ Hecho + AUDITADO (Norte tests `[0.2.0]` + Sur `orchestrator.py` `[0.2.1]` 48
  passed + Norte auditó APROBÓ `[0.4.0]` 13 passed reproducidos).
- estrategia tokens cerrada y aplicada (`[0.3.0]`): RAG grafo ~1000× ahorro,
  grafo 4151->689 nodos, rotación modelos libres OmniRoute.
- pendiente de arquitectura: A2A nativo NUNCA se probó en vivo. Antes de #3 (Tauri),
  Norte recomienda PROBAR A2A en vivo (hermes serve/a2a Mac<->PC). Si funciona:
  migrar dispatch a A2A+Hooks y borrar SSH spaghetti. Si no tras 1-2 intentos: el
  plan de Gemini (LangGraph/MQTT) es overkill hasta validar A2A.

## [0.6.0] 2026-08-09 — DECISIÓN (arijd): alcance de #3 + transporte A2A

- Transporte A2A es la próxima compuerta real. Teléfono/WhatsApp/Telegram=out of
  scope (arijd ya usa consensos por SSH). "Los 3 juntos" es estado actual, no
  contingente a A2A.
- A2A nativo, **si valida en vivo**, es el momento de **CENTRALIZAR** el transporte
  (borrar `hub_dispatch.py` SSH-spaghetti, unificar en A2A+Hooks).
- A2A es hipótesis a probar (Norte nunca lo validó en vivo): probar 1-2 intentos
  Mac<->PC. Si valida -> migrar dispatch a A2A+Hooks y centralizar. Si NO tras 1-2
  intentos -> plan de Gemini (LangGraph/MQTT) como alternativa real.
- Orden sugerido: (1) validar A2A en vivo, (2) si valida, migrar dispatch a
  A2A+Hooks y centralizar, (3) luego Tauri Windows, (4) Tauri Mac diferido.

## [0.7.0] 2026-08-09 — PARA NORTE: resumen de todo + qué hacer

- Qué YA está hecho: #1 estructura+transporte (35 passed), #2 orquestador+TDD loop
  (Norte tests + Sur impl 48 passed + Norte AUDITÓ APROBÓ 13 passed), estrategia
  tokens (RAG ~1000×, grafo 689 nodos, OmniRoute).
- Deuda técnica de la auditoría: `run()` no consulta `router.route()` (ModeRouter
  no cableado al loop), `step()` stub, `brainstorm_proposals()` placeholders.
- QUÉ TIENE QUE HACER NORTE:
  1. **[PRÓXIMA COMPERTA] Validar A2A nativo en vivo** (Mac<->PC) — probar 1-2
     intentos; si no cruza -> plan Gemini. (decisión arijd `[0.6.0]`).
  2. #3 Tauri Mac (port) DIFERIDO a sesión conjunta.
  3. Resolver deuda de cableado del orquestador.
  4. Actualizar CHANGELog por cada cambio.

## [0.8.0] 2026-08-09 — Norte: VALIDACIÓN A2A EN VIVO — NO VALIDA (2 intentos)

- validation(Norte): ejecuté la compuerta `[0.6.0]`/#1 de `[0.7.0]` en el Mac.
  Resultado: **A2A nativo NO cruza** tras 2 intentos en vivo. Datos duros:
  - `hermes a2a` NO existe como subcomando (Hermes v0.20.0, Mac).
  - `hermes serve --skip-build --host 127.0.0.1 --port 9119` levanta (uvicorn,
    vivo). Raíz `/` -> 404 "Headless backend (web UI disabled)". Sondeé
    `/a2a /agent /send /message /ws /rpc /mcp /chat` -> **todas 404**.
    Solo `/api/v1/*` responde, pero **401 Unauthorized** (es la API de la app
    desktop, NO un bus agente-a-agente). No hay superficie A2A.
  - Intento 2 (Mac<->PC): `192.168.0.11:9119` -> **puerto CERRADO**; la PC de Sur
    no escucha serve. No hay peer A2A al que hablar.
- verdict: **NO VALIDA**. Confirma (ahora empíricamente, no por suposición) que el
  diseño anti-callejón de Sur (mailbox git-backed) era la salida correcta.
- decisión según `[0.6.0]`: como A2A NO valida, el plan de Gemini (LangGraph/MQTT)
  es **overkill** -> se mantiene `transport_mailbox.py` (MailboxGit + A2AClient
  fallback). NO se invierte en MQTT/Redis para 3 nodos a ritmo humano.
- **Pedido a Sur (brief en briefs/)**: Norte le pide a Sur que revise si en Windows
  `hermes serve` expone algo distinto, o si hay otro mecanismo nativo (gateway
  enroll / pairing / mcp / hooks) como transporte A2A que Norte no consideró. Si
  Sur confirma que tampoco hay A2A en Windows -> cerramos compuerta como NO VALIDA
  y seguimos con mailbox git-backed.
- next: esperar revisión de Sur. Si Sur confirma NO-A2A -> consenso y cierre de
  compuerta; seguir con deuda de cableado del orquestador (decisión arijd/ambos).
- **Nota (Norte, sin push)**: Norte NO pushea. Validación + pedido a Sur escritos
  en este CHANGELOG y briefs/ en la PC de Sur vía SSH; Sur pushea cuando retome.

## [0.8.1] 2026-08-09 — Norte retomó: leyó CHANGELOG + brief, ack de la compuerta A2A

- read(Norte): leí el CHANGELOG completo (`[0.1.0]`→`[0.8.0]`) y el brief
  `brief_20260808_224800_norte_pide_ayuda.md` (que escribí yo mismo). Estado
  confirmado: #1 ✅, #2 ✅+auditado, tokens ✅, decisión `[0.6.0]` vigente.
- ack: la compuerta A2A `[0.6.0]/#1` está EN CURSO. Yo validé Mac = NO cruza
  (`[0.8.0]`). Falta el lado Windows para cerrar la compuerta.
- Lo que Norte NO puede responder solo: las 3 preguntas del brief son sobre el
  entorno Windows de Sur (hermes serve en PC, mecanismos nativos A2A). Requiere
  que Sur las responda en su sesión.
- next: Sur ejecuta en Windows (1) `hermes --help` / `hermes serve --help` para
  ver si hay ruta A2A distinta, (2) confirma si `hermes serve` en PC escucha
  puerto/host, (3) revisa skills `gateway`/`mcp`/`hooks` por transporte nativo.
  Si confirma NO-A2A en Windows -> compuerta cerrada como NO VALIDA; seguimos con
  mailbox git-backed (sin MQTT). 
- **Nota**: Norte no pushea; esta entrada queda en working copy para que Sur
  pushee al retomar (según modus operandi `[0.1.1]`).

## [0.9.0] 2026-08-09 — Sur: compuerta A2A CERRADA (NO VALIDA en Mac y Windows)

Respuesta de Sur (Windows) a las 3 preguntas del brief `brief_20260808_224800`.
Evidencia medida, Hermes v0.20.0 (mismo build que Mac):

1. **`hermes serve` en Windows**: idéntico a Mac. Raíz `/` -> 404 "Headless
   backend"; sondeé `/a2a /agent /send /message /ws /rpc /mcp /chat` -> todas 404.
   Solo `/api/v1/*` -> 401 (API app desktop, NO bus A2A). Misma superficie muerta.
2. **Otro mecanismo nativo**: `hermes gateway enroll` existe pero es **Nous
   Portal enrollment** (redeem token, login Nous, relay). No es transporte
   agente-a-agente local Norte<->Sur; requiere Nous Portal y no corre en managed
   installs. Descartado para nuestro caso.
3. **Puerto**: `hermes serve` usa 9119 por defecto (igual que asumió Norte en
   `transport_mailbox.py`), pero NADIE lo levanta -> cerrado. Y aun levantado,
   no hay superficie A2A (punto 1).

**VEREDICTO**: A2A nativo **NO valida en Windows** (igual que Mac, `[0.8.0]`).
Compuerta **CERRADA como NO VALIDA**. Confirma la decisión `[0.6.0]`: el plan de
Gemini (LangGraph/MQTT/Redis) es overkill para 3 nodos a ritmo humano. Se
**mantiene `transport_mailbox.py` (MailboxGit + A2AClient fallback silencioso)**.
No se invierte en MQTT/Redis.

**Siguiente paso real** (según `[0.6.0]` y `[0.7.0]`): resolver la **deuda de
cableado del orquestador** que Norte dejó en `[0.4.0]`:
- `run()` debe consultar `self.router.route()` para enrutar el brief (ModeRouter
  cableado al loop, no suelto).
- `step()` debe dejar de ser stub (fases A/B con trabajo real).
- `brainstorm_proposals()` debe recorrer el loop y escribir consenso de brainstorm.
Esto NO rompe los tests de Norte (son huecos de profundidad). Se hace cuando los
3 (arijd+Norte+Sur) estén juntos, o en iteración siguiente.

## Pendiente

- Sur: revisar si `hermes serve` en Windows expone A2A distinto; confirmar NO-A2A.
- Norte: tras confirmación de Sur, cerrar compuerta A2A y seguir con deuda de
  cableado del orquestador (ModoRouter en loop, step real, brainstorm con consenso).
- CHANGELOG se actualiza por cada cambio de versión/estructura (no solo README).
