from __future__ import annotations

from pathlib import Path

import yaml

from conftest import PLUGIN_ROOT, load_plugin

EXPECTED_NATIVE_TOOLS = {
    "ds_doctor", "ds_list_quests", "ds_get_quest_state", "ds_set_active_quest", "ds_new_quest",
    "ds_add_user_message", "ds_read_quest_documents", "ds_memory_search", "ds_memory_read", "ds_memory_write",
    "ds_artifact_record", "ds_confirm_baseline", "ds_waive_baseline", "ds_attach_baseline", "ds_submit_idea",
    "ds_list_research_branches", "ds_record_main_experiment", "ds_create_analysis_campaign", "ds_record_analysis_slice",
    "ds_submit_paper_outline", "ds_submit_paper_bundle", "ds_bash_exec", "ds_pause_quest", "ds_resume_quest", "ds_stop_quest",
}
EXPECTED_SKILLS = {
    "deepscientist:scout", "deepscientist:baseline", "deepscientist:idea", "deepscientist:optimize",
    "deepscientist:experiment", "deepscientist:analysis-campaign", "deepscientist:write", "deepscientist:finalize",
    "deepscientist:decision", "deepscientist:figure-polish", "deepscientist:intake-audit", "deepscientist:review", "deepscientist:rebuttal",
}

class FakeContext:
    def __init__(self, plugin_name="deepscientist"):
        self.plugin_name = plugin_name
        self.tools = {}
        self.commands = {}
        self.hooks = {}
        self.skills = {}
    def register_tool(self, **kwargs):
        self.tools[kwargs["name"]] = kwargs
    def register_command(self, name, handler, **kwargs):
        self.commands[name] = {"handler": handler, **kwargs}
    def register_hook(self, name, handler):
        self.hooks[name] = handler
    def register_skill(self, name, path):
        if ":" in name:
            raise ValueError("plugin skill names must be bare; namespace is derived from plugin name")
        self.skills[f"{self.plugin_name}:{name}"] = Path(path)


def test_manifest_and_registration_contract():
    plugin = load_plugin()
    manifest = yaml.safe_load((PLUGIN_ROOT / "plugin.yaml").read_text(encoding="utf-8"))
    assert manifest["name"] == "deepscientist"
    assert manifest["kind"] == "standalone"
    assert EXPECTED_NATIVE_TOOLS.issubset(set(manifest["provides_tools"]))
    assert "ds_call_mcp_tool" not in manifest["provides_tools"]
    ctx = FakeContext()
    plugin.register(ctx)
    assert EXPECTED_NATIVE_TOOLS.issubset(ctx.tools)
    assert set(manifest["provides_tools"]).issubset(ctx.tools)
    assert ctx.commands.keys() == {"ds"}
    assert {"pre_llm_call", "on_session_start", "on_session_end", "post_tool_call"}.issubset(ctx.hooks)
    assert EXPECTED_SKILLS.issubset(ctx.skills)
    assert ctx.skills["deepscientist:scout"].exists()


def test_real_plugin_context_registers_plugin_skills_as_namespaced_resources():
    import sys

    import hermes_cli
    from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest

    # When pytest is launched from the plugin source root, the local tools.py can
    # shadow Hermes core's top-level tools package. Real Hermes loads plugins
    # from the Hermes process, so pre-cache the core tools package for this
    # source-local contract test.
    hermes_root = Path(hermes_cli.__file__).resolve().parents[1]
    sys.path = [p for p in sys.path if p != str(hermes_root)]
    sys.path.insert(0, str(hermes_root))
    cached_tools = sys.modules.get("tools")
    if cached_tools is not None and not hasattr(cached_tools, "__path__"):
        sys.modules.pop("tools", None)
    from tools.registry import registry as _hermes_registry  # noqa: F401

    plugin = load_plugin()
    manager = PluginManager()
    manifest = PluginManifest(
        name="deepscientist",
        version="0.2.0",
        description="Hermes-native DeepScientist research mode with vendored headless runtime.",
        source="user",
    )
    ctx = PluginContext(manifest, manager)

    plugin.register(ctx)

    registered = set(manager.list_plugin_skills("deepscientist"))
    assert {name.split(":", 1)[1] for name in EXPECTED_SKILLS}.issubset(registered)
    assert "deepscientist-mode" in registered
    assert manager.find_plugin_skill("deepscientist:scout") == PLUGIN_ROOT / "resources" / "skills" / "scout" / "SKILL.md"
    assert manager.find_plugin_skill("deepscientist:deepscientist-mode") == PLUGIN_ROOT / "skills" / "deepscientist-mode" / "SKILL.md"


def test_no_raw_mcp_or_external_cli_bridge_registered():
    plugin = load_plugin()
    ctx = FakeContext(); plugin.register(ctx)
    forbidden = {"ds_call_mcp_tool", "mcp", "raw_mcp", "deepscientist_mcp"}
    assert not (forbidden & set(ctx.tools))
    for tool_name in ctx.tools:
        assert not tool_name.startswith("artifact.")
        assert not tool_name.startswith("memory.")
    assert not (PLUGIN_ROOT / "client.py").exists()
    assert not (PLUGIN_ROOT / "legacy_client.py").exists()
