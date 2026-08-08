"""
test_integration.py — Tests de integracion del Hub (mocks, sin funcionalidad real).

RF cubiertos: RF1 (A2A cruza), RF3 (breaker en loop), RF5 (panic button),
RF6 (modos), RF8 (mailbox git fallback).
"""

import pytest
from conftest import A2AError


# ---- RF1: A2A cruza mensaje Mac<->PC sin SSH manual ----

def test_a2a_mensaje_cruza_lan(a2a_client):
    resp = a2a_client.send("sur", "hola desde norte", context_id="ctx1")
    assert resp.startswith("ACK:")
    assert len(a2a_client.sent) == 1


def test_a2a_falla_lanza_error_para_fallback(a2a_client):
    a2a_client.fail_next()
    with pytest.raises(A2AError):
        a2a_client.send("sur", "mensaje que no cruza")


# ---- RF8: mailbox git como fallback cuando A2A no cruza ----

def test_mailbox_git_fallback_cuando_a2a_falla(a2a_client, mailbox):
    a2a_client.fail_next()
    try:
        a2a_client.send("sur", "brief importante")
    except A2AError:
        # fallback: push al mailbox git-backed
        assert mailbox.push("brief importante") is True
    assert len(mailbox.messages) == 1


# ---- RF3: circuit breaker en loop TDD (A verifica -> B implementa -> itera) ----

def test_breaker_en_loop_tdd_retorna_a_humano(circuit_breaker):
    estados = []
    for _ in range(5):
        r = circuit_breaker.attempt(lambda: False)  # B siempre rompe algo
        estados.append(r)
        if circuit_breaker.tripped:
            break
    assert estados[-1]["handoff"] == "human"
    assert circuit_breaker.attempts == 3


# ---- RF5: Panic Button detiene el loop ----

def test_panic_button_detiene_loop(panic_button):
    # simula loop que chequea el boton
    def loop_step():
        if panic_button.is_pressed():
            return "detenido"
        return "sigo"
    assert loop_step() == "sigo"
    panic_button.press()
    assert loop_step() == "detenido"


# ---- RF6: modos (Just Chatting vs Brainstorming) ----

def test_modo_chat_turno_por_defecto(mode_router):
    mode_router.mode = "chat"
    r = mode_router.route("norte", "seguimos con el hilo")
    assert r["target"] == "next_in_turn"


def test_modo_brainstorm_split_no_bloquea(mode_router):
    # en brainstorm, ambos agentes tiran en paralelo; el router no bloquea
    mode_router.mode = "brainstorm"
    r1 = mode_router.route("norte", "idea A")
    r2 = mode_router.route("sur", "idea B")
    assert r1["target"] == r2["target"]  # ambos procesados, no exclusión
