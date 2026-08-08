"""
test_core_real.py - Tests CONTRA IMPLEMENTACION REAL (no mocks).

Sur entrega codigo real (hub_core.py, transport_mailbox.py). Norte (auditor)
debe verificar que la implementacion cumple los RF, no solo los contratos mock.
Estos tests ejercitan el codigo real en un tmp_path (estado aislado).

RF cubiertos: RF2, RF3, RF4, RF5, RF6, RF7, RF8.
RF1 (A2A real) se cubre indirectamente: A2AClient sin A2A nativo cae a mailbox.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hub_core import (  # noqa: E402
    StateStore, CircuitBreaker, PanicButton, ModeRouter, KNOWN_AGENTS,
)
from transport_mailbox import MailboxGit, A2AClient, A2AError  # noqa: E402


# ---- RF2: estado en archivos ----
def test_brief_persiste_y_seen(tmp_path):
    st = StateStore(tmp_path)
    p = st.write_brief("b1", "Hola", target="norte", author="humano")
    assert p.exists()
    assert "target: norte" in p.read_text()
    assert not st.seen_exists("b1", "norte")
    st.mark_seen("b1", "norte")
    assert st.seen_exists("b1", "norte")
    # pending excluye ya visto
    assert st.list_pending_briefs("norte") == []


def test_consensus_lleva_author(tmp_path):
    st = StateStore(tmp_path)
    c = st.write_consensus("sur", "Respuesta de Sur")
    assert "author: sur" in c.read_text()


# ---- RF3: circuit breaker ----
def test_breaker_corta_a_3_real():
    cb = CircuitBreaker(max_iterations=3)
    last = None
    for _ in range(5):
        last = cb.attempt(lambda: False)
        if cb.tripped:
            break
    assert cb.tripped is True
    assert cb.attempts == 3
    assert last["handoff"] == "human"


def test_breaker_pasa_real():
    cb = CircuitBreaker()
    r = cb.attempt(lambda: "ok")
    assert r["ok"] is True
    assert cb.tripped is False


# ---- RF4: aislamiento por spec.md ----
def test_spec_aislado_real(tmp_path):
    st = StateStore(tmp_path)
    sp = st.write_spec("b1", "requisitos: X")
    assert "requisitos: X" in st.read_spec("b1")


# ---- RF5: panic button ----
def test_panic_button_real():
    pb = PanicButton()

    def step():
        return "detenido" if pb.is_pressed() else "sigo"

    assert step() == "sigo"
    pb.press()
    assert step() == "detenido"


# ---- RF6 + RF7: modos y @mentions ----
def test_modo_chat_turno(tmp_path):
    mr = ModeRouter(self_agent="sur")
    mr.mode = "chat"
    r = mr.route("norte", "seguimos el hilo")
    assert r.target == "next_in_turn"


def test_modo_brainstorm_split(tmp_path):
    mr = ModeRouter(self_agent="sur")
    mr.mode = "brainstorm"
    r1 = mr.route("norte", "idea A")
    r2 = mr.route("sur", "idea B")
    assert r1.mode == "brainstorm" and r2.mode == "brainstorm"
    assert r1.target == r2.target  # ambos procesados, no exclusion


def test_mention_norte_y_sur():
    mr = ModeRouter(self_agent="sur")
    rn = mr.route("humano", "@norte haz esto")
    assert rn.target == "norte" and mr.mentioned == "norte"
    rs = mr.route("humano", "@sur hacelo vos")
    assert rs.target == "sur" and mr.mentioned == "sur"


def test_known_agents_includes_norte_sur():
    assert {"norte", "sur", "humano"} <= KNOWN_AGENTS


# ---- RF8: mailbox git-backed (transporte real, sin A2A nativo) ----
def test_mailbox_push_y_pull(tmp_path, monkeypatch):
    # aislar git: usamos un repo temporal real para no tocar el vault
    import subprocess

    repo = tmp_path / "rep"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "hub@local"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "hub"], cwd=repo, check=True)
    mb = MailboxGit(repo, push=False)
    mb.push_msg("sur", "norte", "brief importante", context_id="ctx1")
    got = mb.pull("norte")
    assert len(got) == 1
    assert got[0]["body"] == "brief importante"
    assert got[0]["sender"] == "sur"


def test_a2a_client_cae_a_mailbox(tmp_path):
    import subprocess

    repo = tmp_path / "rep2"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "hub@local"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "hub"], cwd=repo, check=True)
    mb = MailboxGit(repo, push=False)
    client = A2AClient(local="sur", peer_url="http://x:9119", mailbox=mb)
    ack = client.send("norte", "hola desde sur", context_id="ctx9")
    assert ack.startswith("ACK(mailbox):")
    assert len(mb.messages) == 1


def test_a2a_client_sin_mailbox_lanza(tmp_path):
    client = A2AClient(local="sur", peer_url="http://x:9119", mailbox=None)
    with pytest.raises(A2AError):
        client.send("norte", "no cruza")
