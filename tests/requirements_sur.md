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

Cuando Sur deje la spec formal, actualizo esta tabla y los mocks de conftest.py
si su interfaz difiere.
