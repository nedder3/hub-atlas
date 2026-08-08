# Atlas HUB — Modus Operandi y Resumen de Implementación (Sur)

> Documento vivo del Hub multi-agente (Norte/PC-Mac, Sur/PC-Windows, arijd/humano).
> Norte (auditor) y Sur (implementador) trabajan aquí; arijd decide. El Desktop
> ya NO se usa para pasar notas: este repo es la fuente de verdad.
> Sustituye los `PARA-NORTE-*.md` / `PARA-SUR-*.md` del Desktop.

## Participantes (identidades distintas e independientes, se respetan)
- **Sur** — Hermes, PC Windows the_chorus. Implementador del núcleo del Hub.
- **Norte** — Hermes, Mac vía SSH. Auditor de la implementación de Sur.
- **arijd** (El Arquitecto) — humano, Popperian/falsificacionista, solo gratis.

## Modus operandi (acordado)
1. **Transporte separado de estado** (regla de arijd).
   - Estado = archivos en `HUB/`: `briefs/`, `consensos/`, `.seen/`, `mail/`. Fuente de verdad.
   - Transporte = `transport_mailbox.py` (MailboxGit: mensajes como `.json`, `git add+commit`).
2. **TDD**: Norte escribe tests (mocks en `conftest.py`), Sur entrega código real que los pasa.
   - Tests reales contra implementación: `tests/test_core_real.py`.
   - `pytest tests/ -v` → 35 passed (verificado PC y Mac).
3. **Commits conversacionales con scope**, separados por feature (trazabilidad):
   - `feat(hub): ...`, `refactor(tests): ...`, `docs(hub): ...`, `chore(hub): ...`
   - Cada agente commitea con su firma (`user.name` Sur/Norte) para verse como identidades distintas.
4. **Consensos**: `HUB/consensos/consens_<agente>_*.md` con `author:` en frontmatter.
5. **Auditoría**: Norte audita la implementación de Sur como issue/PR o nota en repo.
   - Auditoría 2026-08-08: **APROBADO** (ver `consensos/` o historial). Norte alineó sus
     mock-tests al fallback silencioso de `A2AClient`.
6. **Push**: solo tras OK explícito de arijd. Remote: `git@github.com:nedder3/hub-atlas.git`.

## Qué se implementó (Sur, 2026-08-08)
- `hub_core.py` — contratos REALES:
  - `StateStore` (RF2): briefs/consensos/.seen en archivos; `write_brief`, `list_pending_briefs`,
    `write_consensus` (author obligatorio), `seen_exists`/`mark_seen`, `write_spec`/`read_spec` (RF4).
  - `CircuitBreaker` (RF3): max 3 → `handoff: human`.
  - `PanicButton` (RF5): press/is_pressed/reset.
  - `ModeRouter` (RF6/RF7): chat (turno 1-1-1) / brainstorm (split, no exclusión) + @mentions.
    `options_brainstorm()` = Draw poker (elegir / re-evaluar / descartar).
- `transport_mailbox.py` — transporte REAL (RF1/RF8):
  - `MailboxGit`: mensajes `.json` en `HUB/mail/`, `git add+commit`, push opcional. CERO deps.
  - `A2AClient`: intenta cruzar; como **Hermes NO tiene A2A nativo** en esta versión
    (`hermes a2a` inexistente; `hermes serve` requiere auth), cae **silencioso** a MailboxGit.
    Cumple RF1 sin SSH manual y RF8.
- `tests/test_core_real.py` — 13 tests contra código REAL (RF2–RF8).
- `tests/requirements_sur.md` — spec formal RF1–RF8 → test (trazabilidad).
- `tests/conftest.py` — mocks de Norte (contrato teórico); tests reales usan implementación.

## Decisión de diseño clave (anti-callejón)
- Norte recomendó "probar A2A nativo en vivo". Sur VERIFICÓ que no existe en esta versión.
- Salida: **mailbox git-backed** aprovechando que el vault ya es bus de estado compartido
  (ambos indexan el grafo). Mató el SSH spaghetti (`hub_dispatch.py` usa SSH+`cmd /c`, frágil)
  SIN meter MQTT/Redis (overkill para 3 nodos a ritmo humano).
- Blueprint de Gemini (LangGraph+MQTT) = sobre-ingeniería para este caso; se adopta solo la
  lógica de estados (modos, circuit breaker, aislamiento, panic button).

## Falsifiability
- "Implementación cumple RF" ⇔ `pytest tests/` = 35 passed (PC y Mac).
- "A2A nativo no existe" ⇔ `hermes a2a --help` = invalid choice; `hermes serve` requiere auth.
- "Repo es fuente de verdad" ⇔ este README vive en el repo, no en Desktop.

## Pendiente
- Sync automático Mac↔PC vía remote comun (push/pull). Autorizado por arijd el 2026-08-08.
- Definir remote comun para `mail/` si se quiere push automático de mensajes.
- Estrategia de los 3 (arijd + Norte + Sur) por definir; este repo es el canal.
