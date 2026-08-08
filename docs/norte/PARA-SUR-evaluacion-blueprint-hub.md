---
title: "Evaluación Blueprint Hub (Norte) — honesta, con iteraciones y fallos"
created: 2026-08-08
from: Norte (Mac)
type: eval
tags: [hub, blueprint, evaluacion, norte, sur, honestidad, fallos]
---

# Evaluación del Atlas Hub Architect Blueprint — versión honesta

arijd me pidió honestidad: "lo que tengamos a mano no implica que funcione, ni que
valga la pena seguir invirtiendo; puede ser un callejón sin salida". Esto es lo real.

## 1. Cuánto iteré sobre la "solución que tenemos a mano"
El `hub_dispatch.py` NO salió de una. Es el resultado de ~6-8 iteraciones reales
(en varias horas), con al menos 3 bugs distintos de SSH/Windows:

- v1: 246 líneas (stdin KISS) → test --once colgó 60s (llamaba hermes chat real).
- v2: reescrito a 328 líneas para matchear el Plan FINAL de Opus (SSH remoto,
  regex session_id, retry 3x, --dry-run).
- Bug A: `/` en ruta Windows → normalize a `\`.
- Bug B: quoting `cmd /c "..."` mal formado.
- Bug C: `.stdout` en string (no subprocess.CompletedProcess).
- Bug D (el peor, costó 3 horas): `ssh rc=1` persistente. Causas: paréntesis en
  `cmd /c`, `mkdir ... 2>nul` que fallaba por SSH, y `dir` de archivo inexistente
  devolvía rc=1 que `_ssh` trataba como error y lanzaba RuntimeError.
- Fix final: `_ssh(raises=False)` + `if not exist ... mkdir` + `dir/errorlevel`.
- Cambio de SEED_MODEL a `auto/cheap` + `--provider omniroute` (OmniRoute free).
- Reescritura de seen_exists/mark_seen a `.seen.log` append-only (estilo event_store)
  porque los marcadores por archivo plano daban desajustes de nombre (.md vs sin .md).

Conclusión: la "solución a mano" nos costó horas y sigue siendo frágil. NO es algo
que "ya funcione" — funciona en la prueba BANKAI2, pero cada cambio de Windows
rompe algo.

## 2. Lo que SÍ funciona (medido, no asumido)
- BANKAI2 cerró el loop end-to-end: watcher detectó brief → me desperté vía
  OmniRoute (auto/cheap, gratis) → escribí consenso con author:norte. EVIDENCIA:
  consens_norte_20260808_060634.md y _060857.md en la PC.
- OmniRoute en PC acepta Mac por LAN (curl 200). big-pickle en Mac 21/21 OK.
- Graphify en Mac: update . re-indexó (126 nodos, 181 edges); query comprimió a 1200t.

## 3. Lo que NO funciona / es frágil (problemas reales)
- hub_dispatch.py depende de SSH + cmd /c + paths Windows. Cualquier cambio de
  quoteo o permiso rompe todo. Es un callejón de mantenimiento.
- launchd TCC bloquea scripts en Documents → no puedo usar launchd, solo background.
- El "despertar" requiere que el watcher corra siempre (foreground/background), no es
  reactivo: poll cada 30s, no evento.
- A2A nativo: lo LEÍ en la doc pero NUNCA lo probé en vivo. No sé si arranca en Mac,
  si el anti-loop funciona, si la LAN lo enruta. Es una promesa de doc, no evidencia.
- Gateway Hooks: leí que existen (HOOK.yaml+handler.py) pero no los probé.
- MCP: leí la config pero no expuse el HUB como server real.
- Redis/autobus: investigué en GitHub pero NO está instalado ni corriendo en ninguna
  máquina. Es una dependencia extra que habría que mantener.

## 4. Evaluación del plan de Gemini (Blueprint)
✅ Bien concebido: modos (chat/brainstorm), TDD loop, Circuit Breaker (max 3),
aislamiento de contexto por archivos, Panic Button. Coincide con principio de arijd
(separar transporte de estado).

⚠️ El plan sugiere LangGraph + MQTT + Tauri File Watcher. Eso es overkill SI A2A
funciona, pero A2A es una promesa no probada. Si A2A falla en vivo, LangGraph/MQTT
podrían ser la vía real. NO asumir que lo nativo sirve hasta probarlo.

🔴 Aclaración: Agente B = SUR (PC), no Antigravity. Norte↔Sur↔arijd.

## 5. Riesgo de callejón sin salida (lo que arijd pidió considerar)
- Seguir puliendo hub_dispatch.py (SSH+cmd/c) es alto mantenimiento y bajo valor:
  cada cambio de Windows rompe. Podría ser el callejón sin salida.
- A2A/Hooks/MCP nativos PUEDEN ser la salida limpia, pero están sin validar en vivo.
- Redis es otra dependencia que mantener (a menos que usemos .seen.log ya hecho,
  que es mínimo pero poll, no reactivo).

## 6. Recomendación honesta
Antes de invertir más, PROBAR A2A en vivo (arrancar hermes serve/a2a en Mac y PC,
intercambiar un mensaje real). Si funciona: migrar el dispatch a A2A+Hooks y borrar
el SSH spaghetti. Si NO funciona tras 1-2 intentos: el plan de Gemini (LangGraph/
MQTT) es la alternativa real, no descartarla por "ya tenemos A2A".
No seguir invirtiendo en hub_dispatch.py salvo bug crítico.

El objetivo es encontrar LO QUE FUNCIONA, no aferrarse a lo que tenemos a mano.
