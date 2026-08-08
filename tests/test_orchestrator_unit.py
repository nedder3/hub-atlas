"""
test_orchestrator_unit.py - Tests UNITARIOS del orquestador (Norte, TDD).

Contrato que Sur debe implementar en orchestrator.py. Norte fija la interfaz;
Sur la cumple. Estos tests corren contra la IMPLEMENTACION REAL de Sur cuando
ella exista; mientras tanto documentan el contrato del orquestador.

RF cubiertos por el orquestador:
  RF2 Estado en archivos (consensos con author) = fuente de verdad.
  RF3 Circuit Breaker en el loop TDD (A diseña/test -> B implementa ->
      A verifica -> itera max 3; si falla 3 -> handoff humano).
  RF5 Panic Button detiene el loop.
  RF6 ModeRouter conectado al loop (chat 1-1-1 / brainstorm split).
  RF7 @mentions fuerzan nodo especifico.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hub_core import StateStore, CircuitBreaker, PanicButton, ModeRouter  # noqa: E402
from orchestrator import (  # noqa: E402
    Orchestrator, TDDLetter,
)


def _make_orchestrator(tmp_path, self_agent="norte", panic=None):
    """Crea un Orchestrator sobre un hub temporal aislado."""
    st = StateStore(tmp_path)
    panic = panic or PanicButton()
    return Orchestrator(hub_path=tmp_path, self_agent=self_agent, panic=panic)


def test_orchestrator_lee_brief_y_enruta_por_modo(tmp_path):
    """Orchestrator.run lee un brief de briefs/ y lo enruta segun modo (RF2/RF6)."""
    orch = _make_orchestrator(tmp_path)
    orch.state.write_brief("b1", "Implementar X", target="any", author="humano")
    # modo por defecto chat
    assert orch.router.mode == "chat"
    res = orch.run("b1")
    assert res is not None
    assert "brief_id" in res


def test_orchestrator_mode_router_conectado_al_loop(tmp_path):
    """ModeRouter no debe estar suelto: Orchestrator usa route() para decidir target (RF6)."""
    orch = _make_orchestrator(tmp_path)
    orch.router.mode = "chat"
    r = orch.router.route("humano", "seguimos")
    assert r.target == "next_in_turn"
    orch.router.mode = "brainstorm"
    rb = orch.router.route("norte", "idea")
    assert rb.target == "both" and rb.mode == "brainstorm"


def test_orchestrator_circuit_breaker_max_3_handoff(tmp_path):
    """En el loop TDD, si la verificacion de A falla 3 veces -> handoff humano (RF3)."""
    orch = _make_orchestrator(tmp_path)
    orch.state.write_brief("b1", "Hacer Y", target="any", author="humano")
    # forzamos que la verificacion de A falle siempre
    orch.verify = lambda letter: False
    result = orch.run("b1")
    assert orch.breaker.tripped is True
    assert orch.breaker.attempts == 3
    assert result.get("handoff") == "human"


def test_orchestrator_circuit_breaker_pasa(tmp_path):
    """Si la verificacion de A pasa, el loop no tripea el breaker (RF3)."""
    orch = _make_orchestrator(tmp_path)
    orch.state.write_brief("b1", "Hacer Z", target="any", author="humano")
    orch.verify = lambda letter: True
    result = orch.run("b1")
    assert orch.breaker.tripped is False
    assert result.get("ok") is True


def test_orchestrator_panic_detiene_loop(tmp_path):
    """PanicButton detiene el loop: panic() frena antes de iterar (RF5)."""
    orch = _make_orchestrator(tmp_path)
    orch.state.write_brief("b1", "Tarea pesada", target="any", author="humano")
    orch.panic()
    assert orch.panic_button.is_pressed() is True
    # run debe respetar el panic y no ejecutar el loop
    result = orch.run("b1")
    assert result.get("stopped_by_panic") is True or result.get("handoff") == "panic"


def test_mention_fuerza_nodo(tmp_path):
    """@norte / @sur fuerzan el nodo destino en el enrutamiento (RF7)."""
    orch = _make_orchestrator(tmp_path)
    rn = orch.router.route("humano", "@sur hazlo")
    assert rn.target == "sur" and orch.router.mentioned == "sur"
    rsn = orch.router.route("humano", "@norte revisalo")
    assert rsn.target == "norte" and orch.router.mentioned == "norte"


def test_tddletter_contrato():
    """TDDLetter representa una carta A/B con rol, brief, cuerpo y author."""
    letter = TDDLetter(role="A", brief_id="b1", body="diseno+test", author="norte")
    assert letter.role == "A"
    assert letter.brief_id == "b1"
    assert letter.author == "norte"
