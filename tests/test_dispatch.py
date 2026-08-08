"""
test_dispatch.py - Tests unitarios del hub_dispatch.py (sin hermes ni SSH).
Valida: parse frontmatter, capture session_id, logica de target, lock local.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hub_dispatch as hd


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
    assert not hd.target_matches("windows", "norte")
    assert hd.target_matches(None, "norte")  # default any


def test_lock_local_atomic():
    d = tempfile.mkdtemp()
    hd.HUB = d
    hd.REMOTE = None
    os.makedirs(os.path.join(d, ".processing"), exist_ok=True)
    # primer lock ok
    assert hd.try_lock("brief_1", "norte", "norte")
    # segundo intento (mismo agente) falla (FileExists)
    assert not hd.try_lock("brief_1", "norte", "norte")
    # otro agente para target:any -> cede si lock vivo
    assert not hd.try_lock("brief_1", "windows", "any")
    hd.release_lock("brief_1", "norte")
    # tras liberar, windows puede tomarlo
    assert hd.try_lock("brief_1", "windows", "any")


def test_seen_local():
    d = tempfile.mkdtemp()
    hd.HUB = d
    hd.REMOTE = None
    assert not hd.seen_exists("brief_x", "norte")
    hd.mark_seen("brief_x", "norte")
    assert hd.seen_exists("brief_x", "norte")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"OK {name}")
    print("ALL TESTS PASSED")
