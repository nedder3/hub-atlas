---
title: "Estrategia ahorro de tokens — Obsidian + Graphify + OmniRoute"
created: 2026-08-09
updated: 2026-08-09
type: estrategia
tags: [tokens, ahorro, graphify, omniroute, rag, modelo, rotacion]
aliases: [ahorro-tokens, rotacion-modelos]
source: 99-Memory/estrategia-ahorro-tokens.md (vault, indexada por graphify)
---

# Estrategia ahorro de tokens — Obsidian + Graphify + OmniRoute

> Objetivo: nunca cargar el vault completo al contexto. Usar RAG del grafo +
> rotación de modelos libres vía OmniRoute. Medido, no teorizado.

## 1. Números medidos (PC the_chorus, 2026-08-09)
- Corpus vault: **21.493 `.md` = 17.061.934 chars ≈ 4,25 M tokens**.
- `graphify query` (budget 2000): **6.735 chars ≈ 1.700 tokens** entregados.
- `graphify query` (budget 8000): 17.961 chars ≈ 4.500 tokens.
- **Ahorro RAG vs dump completo: ~1000×** (4,25M → ~2-4k por consulta).
- Chupador de espacio: `10-Projects/research` = **4,8 GB** (repo the-chorus).
- Ruido en el grafo: `research` tiene 7.780 `.rs/.py` + 20.696 `.md` mapeados
  como nodos (una query sola devolvió 37 nodos de ahí). Corregido con
  `.graphifyignore` (ver abajo).

## 2. Regla de oro (RAG, no dump)
Para cualquier pregunta sobre el vault: `graphify query "<pregunta>" --budget N`
(empieza en 2000, sube solo si corta). NUNCA leer todos los `.md` ni pegar el
vault en el prompt. El grafo ya filtra por comunidad + BFS.

## 3. Rotación de modelos (todos GRATIS, medidos en OmniRoute :20128)
OmniRoute es el proxy OpenAI-compatible (`http://localhost:20128/v1`). Cambiar
`OPENAI_MODEL` en `~/.omniroute.env` o pasar `model=` por llamada.

| Rol | Modelo | Por qué |
|---|---|---|
| RAG grafo / extracción semántica | `oc/big-pickle` | texto-only, gratis; es lo que usa graphify |
| Razonamiento pesado (sesiones largas) | `oc/deepseek-v4-flash-free` | ctx 1M, gratis, mejor que big-pickle en reasoning |
| Triage rápido / barato | `auto/fast` o `auto/cheap` | combos libres, latencia baja |
| Embeddings RAG | `gemini/gemini-embedding-2` | embedding dedicado, libre |
| Default de Hermes (este agente) | `tencent/hy3:free` | actual |

Otros libres útiles: `oc/hy3-free`, `oc/mimo-v2.5-free` (ctx 1M),
`oc/nemotron-3-ultra-free`, `oc/north-mini-code-free`, `auto/best-free`.

**Política de rotación:** sesiones de investigación/larga → `deepseek-v4-flash-free`
(ctx 1M evita fragmentar); tareas cortas de búsqueda → `auto/fast`; el grafo
siempre `big-pickle`. No quemar ctx grande en razonamiento trivial.

## 4. Mi propio contexto (Hermes)
- `hermes prompt-size --json` / `/context` miden el uso real.
- System prompt ya pesa ~25K chars + tools 70K bytes (fijo, no se puede bajar).
- Sesiones largas: usar `/compress` y RETOMAR vía nota del grafo
  (`99-Memory/hub-continuidad-sur.md`, `estrategia-ahorro-tokens.md`) en vez de
  re-pegar el chat. La memoria persistente + grafo cubren el re-arranque.

## 5. Higiene del grafo (aplicado 2026-08-09, VERIFICADO)
Problema medido: el grafo semántico (code graph `graph.json`) tenía **4151 nodos**,
**2994 (72%) venían de `10-Projects/research`** (repo the-chorus: 829 `.md` + 573 `.py`
mapeados como notas). Ruido masivo para RAG del segundo cerebro.

Fix: `.graphifyignore` excluye `.rs`, `.py`, `**/target/`, `10-Projects/research/`
(el repo del Coro NO es el vault de Atlas). Rebuild con `graphify update . --force`
(requiere `--force` porque si no, no sobreescribe al tener menos nodos).

Resultado medido: **689 nodos / 666 edges / 136 comunidades, 0 de research**
(era 4151). El RAG ahora es ~6× más compacto y sin código del Coro.
Queries confirmadas limpias: `query "the-chorus rust orchestrator"` → 0 nodos de
research; `query "OmniRoute auto-arranque"` y `query "estrategia ahorro tokens"`
→ encuentran lo útil al toque.

**Nota operativa:** `graphify update` solo reconstruye el code graph (sin LLM).
Para re-etiquetar comunidades semánticas con LLM: `graphify label . --backend openai
--model oc/big-pickle` (vía OmniRoute). El semantic cache respeta `.graphifyignore`.
