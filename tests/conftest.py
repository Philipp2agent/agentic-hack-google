"""Shared pytest setup (claude-03).

The committed seeds in src/data/ are the demo state. Some test modules write the real files
(src/voice/app.py and src/dashboard/app.py hard-code src/data); this snapshot/restore makes sure
`pytest` never leaves `git status src/data/` dirty.
"""
from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "src" / "data"


@pytest.fixture(scope="session", autouse=True)
def _restore_committed_seeds():
    before = {p: p.read_bytes() for p in DATA_DIR.glob("*.json")}
    yield
    for path, content in before.items():
        if not path.exists() or path.read_bytes() != content:
            path.write_bytes(content)
    for path in DATA_DIR.glob("*.json"):
        if path not in before and path.name not in ("call.json", "meta.json"):
            path.unlink()
    for bak in DATA_DIR.glob("*.test_bak"):
        bak.unlink()
