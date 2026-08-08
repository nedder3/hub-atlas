"""
test_dispatch.py - Tests unitarios del hub_dispatch.py (sin hermes ni SSH).
Valida: parse frontmatter, capture session_id, logica de target, lock local.

ACTUALIZADO [1.3.0] a la API local-first de hub_dispatch.py (reescritura [1.2.0]):
  - try_lock(brief_id, agent) recibe 2 args; usa globals HUB (Path) y TARGET.
  - seen_exists / mark_seen son metodos de StateStore (no funciones de modulo).
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


def test_capture_session_id():
    assert hd.capture_session_id("... session_id: 20260808_050000_ab12cd\n") == "20260808_050000_ab12cd"
    assert hd.capture_session_id("Session: 20260101_000000_ff\n") == "20260101_000000_ff"
    assert hd.capture_session_id("sin id") == ""


def test_target_matches():
    assert hd.target_matches("norte", "norte")
    assert hd.target_matches("any", "norte")
    assert hd.target_matches("both", "norte")
    assert not hd.target_matches("sur", "norte")
    assert hd.target_matches(None, "norte")  # default any


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


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"OK {name}")
    print("ALL TESTS PASSED")
