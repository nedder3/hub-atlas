"""
test_integration.py — Tests de integracion del Hub (mocks + auditoria real).

RF cubiertos: RF1 (A2A cruza), RF3 (breaker en loop), RF5 (panic button),
RF6 (modos), RF8 (mailbox git fallback).

Auditoria: los mock-tests originales asumian que A2AClient.send() lanzaba
A2AError en fallo. La implementacion real de Sur (transport_mailbox.py) hace
caida controlada a mailbox (fallback silencioso, no lanza). Esos mock-tests se
reemplazaron por test_a2a_real_* contra el codigo real. El contrato real es
fallback silencioso; documentado en PARA-NORTE-auditor-implementacion-sur.md.
"""

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from transport_mailbox import A2AClient, MailboxGit, A2AError  # noqa: E402


# ---- RF1: A2A cruza mensaje Mac<->PC sin SSH manual (mock) ----

def test_a2a_mensaje_cruza_lan(a2a_client):
    resp = a2a_client.send("sur", "hola desde norte", context_id="ctx1")
    assert resp.startswith("ACK:")
    assert len(a2a_client.sent) == 1


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
    mode_router.mode = "brainstorm"
    r1 = mode_router.route("norte", "idea A")
    r2 = mode_router.route("sur", "idea B")
    assert r1["target"] == r2["target"]  # ambos procesados, no exclusion


# ---- Auditoria: contrato real de Sur (A2AClient hace fallback silencioso) ----
# Norte (auditor) alinea el mock con la implementacion real de Sur.
# Sur eligio caida controlada a mailbox (no lanzar), documentado en su handoff.

def test_a2a_real_cae_a_mailbox_silencioso(tmp_path):
    """Auditoria: A2AClient real (Sur) cae a mailbox sin lanzar.
    Valida el contrato real, no el mock que lanzaba."""
    import subprocess

    repo = tmp_path / "rep_audit"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "hub@local"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "hub"], cwd=repo, check=True)
    mb = MailboxGit(repo, push=False)
    client = A2AClient(local="norte", peer_url="http://192.168.0.11:9119", mailbox=mb)
    ack = client.send("sur", "brief importante", context_id="ctxA")
    assert ack.startswith("ACK(mailbox):")
    assert len(mb.messages) == 1
    assert mb.messages[0]["sender"] == "norte"
    assert mb.messages[0]["recipient"] == "sur"


def test_a2a_real_sin_mailbox_lanza(tmp_path):
    """Auditoria: si no hay mailbox, A2AClient real lanza A2AError (RF1 falla)."""
    client = A2AClient(local="norte", peer_url="http://x:9119", mailbox=None)
    with pytest.raises(A2AError):
        client.send("sur", "no cruza")
