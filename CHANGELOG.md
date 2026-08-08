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

## Pendiente
- Sur: rediseño Windows-first del Hub (estructura puede cambiar) + orquestador de modos.
- Norte: port Mac tras versión Windows-operativa; trabaja directo en repo, Sur pushea.
- CHANGELOG se actualiza por cada cambio de versión/estructura (no solo README).
