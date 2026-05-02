from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(autouse=True)
def isolated_native_env(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (tmp_path / "bin").mkdir()
    monkeypatch.chdir(project_root)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("DEEPSCIENTIST_HERMES_ROOT", raising=False)
    monkeypatch.delenv("DEEPSCIENTIST_HERMES_CONFIG", raising=False)
    monkeypatch.delenv("DEEPSCIENTIST_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("DEEPSCIENTIST_HERMES_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("DEEPSCIENTIST_HOME", raising=False)
    monkeypatch.delenv("DS_HOME", raising=False)
    monkeypatch.setenv("PATH", f"{tmp_path / 'bin'}:/usr/bin:/bin")
    yield


def load_plugin():
    # Avoid stale package modules between tests while keeping vendored deepscientist importable.
    for name in list(sys.modules):
        if name == "hermes_plugins.deepscientist_native" or name.startswith("hermes_plugins.deepscientist_native."):
            sys.modules.pop(name, None)
    parent = sys.modules.setdefault("hermes_plugins", types.ModuleType("hermes_plugins"))
    parent.__path__ = []
    spec = importlib.util.spec_from_file_location(
        "hermes_plugins.deepscientist_native",
        PLUGIN_ROOT / "__init__.py",
        submodule_search_locations=[str(PLUGIN_ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def parse_json(text: str):
    import json
    return json.loads(text)
