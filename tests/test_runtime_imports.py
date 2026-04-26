from __future__ import annotations

import importlib
import shutil

import pytest

from conftest import load_plugin, parse_json


def test_runtime_imports_without_global_ds_binary_and_without_daemon_config():
    load_plugin()
    from hermes_plugins.deepscientist_native import runtime, tools

    assert shutil.which("ds") is None
    services = runtime.get_services()
    assert services.home.exists()
    assert services.resource_repo_root.exists()
    assert (services.resource_repo_root / "src" / "skills" / "scout" / "SKILL.md").exists()
    payload = parse_json(tools.ds_doctor({}))
    assert payload["ok"] is True
    assert any(item["id"] == "no_external_ds_required" for item in payload["checks"])
    assert "daemon" not in payload["config"]
    assert not any("daemon" in item["id"].lower() for item in payload["checks"])


def test_daemon_modules_are_not_importable_from_native_plugin():
    load_plugin()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("hermes_plugins.deepscientist_native.daemon_manager")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("hermes_plugins.deepscientist_native.daemon_client")
