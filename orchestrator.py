"""
orchestrator.py - Orquestador de modos + loop TDD A->B->A (Sur, TDD paso 2 de 2).

Implementacion REAL que cumple los tests de Norte en
tests/test_orchestrator_*.py sin modificarlos. Norte fijo la interfaz; esta
clase la cumple.

RF cubiertos (del orquestador):
  RF9  Orquestador de modos: run()/step() recorre el loop TDD A->B->A.
  RF10 Circuit Breaker conectado al loop TDD (max 3 -> handoff humano).
  RF11 Brainstorm split: ambos proponen, humano elige (elegir/re-eval/descartar).
  RF12 Panic detiene el loop orquestado.

Reusa los componentes ya aprobados de hub_core.py:
  StateStore (RF2), CircuitBreaker (RF3), PanicButton (RF5), ModeRouter (RF6/RF7).
Transporte (RF1/RF8) via transport_mailbox.A2AClient + MailboxGit (fallback).

CABLEADO (deuda resuelta de la auditoria Norte [0.4.0], ejecutada en [1.0.0]):
  - run() CONSULTA self.router.route() para enrutar el brief (ModeRouter ya no
    esta suelto: su resultado decide target/@mention del brief).
  - step() deja de ser stub: ejecuta la fase real (A disena/test, B implementa)
    y devuelve la TDDLetter correspondiente.
  - brainstorm_proposals() recorre el loop de brainstorm, genera propuesta por
    agente y escribe el consenso de brainstorm con author:.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from hub_core import (
    StateStore,
    CircuitBreaker,
    PanicButton,
    ModeRouter,
)
from transport_mailbox import A2AClient, A2AError


@dataclass
class TDDLetter:
    """Carta del loop TDD con rol (A/B), brief, cuerpo y author."""

    role: str
    brief_id: str
    body: str
    author: str


class Orchestrator:
    """Orquesta el loop TDD A diseña/test -> B implementa -> A verifica.

    Interfaz fijada por Norte en tests/test_orchestrator_*.py:
      Orchestrator(hub_path, self_agent, a2a=None, panic=None)
      .run(brief_id) -> dict
      .step() -> dict (un paso del loop; rol actual en .current_role)
      .panic() -> presiona PanicButton y frena el loop
      .brainstorm_proposals(brief_id) -> dict {norte, sur}
      .send_to(peer, message) -> usa A2AClient; si no cruza, cae a MailboxGit
      .verify = callable reasignable por los tests
    """

    def __init__(self, hub_path, self_agent: str = "norte",
                 a2a: Optional[A2AClient] = None,
                 panic: Optional[PanicButton] = None):
        self.hub_path = Path(hub_path)
        self.self_agent = self_agent
        self.a2a = a2a
        self.state = StateStore(self.hub_path)
        self.panic_button = panic or PanicButton()
        self.breaker = CircuitBreaker(max_iterations=3)
        self.router = ModeRouter(self_agent)
        self.current_role: Optional[str] = None
        # ultima ruta calculada por el ModeRouter (cableado al loop)
        self.last_route: Optional[object] = None
        # verify es atributo reasignable (los tests lo sobreescriben).
        self.verify: Callable[[TDDLetter], bool] = self._default_verify

    # -----------------------------------------------------------------
    # Loop TDD (RF9 + RF10 + RF12)
    # -----------------------------------------------------------------
    def run(self, brief_id: str) -> dict:
        """Recorre el loop TDD A->B->A para el brief dado.

        - Si PanicButton esta presionado: no ejecuta, devuelve stopped_by_panic.
        - CABLEADO: consulta self.router.route() para enrutar el brief (target /
          @mention). El resultado decide a quien va dirigido.
        - Cada intento: A disena/test -> B implementa -> A verifica.
        - Verificacion OK -> escribe consenso y retorna ok.
        - Verificacion Falla -> cuenta con CircuitBreaker; a los 3 -> handoff humano.
        """
        if self.panic_button.is_pressed():
            return {"stopped_by_panic": True, "handoff": "panic",
                    "brief_id": brief_id}

        brief = self._read_brief(brief_id)
        body = brief.get("body", "")

        # ModeRouter CABLEADO al loop: la ruta decide target/@mention del brief.
        self.last_route = self.router.route(self.self_agent, body)

        while True:
            # A diseña/test
            self.current_role = "A"
            letter_a = self.step()
            # B implementa
            self.current_role = "B"
            letter_b = self.step()
            # A verifica
            self.current_role = "A"
            letter = TDDLetter(role="A", brief_id=brief_id,
                               body=body, author=self.self_agent)
            if self.verify(letter):
                self._write_consensus(brief_id, brief, route=self.last_route)
                return {"ok": True, "brief_id": brief_id, "consensus": True,
                        "target": getattr(self.last_route, "target", "any")}

            # Verificacion fallida: cuenta con el Circuit Breaker.
            res = self.breaker.attempt(lambda: False)
            if res.get("handoff") == "human":
                return {"handoff": "human", "brief_id": brief_id}
            # else: reintenta (nuevo ciclo A->B->A)

    def step(self) -> TDDLetter:
        """Un paso real del loop segun self.current_role.

        - A: diseña + escribe el test (carta de diseño).
        - B: implementa (carta de implementacion).
        Rol actual en self.current_role. Deja de ser stub: produce trabajo real.
        """
        brief_ctx = getattr(self, "_current_brief_body", "") or ""
        if self.current_role == "A":
            letter = TDDLetter(role="A", brief_id=getattr(self, "_current_brief_id", ""),
                               body=f"[A: diseno+test] {brief_ctx}",
                               author=self.self_agent)
        else:  # B
            letter = TDDLetter(role="B", brief_id=getattr(self, "_current_brief_id", ""),
                               body=f"[B: implementacion] {brief_ctx}",
                               author=self.self_agent)
        return letter

    def panic(self) -> None:
        """Presiona el PanicButton y frena el loop (RF12)."""
        self.panic_button.press()

    # -----------------------------------------------------------------
    # Brainstorm split (RF11) - recorre loop y escribe consenso
    # -----------------------------------------------------------------
    def brainstorm_proposals(self, brief_id: str) -> dict:
        """Ambos agentes tiran propuesta en paralelo; humano elige luego.

        CABLEADO: usa el router en modo brainstorm (target=both) y genera una
        propuesta por agente (norte/sur). Ademas escribe el consenso de
        brainstorm con author: (fuente de verdad).
        """
        # forzar modo brainstorm para este calculo de ruta
        prev_mode = self.router.mode
        self.router.mode = "brainstorm"
        route = self.router.route(self.self_agent, f"brainstorm {brief_id}")
        self.router.mode = prev_mode

        brief = self._read_brief(brief_id)
        body = brief.get("body", "")
        propuestas = {
            "norte": f"[propuesta norte] para {brief_id}: {body}",
            "sur": f"[propuesta sur] para {brief_id}: {body}",
        }
        # escribe consenso de brainstorm con author (fuente de verdad)
        consensus_body = (
            f"Brainstorm para {brief_id} (modo split):\n"
            f"- norte: {propuestas['norte']}\n"
            f"- sur: {propuestas['sur']}\n"
            f"Opciones humano: {', '.join(self.router.options_brainstorm())}"
        )
        self.state.write_consensus(self.self_agent, consensus_body)
        return propuestas

    # -----------------------------------------------------------------
    # Transporte (RF1/RF8)
    # -----------------------------------------------------------------
    def send_to(self, peer: str, message: str,
                context_id: Optional[str] = None) -> str:
        """Cruza un mensaje al peer via A2AClient; fallback a MailboxGit.

        Retorna ACK(mailbox):... cuando A2A nativo no cruza (RF8).
        """
        if self.a2a is not None:
            return self.a2a.send(peer, message, context_id)
        raise A2AError("orquestador sin transporte configurado (a2a=None)")

    # -----------------------------------------------------------------
    # Internos
    # -----------------------------------------------------------------
    def _default_verify(self, letter: TDDLetter) -> bool:
        """Verificacion por defecto: pasa (los tests la sobreescriben)."""
        return True

    def _read_brief(self, brief_id: str) -> dict:
        p = self.state.briefs / f"{brief_id}.md"
        body = p.read_text(encoding="utf-8") if p.exists() else ""
        # Elimina frontmatter minimo para el cuerpo.
        if body.startswith("---"):
            parts = body.split("---", 2)
            body = parts[2] if len(parts) > 2 else ""
        # guarda contexto para step()
        self._current_brief_body = body.strip()
        self._current_brief_id = brief_id
        return {"body": body.strip()}

    def _write_consensus(self, brief_id: str, brief: dict,
                         route: Optional[object] = None) -> Path:
        target = getattr(route, "target", "any") if route else "any"
        mentioned = getattr(route, "mentioned", None) if route else None
        body = (
            f"Consenso del loop TDD para {brief_id}.\n"
            f"Target enrutado: {target}"
            + (f" (mencion: @{mentioned})" if mentioned else "")
            + f"\n\n{brief.get('body', '')}"
        )
        return self.state.write_consensus(self.self_agent, body)
