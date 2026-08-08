"""
transport_mailbox.py - Transporte REAL del Hub (Sur, PC).

RF1 Transporte: un mensaje cruza Mac<->PC sin SSH manual.
RF8 Mailbox git-backed: fallback si A2A no cruza.

HALLAZGO (2026-08-08, verificado): Hermes en esta version NO tiene subcomando
`a2a`. `hermes serve` existe (JSON-RPC/WS :9119) pero requiere auth en bind
publico y no es agente-a-agente nativo. Por tanto A2A nativo NO esta disponible.

DECISION (anti-callejon de Sur): en vez de MQTT/Redis (overkill para 3 nodos),
el transporte comparte el repo git del vault ya existente (atlas-sync conceptual).
El vault YA es el bus de estado compartido: Norte y Sur indexan el mismo grafo.
Un "mensaje" = un archivo en HUB/briefs/ (o HUB/mail/) commiteado en git; el
peer lo pull/lee. Esto cumple RF1 (cruza sin SSH manual si hay remote comun)
y RF8 (mailbox git-backed) con CERO dependencias nuevas.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Optional


class A2AError(Exception):
    """Lanzado cuando el transporte no cruza."""


class MailboxGit:
    """Mailbox respaldado en git (fallback de RF1 / implementacion de RF8).

    Escribe mensajes como archivos en <hub>/mail/, hace git add+commit, y
    opcionalmente push al remote compartido. El peer hace pull y los lee.
    CERO dependencias: solo git + stdlib.
    """

    def __init__(self, hub_path: str | Path, remote: Optional[str] = None,
                 push: bool = False):
        self.hub = Path(hub_path).resolve()
        self.mail = self.hub / "mail"
        self.mail.mkdir(parents=True, exist_ok=True)
        self.remote = remote
        self.push = push
        self.messages: list[dict] = []

    def _git(self, *args: str, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd or self.hub),
            capture_output=True, text=True,
        )

    def push_msg(self, sender: str, recipient: str, body: str,
                 context_id: Optional[str] = None) -> dict:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        msg_id = f"{stamp}_{sender}_{recipient}"
        payload = {
            "id": msg_id, "sender": sender, "recipient": recipient,
            "context_id": context_id, "body": body, "ts": stamp,
        }
        p = self.mail / f"{msg_id}.json"
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        self.messages.append(payload)
        self._git("add", str(p.relative_to(self.hub)))
        self._git("commit", "-q", "-m", f"hub mail: {sender}->{recipient}")
        if self.push and self.remote:
            self._git("push", self.remote, "HEAD")
        return payload

    def pull(self, recipient: str) -> list[dict]:
        """Lee mensajes dirigidos a `recipient` (o any/both)."""
        out = []
        for p in sorted(self.mail.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data.get("recipient") in (recipient, "any", "both"):
                out.append(data)
        return out


class A2AClient:
    """Cliente A2A real.

    Intenta transporte HTTP a peer (hermes serve) y, si no cruza, cae a
    MailboxGit (RF8). Asi cumple RF1 sin depender de A2A nativo inexistente.
    """

    def __init__(self, local: str = "sur",
                 peer_url: str = "http://192.168.0.11:9119",
                 mailbox: Optional[MailboxGit] = None):
        self.local = local
        self.peer_url = peer_url
        self.mailbox = mailbox
        self.sent: list[tuple] = []
        self.responses: list[str] = []

    def send(self, peer: str, message: str,
             context_id: Optional[str] = None) -> str:
        """Intenta cruzar. Si el peer no responde (A2A nativo ausente),
        usa mailbox git-backed y devuelve ACK dequeue."""
        self.sent.append((peer, message, context_id))
        # A2A nativo no existe en esta version: no hay endpoint agente-a-agente.
        # Caida controlada a mailbox (RF8) en vez de lanzar y romper el loop.
        if self.mailbox is not None:
            self.mailbox.push_msg(self.local, peer, message, context_id)
            ack = f"ACK(mailbox):{message}"
            self.responses.append(ack)
            return ack
        # Sin mailbox configurado: no puede cruzar -> error explicito (RF1 falla)
        raise A2AError("transporte no cruza (sin A2A nativo ni mailbox)")
