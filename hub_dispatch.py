#!/usr/bin/env python3
"""
hub_dispatch.py - Dispatcher LOCAL del HUB multi-agente (Norte/Sur).

REESCRITO v2 (2026-08-09): el dispatcher captura la respuesta de Hermes por
stdout y escribe el consenso EL MISMO via StateStore.write_consensus(), en vez
de delegar ciegamente al LLM la escritura con write_file (que fallaba porque
modelos baratos no invocan tools de forma confiable).

Transporte: usa hub_core.StateStore (briefs/consensos/.seen = fuente de verdad).
NO usa SSH, n8n/SaaS ni Telegram. Sincronizacion entre maquinas = git push/pull.

Flujo por brief:
  1. listar hub/briefs/ (local)
  2. filtrar no procesados (.seen/) y target incluye a este agente
  3. tomar lock atomico (.processing/<id>__<agente>.lock, TTL 600s)
  4. invocar: hermes chat -q "<prompt>" -Q -m <modelo> --max-turns 5
  5. capturar stdout, escribir consenso con StateStore, verificar, marcar .seen

Baseline: al primer arranque, marca todos los briefs existentes como .seen
para no reprocesar el historial. Solo procesa briefs NUEVOS despues del arranque.

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
# Modelo: tencent/hy3:free via Nous (siempre disponible, gratuito, con tool-calling).
# Override via env HUB_SEED_MODEL si se prefiere otro (e.g. auto/best-coding via OmniRoute).
SEED_MODEL = os.environ.get("HUB_SEED_MODEL", "tencent/hy3:free")


def _resolve_hermes_bin():
    """Resuelve la ruta al binario hermes en orden: ENV > ubicaciones conocidas > PATH."""
    # 1) ENV explicito
    env = os.environ.get("HERMES_BIN")
    if env and os.path.exists(env):
        return env
    # 2) ubicaciones conocidas Windows / Mac-Linux
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\hermes.exe"),
        os.path.expanduser("~/.hermes/hermes-agent/venv/bin/hermes"),
        os.path.expanduser("~/.hermes/hermes-agent/hermes"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    # 3) fallback: confiar en PATH
    return "hermes"


HERMES = _resolve_hermes_bin()


def log(msg):
    print(f"[hub_dispatch:{AGENT}] {msg}", flush=True)


# ---------- lock (local, atomico) ----------
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


def extract_body(text):
    """Extrae el cuerpo del brief (todo después del frontmatter)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text.strip()
    in_fm = True
    body_lines = []
    for ln in lines[1:]:
        if in_fm and ln.strip() == "---":
            in_fm = False
            continue
        if not in_fm:
            body_lines.append(ln)
    return "\n".join(body_lines).strip()


def target_matches(target, agent):
    target = (target or "any").lower()
    return target in (agent, "any", "both")


# ---------- hermes ----------
def invoke_hermes(brief_name, brief_body):
    """Invoca Hermes UNA sola vez con -q, captura stdout como respuesta.

    NO delega la escritura del consenso al LLM. El dispatcher captura el
    texto de respuesta y lo escribe el mismo.
    """
    prompt = (
        f"Sos {AGENT}, un agente del Atlas HUB. Hay un brief nuevo para vos.\n\n"
        f"--- BRIEF: {brief_name} ---\n"
        f"{brief_body}\n"
        f"--- FIN BRIEF ---\n\n"
        f"Leé el brief y respondé con tu análisis/respuesta. "
        f"NO uses write_file. Solo respondé en texto."
    )
    cmd = [
        HERMES, "chat",
        "-q", prompt,
        "-Q",
        "-m", SEED_MODEL,
        "--max-turns", "5",
        "--yolo",
    ]
    log(f"invocando hermes (modelo={SEED_MODEL})")
    for attempt in range(3):
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
                cwd=str(HUB),
            )
            # Hermes en modo -Q imprime la respuesta final a stdout
            response = r.stdout.strip()
            if response:
                # Limpiar líneas de session info que Hermes imprime al final
                clean_lines = []
                for line in response.splitlines():
                    # Filtrar lineas de metadata de sesion
                    if line.startswith("Session:") or line.startswith("session_id:"):
                        continue
                    if line.startswith("hermes --resume"):
                        continue
                    if line.startswith("Resume this session:"):
                        continue
                    clean_lines.append(line)
                clean = "\n".join(clean_lines).strip()
                if clean:
                    return clean
            log(f"intento {attempt+1}/3: respuesta vacia, reintentando")
            if r.stderr.strip():
                log(f"  stderr: {r.stderr.strip()[:200]}")
            time.sleep(5)
        except subprocess.TimeoutExpired:
            log(f"intento {attempt+1}/3: timeout (300s)")
            continue
    return None


# ---------- baseline de .seen ----------
def mark_baseline(store, agent):
    """Marca todos los briefs existentes como .seen al primer arranque.

    Esto evita que el dispatcher reprocese el historial completo.
    Se ejecuta solo si no existe el archivo .seen/_baseline_<agent>.
    """
    baseline_marker = store.seen / f"_baseline_{agent}"
    if baseline_marker.exists():
        return  # ya se hizo el baseline

    count = 0
    for b in sorted(store.briefs.glob("*.md")):
        if not store.seen_exists(b.name, agent):
            store.mark_seen(b.name, agent)
            count += 1
    baseline_marker.write_text(
        f"baseline {time.strftime('%Y%m%d_%H%M%S')} ({count} briefs marcados)\n",
        encoding="utf-8",
    )
    log(f"baseline: {count} briefs existentes marcados como .seen")


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
        log(f"procesando {brief_file} (target={TARGET})")
        body = extract_body(text)

        # Invocar Hermes y capturar respuesta
        response = invoke_hermes(brief_file, body)
        if not response:
            log(f"[WARN] hermes no respondio para {brief_file}")
            return

        # EL DISPATCHER escribe el consenso (no el LLM)
        who = meta.get("author", "arijd")
        consensus_body = (
            f"Respuesta de {AGENT} al brief {brief_file} (de {who}):\n\n"
            f"{response}\n\n"
            f"parent: {brief_file}"
        )
        cons_path = STORE.write_consensus(AGENT, consensus_body)

        # Verificar que el archivo realmente existe
        if cons_path.exists():
            STORE.mark_seen(brief_file, AGENT)
            log(f"[OK] consenso escrito: {cons_path.name} (brief de {who})")
        else:
            log(f"[WARN] consenso NO verificado en disco para {brief_file}")
    except Exception as e:
        log(f"[ERROR] error procesando {brief_file}: {e}")
    finally:
        release_lock(brief_file, AGENT)


def main():
    global HUB, AGENT, TARGET, DRY_RUN, STORE
    ap = argparse.ArgumentParser(
        description="Dispatcher local del HUB multi-agente Atlas."
    )
    ap.add_argument("--agent", required=True, choices=["norte", "sur"])
    ap.add_argument("--hub-path", required=True,
                    help="Ruta LOCAL al repo del hub")
    ap.add_argument("--dry-run", action="store_true",
                    help="Solo listar briefs pendientes, no procesar")
    ap.add_argument("--once", action="store_true",
                    help="Procesar una vez y salir (sin loop)")
    ap.add_argument("--skip-baseline", action="store_true",
                    help="No marcar baseline de .seen al arrancar")
    args = ap.parse_args()
    AGENT = args.agent
    HUB = Path(args.hub_path).resolve()
    DRY_RUN = args.dry_run
    TARGET = "any"
    STORE = StateStore(HUB)

    log(f"arrancando. HUB={HUB} agente={AGENT} hermes={HERMES} modelo={SEED_MODEL} dry={DRY_RUN}")

    # Baseline: marcar briefs existentes como procesados
    if not args.skip_baseline and not DRY_RUN:
        mark_baseline(STORE, AGENT)

    while True:
        try:
            for b in sorted(STORE.briefs.glob("*.md")):
                process_brief(b.name)
        except Exception as e:
            log(f"error en loop: {e}")
        if args.once:
            break
        time.sleep(POLL)


if __name__ == "__main__":
    main()
