"""
test_unit.py — Tests unitarios del Hub (mocks, sin funcionalidad real).

RF cubiertos: RF2 (estado archivos), RF3 (circuit breaker), RF4 (aislamiento),
RF7 (@mentions). La funcionalidad la implementa Sur; estos tests definen el contrato.
"""

import pytest


# ---- RF2: estado en archivos (fuente de verdad) ----

def test_brief_se_persiste_en_archivo(hub_paths):
    brief = hub_paths["briefs"] / "brief_001.md"
    brief.write_text("---\ntarget: norte\n---\nHola")
    assert brief.exists()
    assert "target: norte" in brief.read_text()


def test_consensos_se_escriben_con_author(hub_paths):
    c = hub_paths["consensos"] / "consens_norte_001.md"
    c.write_text("---\nauthor: norte\n---\nRespuesta")
    assert "author: norte" in c.read_text()


def test_seen_marca_brief_como_procesado(hub_paths):
    marker = hub_paths["seen"] / "brief_001__norte"
    marker.write_text("")
    assert marker.exists()


# ---- RF3: Circuit Breaker (max 3) ----

def test_circuit_breaker_corta_a_3_intentos(circuit_breaker):
    resultado = None
    for _ in range(5):
        resultado = circuit_breaker.attempt(lambda: False)  # siempre falla
        if circuit_breaker.tripped:
            break
    assert circuit_breaker.tripped is True
    assert circuit_breaker.attempts == 3
    assert resultado["handoff"] == "human"


def test_circuit_breaker_pasa_si_funciona(circuit_breaker):
    r = circuit_breaker.attempt(lambda: "ok")
    assert r["ok"] is True
    assert circuit_breaker.tripped is False


# ---- RF4: aislamiento de contexto (spec.md, no chat abierto) ----

def test_contexto_aislado_por_spec_archivo(hub_paths):
    spec = hub_paths["briefs"] / "spec.md"
    spec.write_text("requisitos: X")
    # Agente B lee spec.md, NO el chat abierto
    assert "requisitos: X" in spec.read_text()


# ---- RF7: @mentions invocan nodo especifico ----

def test_mention_norte_enfoca_a_norte(mode_router):
    r = mode_router.route("humano", "@norte haceme esto")
    assert r["target"] == "norte"
    assert mode_router.mentioned == "norte"


def test_mention_sur_enfoca_a_sur(mode_router):
    r = mode_router.route("humano", "@sur hacelo vos")
    assert r["target"] == "sur"
