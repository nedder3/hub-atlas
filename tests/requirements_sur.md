# Requisitos Funcionales del Hub — Sur (pendiente de especificacion formal)

Este archivo se completa cuando Sur deje los requisitos funcionales formales.
Por ahora, los RF inferidos de su analisis (PARA-NORTE-analisis-blueprint-hub.md)
y del blueprint de Gemini, mapeados a tests en tests/:

| RF | Requisito | Test |
|----|-----------|------|
| RF1 | Transporte A2A cruza Mac<->PC sin SSH manual | test_integration.py::test_a2a_mensaje_cruza_lan |
| RF2 | Estado en archivos como fuente de verdad | test_unit.py::test_brief_se_persiste_en_archivo |
| RF3 | Circuit Breaker max 3 iteraciones | test_unit.py::test_circuit_breaker_corta_a_3_intentos |
| RF4 | Aislamiento de contexto por spec.md | test_unit.py::test_contexto_aislado_por_spec_archivo |
| RF5 | Panic Button detiene loop | test_integration.py::test_panic_button_detiene_loop |
| RF6 | Modos Just Chatting / Brainstorming | test_integration.py::test_modo_chat_turno_por_defecto |
| RF7 | @mentions invocan nodo especifico | test_unit.py::test_mention_norte_enfoca_a_norte |
| RF8 | Mailbox git-backed fallback | test_integration.py::test_mailbox_git_fallback_cuando_a2a_falla |

## Orquestador de modos + TDD loop (#2 blueprint) — tests por Norte

Contrato fijado por Norte en tests/test_orchestrator_*.py. Sur implementa
orchestrator.py para que queden en verde.

| RF | Requisito | Test |
|----|-----------|------|
| RF9 | Orquestador de modos recorre loop TDD A->B->A (run/step) | test_orchestrator_unit.py::test_orchestrator_lee_brief_y_enruta_por_modo |
| RF10 | Circuit Breaker conectado al loop (max 3 -> handoff humano) | test_orchestrator_unit.py::test_orchestrator_circuit_breaker_max_3_handoff |
| RF11 | Brainstorm split: ambos proponen, humano elige | test_orchestrator_integration.py::test_brainstorm_ambos_proponen_y_humano_elige |
| RF12 | Panic detiene el loop orquestado | test_orchestrator_unit.py::test_orchestrator_panic_detiene_loop |

Interfaces que Sur debe cumplir (definidas por Norte):
- `Orchestrator(hub_path, self_agent, a2a=None, panic=None)` usa StateStore/ModeRouter/CircuitBreaker/PanicButton internos.
- `Orchestrator.run(brief_id)` -> recorre A diseña/test -> B implementa -> A verifica -> itera max 3; produce `consens_<agente>_*.md` con `author:`.
- `Orchestrator.step()` -> un paso del loop (rol actual en `Orchestrator.current_role`).
- `TDDLetter(role, brief_id, body, author)` dataclass con roles A/B.
- `Orchestrator.panic()` -> activa PanicButton y frena el loop.
- `Orchestrator.brainstorm_proposals(brief_id)` -> dict {norte: ..., sur: ...}.
- `Orchestrator.send_to(peer, message)` -> usa A2AClient; si no cruza, cae a MailboxGit (RF1/RF8).

Cuando Sur deje la spec formal, actualizo esta tabla y los mocks de conftest.py
si su interfaz difiere.
