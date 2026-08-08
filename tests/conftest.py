"""
conftest.py — Andamiaje de testing para el Hub (Norte/Sur).

REGLA: este archivo NO contiene funcionalidad del hub. Solo define mocks,
fixtures y contratos que los tests usan para verificar los requisitos
funcionales de Sur. La funcionalidad real la implementa Sur; estos tests
deben PASAR cuando su código esté listo (TDD).

Requisitos funcionales cubiertos (de PARA-NORTE-analisis-blueprint-hub.md de Sur):
  RF1  Transporte A2A: un mensaje real cruza Mac<->PC sin SSH manual.
  RF2  Estado en archivos: briefs/, consensos/, .seen/ = fuente de verdad.
  RF3  Circuit Breaker: maximo 3 iteraciones en TDD loop; si falla 3, retorna al humano.
  RF4  Aislamiento de contexto: comunicacion por spec.md/archivos, no chat abierto.
  RF5  Panic Button: freno de emergencia que detiene el loop iterativo.
  RF6  Modos: Just Chatting (turnos 1-1-1) y Brainstorming (split + elegir/re-eval/descartar).
  RF7  @mentions: invocar nodo especifico sin dropdown.
  RF8  Mailbox git-backed: fallback si A2A falla (patron atlas-sync).
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---- Paths ----
HUB = Path(__file__).resolve().parent.parent
HUB_WIN = "C:/Users/arijd/Documents/Atlas/HUB"  # placeholder; Sur define real


# =====================================================================
# MOCKS DE CONTRATOS (no funcionalidad: solo la interfaz que Sur debe cumplir)
# =====================================================================

class MockA2AClient:
    """Contrato: un cliente A2A que envia un mensaje a un peer y recibe respuesta.
    Sur debe implementar esta interfaz real. El mock simula el transporte."""

    def __init__(self, local="norte", peer_url="http://192.168.0.11:9900"):
        self.local = local
        self.peer_url = peer_url
        self.sent = []
        self.responses = []
        self._fail_next = False

    def send(self, peer, message, context_id=None):
        """Envia mensaje a peer. Debe cruzar la LAN sin SSH manual.
        Retorna response o lanza A2AError si no cruza."""
        self.sent.append((peer, message, context_id))
        if self._fail_next:
            self._fail_next = False
            raise A2AError("transporte no cruza (mock)")
        resp = f"ACK:{message}"
        self.responses.append(resp)
        return resp

    def fail_next(self):
        """Simula que A2A no cruza (para test de fallback a mailbox git)."""
        self._fail_next = True


class A2AError(Exception):
    pass


class MockCircuitBreaker:
    """Contrato: limita iteraciones a MAX (3). Si se excede, retorna al humano.
    Sur debe implementar el real; esto define el comportamiento esperado."""

    def __init__(self, max_iterations=3):
        self.max_iterations = max_iterations
        self.attempts = 0
        self.tripped = False

    def attempt(self, fn):
        """Ejecuta fn(); si falla y supera max, tripped=True y retorna al humano."""
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


class MockPanicButton:
    """Contrato: freno de emergencia. Cuando se activa, detiene el loop."""

    def __init__(self):
        self.pressed = False

    def press(self):
        self.pressed = True

    def is_pressed(self):
        return self.pressed


class MockModeRouter:
    """Contrato: enruta mensajes segun modo (chat/brainstorm) y @mentions."""

    def __init__(self):
        self.mode = "chat"  # o "brainstorm"
        self.mentioned = None

    def route(self, sender, message):
        if "@norte" in message.lower():
            self.mentioned = "norte"
            return {"target": "norte"}
        if "@sur" in message.lower():
            self.mentioned = "sur"
            return {"target": "sur"}
        # turno por defecto en Just Chatting: 1-1-1
        return {"target": "next_in_turn"}


class MockMailboxGit:
    """Contrato: mailbox respaldado en git (fallback si A2A falla)."""

    def __init__(self, repo_path=HUB):
        self.repo_path = repo_path
        self.messages = []

    def push(self, msg):
        self.messages.append(msg)
        # Sur debe implementar: git add + commit + (push al repo compartido)
        return True

    def pull(self):
        return self.messages


# =====================================================================
# FIXTURES
# =====================================================================

@pytest.fixture
def a2a_client():
    return MockA2AClient()


@pytest.fixture
def circuit_breaker():
    return MockCircuitBreaker(max_iterations=3)


@pytest.fixture
def panic_button():
    return MockPanicButton()


@pytest.fixture
def mode_router():
    return MockModeRouter()


@pytest.fixture
def mailbox():
    return MockMailboxGit()


@pytest.fixture
def hub_paths(tmp_path):
    """Crea estructura de archivos temporal para tests de estado (RF2)."""
    briefs = tmp_path / "briefs"
    consensos = tmp_path / "consensos"
    seen = tmp_path / "seen"
    for d in (briefs, consensos, seen):
        d.mkdir()
    return {"briefs": briefs, "consensos": consensos, "seen": seen}
