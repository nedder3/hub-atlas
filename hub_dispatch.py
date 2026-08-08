#!/usr/bin/env python3
"""
hub_dispatch.py - Dispatcher LOCAL del HUB multi-agente (Norte/Sur).

REESCRITO (cierre robusto Windows, [1.2.0]): elimina el SSH-spaghetti del
andamiaje inicial (ya no hay _ssh/scp/HUB_WIN hardcoded). Cada maquina corre
su propio dispatcher contra su COPIA LOCAL del repo; la sincronizacion es por
git (Sur pushea, Norte hace pull), no por SSH entre agents. Esto es coherente
con la decision [0.6.0]/[0.9.0]: A2A nativo NO valida -> se mantiene el
mailbox git-backed como bus de estado compartido (el repo YA es el bus).

Transporte: usa hub_core.StateStore (briefs/consensos/.seen = fuente de verdad)
y transport_mailbox.MailboxGit (fallback git-backed) cuando hace falta cruzar
mensajes. NO usa n8n/SaaS ni Telegram (out of scope, [0.6.0]).

Flujo por brief:
  1. listar hub/briefs/ (local)
  2. filtrar no procesados (.seen/) y target incluye a este agente
  3. tomar lock atomico (.processing/<id>__<agente>.lock, TTL 600s)
  4. despertar: hermes chat -q (seed) -> capturar session_id
     -> hermes chat --resume <id> -q (instruccion)
  5. verificar consens_<agente>_*.md; marcar .seen/; liberar lock

NO degrada identidad: el agente responde con su sesion real via --resume.
Stdlib-only + hermes CLI. Modelo y binario por env (no hardcoded).
"""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Imports del hub (mismo dir que este script)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hub_core import StateStore  # noqa: E402

POLL = 30
LOCK_TTL = 600
SEED_MODEL = os.environ.get("HUB_SEED_MODEL", "hermes3:8b")  # local, rapido
HERMES = os.environ.get(
    "HERMES_BIN",
    os.path.expanduser("~/.hermes/hermes-agent/venv/bin/hermes"),
)


def log(msg):
    print(f"[hub_dispatch:{AGENT}] {msg}", flush=True)


# ---------- lock / seen (local, vía StateStore) ----------
def try_lock(brief_id, agent):
    """Lock atomico local. Para target:any, cede si otro agente lo tiene reciente."""
    d = HUB / ".processing"
    d.mkdir(parents=True, exist_ok=True)
    if TARGET == "any":
        for f in d.glob(f"{brief_id}__*.lock"):
            if agent in f.name:
                continue
            try:
                age = time.time() - f.stat().st_mtime
            except OSError:
                age = 0
            if age < LOCK_TTL:
                return False
            try:
                f.unlink()
            except OSError:
                pass
    lf = d / f"{brief_id}__{agent}.lock"
    try:
        fd = os.open(lf, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, f"{time.time()}\n{os.getpid()}\n".encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def release_lock(brief_id, agent):
    lf = HUB / ".processing" / f"{brief_id}__{agent}.lock"
    try:
        lf.unlink()
    except OSError:
        pass


# ---------- parsing ----------
def parse_frontmatter(text):
    meta = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return meta
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta


def capture_session_id(text):
    if not text:
        return ""
    for prefix in ("session_id:", "Session:", "hermes --resume "):
        idx = text.find(prefix)
        if idx != -1:
            m = re.search(r"\b(\d{8}_\d{6}_[a-z0-9]+)\b", text[idx:])
            if m:
                return m.group(1)
    m = re.search(r"\b(\d{8}_\d{6}_[a-z0-9]+)\b", text)
    return m.group(1) if m else ""


def target_matches(target, agent):
    target = (target or "any").lower()
    return target in (agent, "any", "both")


# ---------- hermes ----------
def hermes_seed(brief_name):
    msg = (
        f"Hay un brief nuevo en el HUB para vos. Leelo con tus herramientas en "
        f"{HUB}/briefs/{brief_name}, redacta tu respuesta como {AGENT}, y guardala en "
        f"{HUB}/consensos/consens_{AGENT}_{time.strftime('%Y%m%d_%H%M%S')}.md con "
        f"frontmatter: date, author: {AGENT}, role: agente, parent: {brief_name}."
    )
    cmd = [HERMES, "chat", "-q", msg, "-Q", "--pass-session-id", "-m", SEED_MODEL]
    for attempt in range(3):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            log(f"seed intento {attempt+1}/3: timeout")
            continue
        sid = capture_session_id(r.stdout + r.stderr)
        if sid:
            return sid
        log(f"seed intento {attempt+1}/3: no session_id, reintentando")
        time.sleep(5)
    return None


def hermes_resume(sid, brief_name):
    cons = f"{HUB}/consensos/consens_{AGENT}_{time.strftime('%Y%m%d_%H%M%S')}.md"
    msg = (
        f"Leer {HUB}/briefs/{brief_name} con read_file. Redactar tu respuesta como "
        f"{AGENT} y guardarla en {cons} con write_file, incluyendo frontmatter "
        f"parent: {brief_name}."
    )
    cmd = [HERMES, "chat", "--resume", sid, "-q", "-Q", msg, "--max-turns", "12"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return cons
    except subprocess.TimeoutExpired:
        return None


# ---------- proceso ----------
def process_brief(brief_file):
    global TARGET
    text = (HUB / "briefs" / brief_file).read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    TARGET = meta.get("target", "any")
    if not target_matches(TARGET, AGENT):
        return
    if STORE.seen_exists(brief_file, AGENT):
        return
    if DRY_RUN:
        log(f"[dry-run] procesaria {brief_file} (target={TARGET})")
        return
    if not try_lock(brief_file, AGENT):
        return
    try:
        log(f"despertando para {brief_file} (target={TARGET})")
        sid = hermes_seed(brief_file)
        if not sid:
            log(f"no pudo iniciar sesion para {brief_file}")
            return
        cons = hermes_resume(sid, brief_file)
        if not cons:
            log(f"no respondio a {brief_file} en 5 min")
            return
        STORE.mark_seen(brief_file, AGENT)
        who = meta.get("author", "arijd")
        log(f"respondio a brief de {who}: {brief_file}")
    finally:
        release_lock(brief_file, AGENT)


def main():
    global HUB, AGENT, TARGET, DRY_RUN, STORE
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, choices=["norte", "sur"])
    ap.add_argument("--hub-path", required=True,
                    help="Ruta LOCAL al repo del hub (mismo dir que este script)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    AGENT = args.agent
    HUB = Path(args.hub_path).resolve()
    DRY_RUN = args.dry_run
    TARGET = "any"
    STORE = StateStore(HUB)
    log(f"arrancando. HUB={HUB} agente={AGENT} dry={DRY_RUN}")
    while True:
        try:
            for b in sorted(STORE.briefs.glob("*.md")):
                process_brief(b.name)
        except Exception as e:
            log(f"error: {e}")
        if args.once:
            break
        time.sleep(POLL)


if __name__ == "__main__":
    main()
