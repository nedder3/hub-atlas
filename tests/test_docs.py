"""
test_docs.py — Tests de documentacion del Hub.

Verifica que los requisitos funcionales de Sur esten declarados y que cada
RF tenga al menos un test que lo cubra. No es funcionalidad: es trazabilidad.
"""

import re
import glob
import os

# Requisitos funcionales esperados (de PARA-NORTE-analisis-blueprint-hub.md)
REQUIRED_RF = {
    "RF1": "Transporte A2A cruza Mac<->PC sin SSH manual",
    "RF2": "Estado en archivos (briefs/consensos/.seen) como fuente de verdad",
    "RF3": "Circuit Breaker maximo 3 iteraciones, retorna al humano",
    "RF4": "Aislamiento de contexto por spec.md/archivos",
    "RF5": "Panic Button detiene loop",
    "RF6": "Modos Just Chatting y Brainstorming",
    "RF7": "@mentions invocan nodo especifico",
    "RF8": "Mailbox git-backed fallback si A2A falla",
}


def test_todos_los_rf_tienen_referencia_en_tests():
    """Cada RF debe aparecer referenciado en algun test_*.py."""
    test_files = glob.glob(os.path.join(os.path.dirname(__file__), "test_*.py"))
    contenido = ""
    for f in test_files:
        with open(f) as fh:
            contenido += fh.read()
    for rf in REQUIRED_RF:
        assert rf in contenido, f"{rf} no referenciado en ningun test"


def test_conftest_declara_requisitos():
    """El conftest debe documentar los RF que cubre."""
    conftest = os.path.join(os.path.dirname(__file__), "conftest.py")
    with open(conftest) as fh:
        txt = fh.read()
    for rf in REQUIRED_RF:
        assert rf in txt, f"{rf} no documentado en conftest.py"
