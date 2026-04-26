from __future__ import annotations

import importlib
import shutil
import sys
import types
from pathlib import Path

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


def test_runtime_prefers_vendored_runtime_when_top_level_package_is_preloaded(tmp_path):
    load_plugin()
    from hermes_plugins.deepscientist_native import runtime

    fake_pkg = tmp_path / "external" / "deepscientist"
    fake_pkg.mkdir(parents=True)
    fake_init = fake_pkg / "__init__.py"
    fake_init.write_text("", encoding="utf-8")
    poison = types.ModuleType("deepscientist")
    poison.__file__ = str(fake_init)
    poison.__path__ = [str(fake_pkg)]
    poison_artifact = types.ModuleType("deepscientist.artifact")
    poison_artifact.__file__ = str(fake_pkg / "artifact.py")
    sys.modules["deepscientist"] = poison
    sys.modules["deepscientist.artifact"] = poison_artifact

    runtime.ensure_runtime_import_environment()
    import deepscientist
    import deepscientist.artifact

    assert Path(deepscientist.__file__).resolve().is_relative_to(runtime.VENDOR_ROOT.resolve())
    assert Path(deepscientist.artifact.__file__).resolve().is_relative_to(runtime.VENDOR_ROOT.resolve())


def test_daemon_modules_are_not_importable_from_native_plugin():
    load_plugin()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("hermes_plugins.deepscientist_native.daemon_manager")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("hermes_plugins.deepscientist_native.daemon_client")
