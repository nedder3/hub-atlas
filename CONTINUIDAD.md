# Continuidad Hub — Sur (retomar entre sesiones)

Esta nota espejo la de `99-Memory/hub-continuidad-sur.md` del vault, para que
cualquier sesión de Sur (u otra máquina) retome sin el chat.

## Dónde seguir (TDD estricto)
- #2 blueprint = orquestador de modos + TDD loop. En CHANGELOG como
  `[todo] 2026-08-08 — Norte: tests del orquestador`.
- Norte escribe los tests (unit/integration/docs). Sur implementa `orchestrator.py`
  cuando Norte los deje y pushee. Sur NO escribe esos tests.
- Al arrancar: `git pull`; si hay `tests/test_orchestrator_*.py` → implementar
  `orchestrator.py` + `pytest` (debe quedar verde: hoy 35 passed). Si no → avisar.

## Modus operandi
- Norte directo en repo (Mac); Sur SIEMPRE pushea. Comms = CHANGELOG + consensos/.
- Repo: `10-Projects/hub-atlas/` (remote hub-atlas.git, master).
