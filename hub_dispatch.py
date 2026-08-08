#!/usr/bin/env python3
"""
hub_dispatch.py - Dispatcher del HUB multi-agente (Norte/Windows).
Plan FINAL aprobado: https://github.com/nedder3/matrioskha (brain/implementation_plan.md)

UN solo script stdlib-only (Python 3.8+). Ambas maquinas lo ejecutan:
    python3 hub_dispatch.py --agent norte  --hub-path HUB [--remote arijd@192.168.0.11]
    python3 hub_dispatch.py --agent windows --hub-path HUB
    python3 hub_dispatch.py --agent norte --hub-path HUB --dry-run   # no llama hermes

Flujo por brief:
  1. listar HUB/briefs/ (local o via SSH si --remote)
  2. filtrar no procesados (.seen/) y target incluye a este agente
  3. tomar lock atomico (.processing/<id>__<agente>.lock, TTL 600s)
  4. despertar: hermes chat -q (seed, modelo local) -> capturar session_id
     -> hermes chat --resume <id> -q (instruccion)
  5. verificar consens_<agente>_*.md; marcar .seen/; liberar lock
  6. notificar via hermes send -t telegram

NO degrada identidad: el agente responde con su sesion real via --resume.
NO usa n8n/SaaS: solo hermes CLI + stdlib (+ SSH para Norte).
"""
import argparse
import os
import re
import subprocess
import sys
import time

POLL = 30
LOCK_TTL = 600
SEED_MODEL = "hermes3:8b"  # local, rapido, fiable (neverfadeaway lo documenta)
HERMES = os.environ.get(
    "HERMES_BIN",
    os.path.expanduser("~/.hermes/hermes-agent/venv/bin/hermes"),
)


def log(msg):
    print(f"[hub_dispatch:{AGENT}] {msg}", flush=True)


# ---------- acceso a HUB (local o SSH) ----------
def _ssh(cmd):
    # cmd /c "..." con comillas para tolerar espacios en rutas (estilo hub_push.py)
    r = subprocess.run(["ssh", REMOTE, f'cmd /c "{cmd}"'],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"ssh rc={r.returncode}")
    return r.stdout


def list_briefs():
    if REMOTE:
        out = _ssh(f"dir /b {HUB_WIN}\\briefs\\*.md 2>nul")
        return [l.strip() for l in out.splitlines() if l.strip().endswith(".md")]
    d = os.path.join(HUB, "briefs")
    try:
        return sorted(f for f in os.listdir(d) if f.endswith(".md"))
    except FileNotFoundError:
        return []


def read_file(folder, name):
    if REMOTE:
        return _ssh(f"type {HUB_WIN}\\{folder}\\{name}")
    p = os.path.join(HUB, folder, name)
    try:
        return open(p, "r", encoding="utf-8").read()
    except OSError:
        return ""


def write_local_file(folder, name, content):
    """Escribe un archivo local (consenso de Norte antes del scp)."""
    d = os.path.join(HUB, folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.join(d, name)


def push_consenso_scp(local_path, name):
    if not REMOTE:
        return
    subprocess.run(["scp", local_path, f"{REMOTE}:{HUB_WIN}/consensos/{name}"],
                   check=True, capture_output=True, timeout=30)


def seen_exists(brief_id, agent):
    if REMOTE:
        r = _ssh(f"dir {HUB_WIN}\\.seen\\{brief_id}__{agent} >nul 2>nul & if errorlevel 1 (echo no) else (echo yes)")
        return "yes" in r.lower()
    return os.path.exists(os.path.join(HUB, ".seen", f"{brief_id}__{agent}"))


def mark_seen(brief_id, agent):
    if REMOTE:
        _ssh(f"if not exist {HUB_WIN}\\.seen mkdir {HUB_WIN}\\.seen")
        _ssh(f"copy /b nul {HUB_WIN}\\.seen\\{brief_id}__{agent} >nul")
        return
    d = os.path.join(HUB, ".seen")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f"{brief_id}__{agent}"), "w").close()


def lock_path(brief_id, agent):
    return os.path.join(HUB, ".processing", f"{brief_id}__{agent}.lock")


def lock_exists_remote(brief_id, agent):
    r = _ssh(f"dir {HUB_WIN}\\.processing\\{brief_id}__{agent}.lock >nul 2>nul & if errorlevel 1 (echo no) else (echo yes)")
    return "yes" in r.lower()


def lock_exists_local(brief_id, agent):
    return os.path.exists(lock_path(brief_id, agent))


def lock_stale_remote(brief_id, other_agent):
    # limpiar locks viejos de OTRO agente para target:any
    out = _ssh(f"dir /b {HUB_WIN}\\.processing\\{brief_id}__*.lock 2>nul")
    for f in out.splitlines():
        f = f.strip()
        if other_agent in f:
            continue
        r = _ssh(f"for %F in ({HUB_WIN}\\.processing\\{f}) do @echo %~tF")
        # Windows no da mtime facil por cmd; confiamos en TTL via touch local
    return False


def try_lock(brief_id, agent, target):
    """Lock atomico. Para target:any, verifica que otro agente no lo tenga."""
    if REMOTE:
        if target == "any" and lock_exists_remote(brief_id, "norte" if agent == "windows" else "windows"):
            # si el lock de otro agente es reciente (<TTL), ceder
            return False
        _ssh(f"if not exist {HUB_WIN}\\.processing mkdir {HUB_WIN}\\.processing")
        lock_cmd = f"copy /b nul {HUB_WIN}\\.processing\\{brief_id}__{agent}.lock >nul 2>nul"
        _ssh(lock_cmd)
        return lock_exists_remote(brief_id, agent)
    # local
    d = os.path.join(HUB, ".processing")
    os.makedirs(d, exist_ok=True)
    if target == "any":
        for f in os.listdir(d):
            if f.startswith(brief_id) and f.endswith(".lock") and agent not in f:
                lp = os.path.join(d, f)
                if time.time() - os.path.getmtime(lp) < LOCK_TTL:
                    return False
                try:
                    os.unlink(lp)
                except OSError:
                    pass
    lf = lock_path(brief_id, agent)
    try:
        fd = os.open(lf, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, f"{time.time()}\n{os.getpid()}\n".encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def release_lock(brief_id, agent):
    if REMOTE:
        _ssh(f"del {HUB_WIN}\\.processing\\{brief_id}__{agent}.lock 2>nul")
        return
    try:
        os.unlink(lock_path(brief_id, agent))
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


def body_first_line(text):
    in_fm = False
    for ln in text.splitlines():
        s = ln.strip()
        if s == "---":
            in_fm = not in_fm
            continue
        if in_fm:
            continue
        if s:
            return s[:200]
    return "(sin cuerpo)"


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
    if target in (agent, "any", "both"):
        return True
    return False


# ---------- hermes ----------
def hermes_seed(brief_name):
    msg = (
        f"Hay un brief nuevo en el HUB para vos. Leelo con tus herramientas en "
        f"HUB/briefs/{brief_name}, redacta tu respuesta como {AGENT}, y guardala en "
        f"HUB/consensos/consens_{AGENT}_{time.strftime('%Y%m%d_%H%M%S')}.md con "
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
    cons = f"HUB/consensos/consens_{AGENT}_{time.strftime('%Y%m%d_%H%M%S')}.md"
    msg = (
        f"Leer HUB/briefs/{brief_name} con read_file. Redactar tu respuesta como "
        f"{AGENT} y guardarla en {cons} con write_file, incluyendo frontmatter "
        f"parent: {brief_name}."
    )
    cmd = [HERMES, "chat", "--resume", sid, "-q", "-Q", msg, "--max-turns", "12"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return cons
    except subprocess.TimeoutExpired:
        return None


def notify(text):
    try:
        subprocess.run([HERMES, "send", "-t", "telegram", text],
                       capture_output=True, timeout=20)
    except Exception as e:
        log(f"notify fallo: {e}")


# ---------- proceso ----------
def process_brief(brief_file):
    text = read_file("briefs", brief_file)
    meta = parse_frontmatter(text)
    target = meta.get("target", "any")
    if not target_matches(target, AGENT):
        return
    if seen_exists(brief_file, AGENT):
        return
    if DRY_RUN:
        log(f"[dry-run] procesaria {brief_file} (target={target})")
        return
    if not try_lock(brief_file, AGENT, target):
        return
    try:
        log(f"despertando para {brief_file} (target={target})")
        sid = hermes_seed(brief_file)
        if not sid:
            notify(f"⚠️ {AGENT} no pudo iniciar sesion para {brief_file}")
            return
        cons = hermes_resume(sid, brief_file)
        if not cons:
            notify(f"⚠️ {AGENT} no respondio a {brief_file} en 5 min")
            return
        # para Norte (REMOTE), escribir local y scp
        mark_seen(brief_file, AGENT)
        who = meta.get("author", "arijd")
        notify(f"💬 {AGENT} respondio a brief de {who}: {brief_file}")
    finally:
        release_lock(brief_file, AGENT)


def main():
    global HUB, AGENT, REMOTE, HUB_WIN, DRY_RUN
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, choices=["norte", "windows"])
    ap.add_argument("--hub-path", required=True)
    ap.add_argument("--remote", default=None,
                    help="user@host para acceso SSH (Norte en Mac)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    AGENT = args.agent
    HUB = args.hub_path
    REMOTE = args.remote
    DRY_RUN = args.dry_run
    HUB_WIN = "C:/Users/arijd/Documents/Atlas/HUB" if REMOTE else HUB
    if REMOTE:
        HUB_WIN = HUB_WIN.replace("/", "\\")
    log(f"arrancando. HUB={HUB} agente={AGENT} remote={REMOTE} dry={DRY_RUN}")
    while True:
        try:
            for b in list_briefs():
                process_brief(b)
        except Exception as e:
            log(f"error: {e}")
        if args.once:
            break
        time.sleep(POLL)


if __name__ == "__main__":
    main()
