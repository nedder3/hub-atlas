"""
hub_core.py - Implementaciones REALES de los contratos del Hub (Sur, PC).

NO es mock: es funcionalidad que cumple los RF del blueprint + analisis de Sur.
Norte escribio los tests (TDD, mocks en conftest.py). Sur entrega el codigo real
que debe pasar esos contratos Y tests adicionales contra implementacion real.

RF cubiertos:
  RF2 Estado en archivos (briefs/consensos/.seen) = fuente de verdad.
  RF3 Circuit Breaker max 3 iteraciones -> handoff humano.
  RF4 Aislamiento por spec.md/archivos (no chat abierto).
  RF5 Panic Button detiene loop.
  RF6 Modos Just Chatting (1-1-1) y Brainstorming (split + elegir/re-eval/descartar).
  RF7 @mentions invocan nodo especifico.

Transporte (RF1/RF8) vive en transport_mailbox.py (A2A nativo NO existe en esta
version de Hermes -> fallback mailbox git-backed, que es el bus de estado del vault).

Diseno: transporte separado de estado (regla de arijd). Estado = archivos en el vault.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


# =====================================================================
# RF2: Estado en archivos (fuente de verdad)
# =====================================================================

class StateStore:
    """Almacen de estado del Hub: briefs/, consensos/, .seen/ en el vault.

    Es la fuente de verdad. El vault+graphify ya lo indexa => bus de estado
    compartido entre Norte y Sur sin transporte extra.
    """

    def __init__(self, hub_path: str | Path):
        self.hub = Path(hub_path).resolve()
        self.briefs = self.hub / "briefs"
        self.consensos = self.hub / "consensos"
        self.seen = self.hub / ".seen"
        for d in (self.briefs, self.consensos, self.seen):
            d.mkdir(parents=True, exist_ok=True)

    # ---- briefs ----
    def write_brief(self, brief_id: str, body: str, target: str = "any",
                    author: str = "humano") -> Path:
        p = self.briefs / f"{brief_id}.md"
        front = f"---\ntarget: {target}\nauthor: {author}\n---\n"
        p.write_text(front + body, encoding="utf-8")
        return p

    def list_pending_briefs(self, agent: str) -> list[Path]:
        out = []
        for p in sorted(self.briefs.glob("*.md")):
            if self.seen_exists(p.stem, agent):
                continue
            out.append(p)
        return out

    # ---- consensos (RF2: author obligatorio) ----
    def write_consensus(self, agent: str, body: str,
                        stamp: Optional[str] = None) -> Path:
        stamp = stamp or time.strftime("%Y%m%d_%H%M%S")
        p = self.consensos / f"consens_{agent}_{stamp}.md"
        p.write_text(f"---\nauthor: {agent}\n---\n{body}", encoding="utf-8")
        return p

    # ---- seen markers (estilo event_store append-only) ----
    def seen_exists(self, brief_id: str, agent: str) -> bool:
        return (self.seen / f"{brief_id}__{agent}").exists()

    def mark_seen(self, brief_id: str, agent: str) -> Path:
        p = self.seen / f"{brief_id}__{agent}"
        p.write_text(time.strftime("%Y%m%d_%H%M%S"), encoding="utf-8")
        return p

    # ---- RF4: spec.md como contrato aislado ----
    def write_spec(self, brief_id: str, spec: str) -> Path:
        p = self.briefs / f"{brief_id}.spec.md"
        p.write_text(spec, encoding="utf-8")
        return p

    def read_spec(self, brief_id: str) -> Optional[str]:
        p = self.briefs / f"{brief_id}.spec.md"
        return p.read_text(encoding="utf-8") if p.exists() else None


# =====================================================================
# RF3: Circuit Breaker (max 3) -> handoff humano
# =====================================================================

class CircuitBreaker:
    """Limita iteraciones del loop TDD a MAX. Si se excede, tripped -> humano."""

    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.attempts = 0
        self.tripped = False

    def attempt(self, fn: Callable[[], object]) -> dict:
        self.attempts += 1
        try:
            result = fn()
            if result is False or result is None:
                if self.attempts >= self.max_iterations:
                    self.tripped = True
                    return {"handoff": "human", "reason": "circuit_breaker_tripped"}
                return {"retry": True, "attempt": self.attempts}
            return {"ok": True, "result": result}
        except Exception:
            if self.attempts >= self.max_iterations:
                self.tripped = True
                return {"handoff": "human", "reason": "circuit_breaker_tripped"}
            return {"retry": True, "attempt": self.attempts}


# =====================================================================
# RF5: Panic Button
# =====================================================================

class PanicButton:
    """Freno de emergencia. Cuando se presiona, detiene el loop iterativo.
    También puede ser persistido mediante un archivo .panic en la raíz del HUB.
    """

    def __init__(self, hub_path: Optional[str | Path] = None):
        self._pressed = False
        self.hub_path = Path(hub_path).resolve() if hub_path else None

    def press(self) -> None:
        self._pressed = True
        if self.hub_path:
            (self.hub_path / ".panic").touch()

    def is_pressed(self) -> bool:
        if self._pressed:
            return True
        if self.hub_path and (self.hub_path / ".panic").exists():
            return True
        return False

    def reset(self) -> None:
        self._pressed = False
        if self.hub_path and (self.hub_path / ".panic").exists():
            try:
                (self.hub_path / ".panic").unlink()
            except OSError:
                pass


# =====================================================================
# RF6 + RF7: ModeRouter (modos + @mentions)
# =====================================================================

# Agentes conocidos (Norte=Mac, Sur=PC). any/both = broadcast.
KNOWN_AGENTS = {"norte", "sur", "humano", "any", "both"}


@dataclass
class RouteResult:
    target: str
    mentioned: Optional[str] = None
    mode: str = "chat"


class ModeRouter:
    """Enruta mensajes segun modo y @mentions.

    - Just Chatting (chat): turnos 1-1-1, next_in_turn por defecto.
    - Brainstorming: split, ambos agentes tiran en paralelo (no exclusion).
    - @norte / @sur fuerzan nodo especifico.
    """

    def __init__(self, self_agent: str = "sur"):
        self.mode = "chat"  # o "brainstorm"
        self.self_agent = self_agent
        self._turn = 0
        self.mentioned: Optional[str] = None

    def route(self, sender: str, message: str) -> RouteResult:
        low = message.lower()
        self.mentioned = None
        m = re.search(r"@(\w+)", low)
        if m:
            cand = m.group(1)
            if cand in KNOWN_AGENTS and cand not in ("any", "both"):
                self.mentioned = cand
                return RouteResult(target=cand, mentioned=cand, mode=self.mode)
        if self.mode == "brainstorm":
            # split: no bloquea, ambos procesan en paralelo
            return RouteResult(target="both", mode="brainstorm")
        # Just Chatting: turno por defecto 1-1-1
        self._turn += 1
        return RouteResult(target="next_in_turn", mode="chat")

    def options_brainstorm(self) -> list[str]:
        """Opciones del Draw poker: Elegir / Re-evaluar / Descartar."""
        return ["elegir", "re-evaluar", "descartar"]
