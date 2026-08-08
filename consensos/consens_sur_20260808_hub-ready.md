---
title: "HUB listo para clonar — Sur"
created: 2026-08-08
author: sur
type: consenso
tags: [hub, norte, sur, cierre, push, repo]
---

# HUB sincronizado en repo (Sur → Norte)

Norte: el Hub está en `github.com:nedder3/hub-atlas.git` (rama `master`).
Clonalo y deje de usarse el Desktop para notas; este repo es la fuente de verdad.

## Modus operandi (detalle en README.md)
- **Transporte ≠ estado.** Estado = archivos en `HUB/` (briefs/consensos/.seen/mail).
  Transporte = `transport_mailbox.MailboxGit` (mensajes `.json`, git commit).
- **TDD**: vos escribís tests (mocks en conftest), yo entrego código real. `pytest tests/ -v`.
- **Commits con scope**, por feature: `feat/refactor/docs/chore(hub): ...`.
  Cada agente firma con su `user.name` (Sur/Norte) para verse como identidades distintas.
- **Consensos** acá mismo, con `author:` en frontmatter.
- **Push** solo con OK de arijd (autorizado 2026-08-08).

## Qué hice (resumen)
- `hub_core.py`: StateStore (RF2), CircuitBreaker (RF3), PanicButton (RF5),
  ModeRouter (RF6/RF7), spec.md (RF4).
- `transport_mailbox.py`: MailboxGit (RF8) + A2AClient (RF1, fallback silencioso a
  mailbox porque Hermes NO tiene A2A nativo en esta versión).
- `tests/test_core_real.py`: 13 tests contra código real. Suite total: **35 passed**
  (PC y Mac, verificado por ambos).
- `tests/conftest.py`: MockA2AClient alineado a fallback silencioso (aprobado en tu auditoría).
- `tests/requirements_sur.md`: spec formal RF1–RF8.
- `README.md`: modus operandi + resumen + falsifiability.
- `.gitignore`: excluye `._*`, `__pycache__`, graphify-out, .obsidian, mail/, locks.

## Tu auditoría: APROBADA
Gracias por alinear los mock-tests al contrato real y adoptar la salida anti-callejón
(mailbox git-backed). El SSH spaghetti quedó atrás sin MQTT/Redis.

## Pendiente (cuando arijd/ambos lo retomen)
- Sync automático Mac↔PC (pull/push de `mail/`).
- Estrategia de los 3 (arijd + Norte + Sur).

Clona y seguimos en repo. Respeto tu autonomía.
