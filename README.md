# Atlas HUB — Bus de Coordinación Multi-Agente

> Hub multi-agente (Norte/Mac, Sur/Windows, arijd/humano).
> Estado compartido en archivos. Transporte = git. Reacción automática a briefs.

## Participantes
- **Sur** — Hermes Agent v0.20.0, PC Windows. Dispatcher local.
- **Norte** — Hermes, Mac (desactivado temporalmente, [1.4.0]). Dispatcher local.
- **arijd** (El Arquitecto) — humano, decide. Human-in-the-loop.

## Cómo funciona (v2.0.0)

```
arijd escribe brief en briefs/
        ↓
FileSystemWatcher detecta .md nuevo (hub_watcher_real.ps1)
        ↓
hub_dispatch.py --agent sur --once
        ↓
hermes chat -q "<brief>" -Q -m tencent/hy3:free
        ↓
dispatcher captura stdout de Hermes
        ↓
StateStore.write_consensus() → consensos/consens_sur_YYYYMMDD_HHMMSS.md
        ↓
StateStore.mark_seen() → .seen/brief_xxx.md__sur
```

**El dispatcher escribe el consenso él mismo** (no delega al LLM). Esto hace el
flujo determinista: si Hermes responde, el consenso se escribe.

## Estructura del repo

```
hub-atlas/
├── briefs/              # arijd (o agente) escribe pedidos aquí
├── consensos/           # agentes escriben respuestas aquí
├── .seen/               # markers de briefs procesados (append-only)
├── .processing/         # locks atómicos (TTL 600s)
├── hub_core.py          # StateStore, CircuitBreaker, PanicButton, ModeRouter
├── hub_dispatch.py      # Dispatcher local (invoca Hermes, escribe consenso)
├── orchestrator.py      # Loop TDD A→B→A (framework, no usado en dispatch)
├── transport_mailbox.py # MailboxGit + A2AClient fallback (git-backed)
├── hub_watcher_real.ps1 # FileSystemWatcher (reacción instantánea)
├── hub_watcher_task.xml # Task Scheduler XML (logon trigger)
├── normalize_seen.ps1   # Limpieza de .seen markers (one-shot)
├── config.json          # Participantes (arijd, norte, sur)
├── tests/               # 49 tests (pytest)
└── CHANGELOG.md         # Historial completo [0.1.0] → [2.0.0]
```

## Modus operandi
1. **Transporte separado de estado** (regla de arijd).
   - Estado = archivos: `briefs/`, `consensos/`, `.seen/`. Fuente de verdad.
   - Transporte = git push/pull entre máquinas.
2. **TDD**: Norte escribe tests, Sur implementa. `pytest tests/ -v` → 49 passed.
3. **Commits conversacionales** con scope: `feat(hub):`, `fix(dispatch):`, etc.
4. **Consensos**: `consensos/consens_<agente>_*.md` con `author:` en frontmatter.
5. **Push**: solo tras OK de arijd. Remote: `git@github.com:nedder3/hub-atlas.git`.

## Componentes (RF cubiertos)

| Componente | RF | Estado |
|---|---|---|
| `StateStore` (briefs/consensos/.seen) | RF2 | Sólido, 49 tests |
| `CircuitBreaker` (max 3 → handoff humano) | RF3 | Sólido |
| `PanicButton` (freno de emergencia) | RF5 | Sólido |
| `ModeRouter` (chat/brainstorm/@mentions) | RF6/RF7 | Sólido |
| `MailboxGit` (transporte git-backed) | RF1/RF8 | Sólido |
| `hub_dispatch.py` (dispatcher local) | — | **Operativo** (v2, E2E verificado) |
| `hub_watcher_real.ps1` (FileSystemWatcher) | — | **Nuevo** (v2.0.0) |

## Activar el watcher automático

```powershell
# Importar tarea en Task Scheduler (se activa al login)
schtasks /create /xml hub_watcher_task.xml /tn AtlasHubWatcher

# O correr manualmente
powershell -ExecutionPolicy Bypass -File hub_watcher_real.ps1
```

## Probar manualmente

```bash
# Crear brief de prueba
python -c "
from hub_core import StateStore
s = StateStore('.')
s.write_brief('test_manual', 'Respondé con una línea.', target='sur', author='arijd')
"

# Correr dispatcher una vez
python hub_dispatch.py --agent sur --hub-path . --once --skip-baseline

# Verificar consenso
dir consensos\consens_sur_*.md
```

## Decisiones de diseño
- **A2A nativo NO existe** en Hermes v0.20.0 → mailbox git-backed ([0.8.0]/[0.9.0]).
- **MQTT/Redis descartado** como overkill para 3 nodos a ritmo humano.
- **Port Mac Tauri CANCELADO** por arijd ([1.4.0]). Alcance = 100% Windows.
- **Modelo default**: `tencent/hy3:free` via Nous (gratuito). Override: `HUB_SEED_MODEL`.

## Mac/Norte (cuando se reactive)
Norte no necesita SSH. Clona el repo, corre su dispatcher local, git push/pull.
**Git es el bus.**
