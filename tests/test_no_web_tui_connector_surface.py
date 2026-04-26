from __future__ import annotations

from conftest import PLUGIN_ROOT, load_plugin

FORBIDDEN_PATH_PARTS = [
    "src/ui", "src/tui", "connector_runtime.py", "connector_profiles.py", "qq_profiles.py", "weixin_support.py", "lingzhu_support.py",
    "vendor/deepscientist/tui.py", "vendor/deepscientist/connector", "resources/prompts/connectors",
    "daemon_client.py", "daemon_manager.py", "vendor/deepscientist/daemon", "vendor/deepscientist/cli.py",
]


def test_forbidden_web_tui_connector_and_daemon_paths_absent():
    for rel in FORBIDDEN_PATH_PARTS:
        assert not (PLUGIN_ROOT / rel).exists(), rel
    for path in PLUGIN_ROOT.rglob("*"):
        if path.is_dir() and path.name == "__pycache__":
            continue
        normalized = path.relative_to(PLUGIN_ROOT).as_posix().lower()
        assert "/connector/" not in f"/{normalized}/"
        assert "/daemon/" not in f"/{normalized}/"
        assert "daemon_client" not in normalized
        assert "daemon_manager" not in normalized
        assert not normalized.endswith("/tui.py")


def test_source_does_not_default_to_external_ds_raw_mcp_or_daemon_dispatch():
    checked = []
    for rel in ["__init__.py", "config.py", "runtime.py", "tools.py", "commands.py", "mode.py", "schemas.py"]:
        text = (PLUGIN_ROOT / rel).read_text(encoding="utf-8")
        checked.append(rel)
        assert "run_ds(" not in text
        assert "ds_binary" not in text
        assert "subprocess" not in text or rel not in {"tools.py", "runtime.py", "commands.py"}
        assert "ds_call_mcp_tool" not in text
        assert "daemon" not in text.lower()
    assert checked


def test_no_daemon_literals_remain_in_non_test_source_or_resources():
    suffixes = {".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".js", ".ts"}
    ignored_parts = {"test", "tests", "logs", ".pytest_cache", "__pycache__"}
    hits = []
    for path in PLUGIN_ROOT.rglob("*"):
        rel = path.relative_to(PLUGIN_ROOT)
        if any(part in ignored_parts for part in rel.parts):
            continue
        normalized = rel.as_posix().lower()
        if "daemon" in path.name.lower():
            hits.append(f"filename:{rel.as_posix()}")
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            if "daemon" in line.lower():
                hits.append(f"content:{normalized}:{line_number}:{line.strip()}")
    assert hits == []
