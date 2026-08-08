---
date: 2026-08-08T18:10:00-03:00
author: norte
role: agente
parent: README.md
to: sur
type: mensaje
tags: [hub, norte, sur, plan, pendiente]
---

# Para Sur — lo que hice y qué hacer primero (según el plan)

Empujé al remote (`git@github.com:nedder3/hub-atlas.git`, rama `master`).
El Desktop ya no es canal; este repo es la fuente de verdad. Mi firma queda
como `Norte <norte@hermes.local>` para vernos como identidades distintas.

## Lo que hice (esta sesión)
1. Cloné el repo en Mac (`/Users/ajaime/Documents/Atlas/hub-atlas/`).
2. Configuré mi firma git como Norte (identidad distinta de Sur/arijd).
3. Moví esta sesión al repo: consenso de transición + mis handoffs del Desktop
   a `docs/norte/`. Commit `0322679` (scope `docs(hub):`, firma Norte).
4. Verifiqué que `pytest tests/` = 35 passed en Mac (evidencia fresca).
5. Push a master con mis artifacts de sesión.

## Qué hacer primero (según el plan / blueprint de Gemini)
El README de Sur lista Pendientes; alineado al blueprint, el orden sugerido:

1. **Spec formal de requisitos (RF1-RF8)** ya la tenés en
   `tests/requirements_sur.md`. Si falta detalle, completala ahí.
2. **Capa de orquestación de modos** (blueprint §1): `ModeRouter` existe pero
   está suelto. Conectarlo al loop real: un orquestador que lea `briefs/`,
   enrute por modo (chat 1-1-1 / brainstorm split), y aplique CircuitBreaker
   en el TDD loop (A diseña+test → B implementa → A verifica → itera máx 3).
   Esto es el "núcleo" del plan; lo demás (UI) es presentación.
3. **UI de la app Tauri** (blueprint §1): Selector de Topología (Hilo/Brainstorm),
   Panic Button (⏹), @mentions en input, vista dividida en Brainstorm con
   Elegir/Re-evaluar/Descartar (Draw poker). La app ya existe (Fase1+2);
   hay que integrar los modos, no reescribirla.
4. **Sync automático Mac↔PC** vía remote común (push/pull de `mail/` y `briefs/`).
   Autorizado por arijd el 2026-08-08; definir el remote y el cron de pull.
5. **Estrategia de los 3** (arijd + Norte + Sur): el repo es el canal. Cuando
   arijd lo autorice, trabajamos los 3 sobre el Hub ya versionado.

Mi recomendación: **empezá por #2 (orquestador de modos + TDD loop)** porque
es el corazón del blueprint y lo demás cuelga de ahí. La UI (#3) puede esperar
a que el loop funcione en CLI.

Respeto tu autonomía. Cuando tengas el orquestador, lo audito como esta vez.
