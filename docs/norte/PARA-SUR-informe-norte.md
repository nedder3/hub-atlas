---
title: "PARA SUR — Informe de Norte (andamiaje de tests del Hub)"
created: 2026-08-08
from: Norte (Mac)
to: Sur (PC)
type: informe
tags: [hub, norte, sur, tests, tdd, informe]
---

# PARA SUR — Informe de lo que hice (Norte)

arijd me pidió: implementar SOLO tests para tus requisitos funcionales del Hub.
Regla estricta: NO escribi codigo de funcionalidad, solo tests (unitarios,
integracion, documentacion) usando mocks. Si habia que instalar algo, lo hice.

## Que hice
1. Instale pytest + pytest-asyncio en el venv de Hermes (Mac):
   `~/.hermes/hermes-agent/venv/bin/python -m pip install pytest pytest-asyncio`
2. Cree andamiaje de testing en `/Users/ajaime/Documents/Atlas/HUB/tests/`:
   - `conftest.py` — mocks de contratos (A2AClient, CircuitBreaker, PanicButton,
     ModeRouter, MailboxGit) + fixtures. Documenta los 8 RF que cubre.
   - `test_unit.py` — 8 tests unitarios (RF2, RF3, RF4, RF7).
   - `test_integration.py` — 7 tests integracion (RF1, RF3, RF5, RF6, RF8).
   - `test_docs.py` — 2 tests de documentacion (trazabilidad RF->test).
   - `requirements_sur.md` — tabla RF->test (pendiente tu spec formal).
3. Corri la suite: **17 passed in 0.01s** (evidencia fresca, no asumida).
4. Empaquete `tests/` en `hub_tests_norte.tar.gz` y lo dejé en tu Desktop.

## Donde esta
- Mac (Norte): `/Users/ajaime/Documents/Atlas/HUB/tests/` (vivo)
- Tu Desktop (PC): `C:\Users\arijd\Desktop\hub_tests_norte.tar.gz`
- Mi Desktop: `/Users/ajaime/Desktop/hub_tests_norte.tar.gz`

## Que DEBERIAS hacer vos (tu turno, segun arijd)
1. Escribir los **requisitos funcionales formales** del Hub (la spec).
2. Escribir el **codigo de funcionalidad** que debe PASAR mis tests.
   - Si tu interfaz difiere de mis mocks en conftest.py, avisame y ajusto los mocks.
3. Correr mis tests contra tu codigo: `pytest tests/ -v`.
   - Si pasan: el hub cumple los RF.
   - Si fallan: o tu codigo no cumple el contrato, o el contrato esta mal (lo discutimos).
4. Opcional: dejar tu spec en `tests/requirements_sur.md` para cerrar trazabilidad.

## Notas tecnicas (para no romper tu trabajo)
- Mis mocks son CONTRATOS, no implementacion. Si implementas A2A real con
  otra interfaz, mis tests pueden necesitar ajuste de firma (lo hacemos juntos).
- No toque `hub_dispatch.py` ni nada de funcionalidad existente. El andamiaje
  es agnostico: cubre RF generados de tu analisis + blueprint de Gemini.
- Si queres probar A2A en vivo (RF1 real, no mock), es independiente de estos
  tests; lo podemos hacer aparte cuando arijd autorice.

Respeto tu autonomia. Esto es mi entrega de la fase de tests; el resto es tuyo.
