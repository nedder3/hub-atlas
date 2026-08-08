"""
test_orchestrator_integration.py - Tests de INTEGRACION del orquestador (Norte, TDD).

Loop end-to-end con mocks de A2A/Mailbox. Un brief recorre A->B->A y produce
consens_<agente>_*.md con author (RF2). Brainstorm: ambos tiran propuesta en
paralelo y humano elige via options_brainstorm() (RF6). Mailbox fallback cuando
A2A no cruza (RF1/RF8).

Sur debe implementar de modo que estos tests queden en verde sin modificarlos.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hub_core import StateStore  # noqa: E402
from orchestrator import Orchestrator, TDDLetter  # noqa: E402
from transport_mailbox import MailboxGit, A2AClient  # noqa: E402

import subprocess


def _git_repo(tmp_path, name):
    repo = tmp_path / name
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "hub@local"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "hub"], cwd=repo, check=True)
    return repo


def test_loop_end_to_end_produce_consensus(tmp_path):
    """Un brief recorre A->B->A y deja consens_<agente>_*.md con author (RF2)."""
    orch = Orchestrator(hub_path=tmp_path, self_agent="norte")
    orch.state.write_brief("b1", "Construir feature", target="any", author="humano")
    # A verifica OK
    orch.verify = lambda letter: True
    result = orch.run("b1")
    # debe existir al menos un consenso escrito con author
    consensos = list((tmp_path / "consensos").glob("consens_*.md"))
    assert len(consensos) >= 1
    texto = consensos[0].read_text(encoding="utf-8")
    assert "author:" in texto


def test_tdd_roles_a_b_a(tmp_path):
    """El loop sigue A diseña/test -> B implementa -> A verifica (TDDLetter roles)."""
    orch = Orchestrator(hub_path=tmp_path, self_agent="norte")
    orch.state.write_brief("b1", "Refactor", target="any", author="humano")
    seen_roles = []

    def fake_step():
        # registrar roles en orden
        seen_roles.append(orch.current_role)
        from hub_core import PanicButton
        return {"ok": True}

    orch.step = fake_step
    orch.verify = lambda letter: True
    orch.run("b1")
    # debe haber al menos un ciclo A->B->A
    assert "A" in seen_roles and "B" in seen_roles


def test_brainstorm_ambos_proponen_y_humano_elige(tmp_path):
    """Brainstorm: A y B tiran propuesta en paralelo; humano elige (RF6)."""
    orch = Orchestrator(hub_path=tmp_path, self_agent="norte")
    orch.router.mode = "brainstorm"
    orch.state.write_brief("b1", "Idea abierta", target="any", author="humano")
    # ambos agentes deben poder emitir propuesta
    propuestas = orch.brainstorm_proposals("b1")
    assert isinstance(propuestas, dict)
    assert "norte" in propuestas and "sur" in propuestas
    # humano elige via options_brainstorm
    opciones = orch.router.options_brainstorm()
    assert opciones == ["elegir", "re-evaluar", "descartar"]


def test_mailbox_fallback_cuando_a2a_no_cruza(tmp_path):
    """Si A2A no cruza, el orquestador usa MailboxGit como transporte (RF1/RF8)."""
    repo = _git_repo(tmp_path, "mailrepo")
    mb = MailboxGit(repo, push=False)
    client = A2AClient(local="norte", peer_url="http://192.168.0.11:9119", mailbox=mb)
    orch = Orchestrator(hub_path=tmp_path, self_agent="norte", a2a=client)
    orch.state.write_brief("b1", "Mensaje a Sur", target="sur", author="humano")
    # enviar mensaje cruzando a sur via transporte
    ack = orch.send_to("sur", "brief b1 listo")
    assert ack.startswith("ACK(mailbox):")
    # el mensaje debe haber quedado en el mailbox git
    assert len(mb.messages) == 1
