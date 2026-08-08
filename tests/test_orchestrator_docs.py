"""
test_orchestrator_docs.py - Tests de DOCUMENTACION del orquestador (Norte, TDD).

Trazabilidad RF -> test del orquestador, al estilo de test_docs.py. Verifica que
cada RF del orquestador este referenciado en algun test_orchestrator_*.py y que
la tabla de requirements_sur.md se amplie con los RF del orquestador.
"""

import re
import glob
import os

# RF del orquestador (ademas de los RF2-RF8 ya cubiertos por hub_core):
#   RF9  Orquestador de modos: run()/step() recorre el loop TDD A->B->A.
#   RF10 Circuit Breaker conectado al loop TDD (max 3 -> handoff humano).
#   RF11 Brainstorm split: ambos proponen, humano elige (elegir/re-eval/descartar).
#   RF12 Panic detiene el loop orquestado.
ORCH_RF = {
    "RF9": "Orquestador de modos recorre loop TDD A->B->A",
    "RF10": "Circuit Breaker conectado al loop (max 3 -> handoff humano)",
    "RF11": "Brainstorm split: ambos proponen, humano elige",
    "RF12": "Panic detiene el loop orquestado",
}


def test_orch_rf_referenciados_en_tests():
    """Cada RF del orquestador debe aparecer en algun test_orchestrator_*.py."""
    test_files = glob.glob(
        os.path.join(os.path.dirname(__file__), "test_orchestrator_*.py")
    )
    assert test_files, "no se encontraron test_orchestrator_*.py"
    contenido = ""
    for f in test_files:
        with open(f, encoding="utf-8") as fh:
            contenido += fh.read()
    for rf in ORCH_RF:
        assert rf in contenido, f"{rf} no referenciado en tests del orquestador"


def test_requirements_ampliado_con_orch_rf():
    """requirements_sur.md debe listar los RF del orquestador (trazabilidad)."""
    req = os.path.join(os.path.dirname(__file__), "requirements_sur.md")
    with open(req, encoding="utf-8") as fh:
        txt = fh.read()
    for rf in ORCH_RF:
        assert rf in txt, f"{rf} no documentado en requirements_sur.md"
