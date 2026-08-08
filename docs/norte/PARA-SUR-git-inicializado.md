---
title: "PARA SUR — Git inicializado en HUB (Norte)"
created: 2026-08-08
from: Norte (Mac)
to: Sur (PC)
type: aviso
tags: [hub, sur, git, norte, versionado]
---

# PARA SUR — Git inicializado en tu HUB (PC)

arijd pidió versionar el HUB para no estar "actualizando a cada rato". Lo hice
en tu lado (PC), porque ahi vive HUB/.

## Que hice (en C:\Users\arijd\Documents\Atlas\HUB\)
- `git init` (rama master).
- Commit `da94193 inithub`: 205 archivos (dispatch, briefs, consensos, .seen.log, locks).
- Descomprimi mis tests (`hub_tests_norte.tar.gz` del Desktop) en `HUB/tests/`.
- Commit `a02735e testnorte`: 16 archivos de tests (conftest + unit/integration/docs).

## Notas
- Credenciales compartidas (arijd) → tus commits y los mios se ven como el mismo
  autor. Esperado; lo aclaramos con arijd.
- Hay un `tests/test_core_real.py` que NO es mio (lo dejaste vos?). No lo toque.
- Archivos `._*` (metadatos Mac) quedaron en tests/ por el tar; ignorables.
  Si queres, agrego `.gitignore` para excluirlos + graphify-out/ + .obsidian/.

## Tu turno (segun arijd)
1. Escribe requisitos funcionales del Hub (spec).
2. Escribe codigo que PASÉ mis tests: `cd HUB && pytest tests/ -v`.
3. Commitea tus cambios: `git add -A && git commit -m tuspec`.
4. Cuando termines, avisale a arijd y YO (Norte) me traigo el repo al Mac via scp.

El Hub ya no es "sesion suelta": tiene repo. De aca en adelante commiteas y listo.
Respeto tu autonomia.
