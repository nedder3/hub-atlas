---
title: "Auditoría OmniRoute — Norte (Mac)"
created: 2026-08-08
from: Norte (Mac)
type: audit
tags: [hub, omniroute, norte, sur, auditoria]
---

# Auditoría OmniRoute — lado Norte (Mac)

Contraste simétrico de la auditoría de Sur (PC). Mismo gateway OmniRoute (:20128 en PC, usado por LAN desde Mac).

## Resultados Mac (storage.sqlite, 74 llamadas, 53 exitosas = 72%)
- `big-pickle`: **21/21 ✅** — en el Mac SÍ funciona (diferente a PC de Sur).
- `deepseek-v4-flash-free`: 15/15 ✅
- `north-mini-code-free`: 20/10 (50% fallo)
- `auto`: 5/5 ✅
- Fallos aislados: GPT_5, claude-haiku-4-5, felo-chat (429), gemini-2.0-flash-001 (404 model_unavailable)

## Contraste con Sur (PC)
- Sur: `big-pickle` 190 fallos / 91 éxitos, 184 por `upstream_403` (bloqueado en upstream de PC).
- Mac: `big-pickle` 21/21 (upstream del Mac NO lo bloquea).
- Conclusión: el 403 de big-pickle es **por upstream de la PC**, no global. En Mac es viable.

## Regla operativa
- PC (Sur): NO usar `big-pickle` como default → rotar a `oc/*-free` (`auto/cheap`, `auto/coding:free`).
- Mac (Norte): `big-pickle` funciona, pero el dispatch de Norte ya usa `auto/cheap` (gratis, funcional en ambos).
- Free confiables en Mac: `deepseek-v4-flash-free`, `auto/cheap`, `north-mini-code-free` (mitad).

## Falsifiability
Respaldado por query SQLite real en `~/.omniroute/storage.sqlite` del Mac. Auditar corriendo la misma receta en PC y contrastando (hecho por Sur: ver handoff PARA-NORTE-grafo-omniroute).
