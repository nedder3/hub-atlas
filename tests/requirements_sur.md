# Requisitos Funcionales del Hub — Sur (spec formal)

> Sur (PC, the_chorus). Norte dejó el andamiaje de tests (TDD): él los escribió,
> yo entrego la spec formal + cierro trazabilidad. Respeto su autonomía: no toco
> su andamiaje salvo que el contrato difiera (ver "Desajustes").

## Decisiones de diseño (Sur, desde PARA-NORTE-analisis-blueprint-hub.md)
- **Transporte**: A2A nativo de Hermes PRIMERO (RF1). Si no cruza en vivo, fallback
  a mailbox git-backed (RF8). NO LangGraph/MQTT (overkill para 3 nodos a ritmo humano).
- **Estado**: archivos = fuente de verdad (RF2). `briefs/`, `consensos/`, `.seen/`.
  El vault+graphify ya es bus de estado compartido (ambos indexan `consensos/`).
- **Circuit Breaker**: max 3 (RF3). Si falla 3 → handoff al humano. Obligatorio.
- **Aislamiento**: comunicación por `spec.md`/archivos, no chat abierto (RF4).
- **Panic Button**: freno de emergencia que detiene el loop iterativo (RF5).
- **Modos**: Just Chatting (turnos 1-1-1) y Brainstorming (split + elegir/re-eval/descartar) (RF6).
- **@mentions**: invocar nodo específico sin dropdown (RF7). Norte=A, Sur=B.

## Tabla RF → test (trazabilidad, cierra test_docs.py)

| RF | Requisito | Test | Estado (PC Sur, 2026-08-08) |
|----|-----------|------|------------------------------|
| RF1 | Transporte A2A cruza Mac<->PC sin SSH manual | test_integration.py::test_a2a_mensaje_cruza_lan | MOCK pasa; A2A real PENDIENTE probar en vivo |
| RF2 | Estado en archivos como fuente de verdad | test_unit.py::test_brief_se_persiste_en_archivo | PASS (mock) |
| RF3 | Circuit Breaker max 3 iteraciones | test_unit.py::test_circuit_breaker_corta_a_3_intentos | PASS (mock) |
| RF4 | Aislamiento de contexto por spec.md | test_unit.py::test_contexto_aislado_por_spec_archivo | PASS (mock) |
| RF5 | Panic Button detiene loop | test_integration.py::test_panic_button_detiene_loop | PASS (mock) |
| RF6 | Modos Just Chatting / Brainstorming | test_integration.py::test_modo_chat_turno_por_defecto | PASS (mock) |
| RF7 | @mentions invocan nodo especifico | test_unit.py::test_mention_norte_enfoca_a_norte | PASS (mock) |
| RF8 | Mailbox git-backed fallback | test_integration.py::test_mailbox_git_fallback_cuando_a2a_falla | PASS (mock) |

## Evidencia de ejecución (Sur, PC)
- `pytest HUB/tests/ -v` → **22 passed** (17 mocks + 5 test_dispatch contra hub_dispatch.py real de Norte).
- pytest instalado en venv graphifyy (no toqué el sistema).
- Los 5 `test_dispatch.py` pasan contra el `hub_dispatch.py` real → el contrato
  HUB/REMOTE como globals mutables SÍ se cumple en la implementación de Norte.

## Desajustes de contrato (para discutir con Norte, no bloquea)
- `test_dispatch.py` asume `hd.HUB` / `hd.REMOTE` como globals mutables. En
  `hub_dispatch.py` real parecen resolverse por argumento/CLI; sin embargo los
  tests pasan, así que el script los expone como globals en algún punto (main).
  No lo modifico: es código de Norte y respeta su identidad.
- RF1 (A2A real) sigue sin probar en vivo (Norte lo admitió; yo lo propuse primero).
  Es la única incógnita real. Cuando arijd autorice, probamos `hermes serve/a2a`
  Mac<->PC y medimos si cruza. Eso decide si tiramos el SSH spaghetti.

## Falsifiability
- "Tests cumplen RF" ⇔ `pytest HUB/tests/` = 22 passed (verificado arriba).
- "A2A funciona" ⇔ un mensaje real cruza Mac<->PC sin SSH manual (PENDIENTE).
