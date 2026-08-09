"""
test_dispatch.py - Tests unitarios del hub_dispatch.py (sin hermes ni SSH).
Valida: parse frontmatter, logica de target, lock local, extract_body, baseline.

ACTUALIZADO (v2): adaptado a hub_dispatch.py reescrito:
  - capture_session_id eliminado (ya no se usa seed/resume de dos pasos).
  - extract_body() testeado (nueva funcion que extrae cuerpo del brief).
  - mark_baseline() testeado.
  - try_lock y seen siguen igual.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hub_dispatch as hd
from hub_core import StateStore


def test_parse_frontmatter():
    text = "---\ndate: x\nauthor: arijd\nrole: humano\ntarget: norte\n---\ncuerpo"
    m = hd.parse_frontmatter(text)
    assert m["target"] == "norte"
    assert m["author"] == "arijd"
    # sin frontmatter
    assert hd.parse_frontmatter("hola mundo") == {}


def test_target_matches():
    assert hd.target_matches("norte", "norte")
    assert hd.target_matches("any", "norte")
    assert hd.target_matches("both", "norte")
    assert not hd.target_matches("sur", "norte")
    assert hd.target_matches(None, "norte")  # default any


def test_extract_body():
    text = "---\ndate: x\nauthor: arijd\ntarget: sur\n---\nEste es el cuerpo del brief."
    assert hd.extract_body(text) == "Este es el cuerpo del brief."
    # sin frontmatter
    assert hd.extract_body("hola mundo") == "hola mundo"
    # frontmatter vacio
    assert hd.extract_body("---\n---\ncuerpo") == "cuerpo"


def test_lock_local_atomic():
    d = Path(tempfile.mkdtemp())
    hd.HUB = d
    hd.TARGET = "any"  # global usado por try_lock para ceder a otro agente
    # primer lock ok
    assert hd.try_lock("brief_1", "norte")
    # segundo intento (mismo agente) falla (FileExists)
    assert not hd.try_lock("brief_1", "norte")
    # otro agente para target:any -> cede si lock vivo
    assert not hd.try_lock("brief_1", "sur")
    hd.release_lock("brief_1", "norte")
    # tras liberar, sur puede tomarlo
    assert hd.try_lock("brief_1", "sur")
    hd.release_lock("brief_1", "sur")


def test_seen_local():
    d = Path(tempfile.mkdtemp())
    hd.HUB = d
    store = StateStore(d)
    assert not store.seen_exists("brief_x", "norte")
    store.mark_seen("brief_x", "norte")
    assert store.seen_exists("brief_x", "norte")


def test_mark_baseline():
    d = Path(tempfile.mkdtemp())
    store = StateStore(d)
    # crear algunos briefs
    store.write_brief("brief_1", "cuerpo 1", target="sur", author="arijd")
    store.write_brief("brief_2", "cuerpo 2", target="any", author="arijd")
    # verificar que no estan marcados
    assert not store.seen_exists("brief_1.md", "sur")
    assert not store.seen_exists("brief_2.md", "sur")
    # ejecutar baseline
    hd.AGENT = "sur"
    hd.HUB = d
    hd.mark_baseline(store, "sur")
    # ahora deben estar marcados
    assert store.seen_exists("brief_1.md", "sur")
    assert store.seen_exists("brief_2.md", "sur")
    # el baseline marker debe existir
    assert (store.seen / "_baseline_sur").exists()
    # segundo llamado no vuelve a marcar (idempotente)
    hd.mark_baseline(store, "sur")  # no explota


def test_dispatch_respects_panic():
    d = Path(tempfile.mkdtemp())
    hd.HUB = d
    hd.STORE = StateStore(d)
    hd.AGENT = "sur"
    hd.DRY_RUN = False
    
    # Create brief
    hd.STORE.write_brief("brief_panic_test", "cuerpo", target="sur", author="arijd")
    assert not hd.STORE.seen_exists("brief_panic_test.md", "sur")
    
    # Enable panic file
    (d / ".panic").touch()
    
    # Try processing - should skip and not lock/seen/consensus
    hd.process_brief("brief_panic_test.md")
    
    assert not hd.STORE.seen_exists("brief_panic_test.md", "sur")
    assert list((d / "consensos").glob("consens_sur_*")) == []
    # Clean up panic file
    (d / ".panic").unlink()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"OK {name}")
    print("ALL TESTS PASSED")
