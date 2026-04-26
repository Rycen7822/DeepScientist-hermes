from __future__ import annotations

from conftest import PLUGIN_ROOT


REQUIRED_TOOL_NAMES = [
    "ds_doctor",
    "ds_new_quest",
    "ds_set_active_quest",
    "ds_get_quest_state",
    "ds_memory_write",
    "ds_memory_search",
    "ds_artifact_record",
    "ds_bash_exec",
    "ds_submit_idea",
    "ds_record_main_experiment",
    "ds_submit_paper_bundle",
]

REQUIRED_SLASH_COMMANDS = [
    "/ds doctor",
    "/ds new <goal>",
    "/ds active [quest_id]",
    "/ds status [quest_id]",
    "/ds stage [stage]",
    "/ds docs <quest_id>",
]

REQUIRED_STAGES = [
    "scout",
    "baseline",
    "idea",
    "optimize",
    "experiment",
    "analysis-campaign",
    "write",
    "finalize",
    "review",
    "rebuttal",
]


def test_user_usage_documentation_exists_and_covers_agent_workflow():
    usage = PLUGIN_ROOT / "docs" / "USAGE.md"
    assert usage.exists()
    text = usage.read_text(encoding="utf-8")

    required_phrases = [
        "Hermes agent 操作手册",
        "Agent runbook",
        "首次接手任务",
        "何时使用 DeepScientist 工具，何时使用 Hermes 原生工具",
        "<project>/DeepScientist/",
        "不要调用全局 npm `ds`",
        "不要暴露 raw MCP",
        "Web UI",
        "TUI",
        "项目本地存储",
        "记忆与 artifacts 的写入规范",
        "阶段推进规则",
        "故障处理",
        "安装后验证",
    ]
    for phrase in required_phrases:
        assert phrase in text

    for name in REQUIRED_TOOL_NAMES:
        assert f"`{name}`" in text
    for command in REQUIRED_SLASH_COMMANDS:
        assert f"`{command}`" in text
    for stage in REQUIRED_STAGES:
        assert f"`{stage}`" in text
    assert "daemon" not in text.lower()


def test_readmes_point_to_usage_guide_and_quickstart():
    readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
    zh_readme = (PLUGIN_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    assert "docs/USAGE.md" in readme
    assert "Quick start" in readme
    assert "<project>/DeepScientist/" in readme
    assert "deepscientist:deepscientist-mode" in readme
    assert "README.zh-CN.md" in readme
    assert "daemon" not in readme.lower()

    assert "docs/USAGE.md" in zh_readme
    assert "快速开始" in zh_readme
    assert "<project>/DeepScientist/" in zh_readme
    assert "deepscientist:deepscientist-mode" in zh_readme
    assert "README.md" in zh_readme
    assert "daemon" not in zh_readme.lower()


def test_agent_mode_skill_contains_enough_operational_guidance():
    skill = PLUGIN_ROOT / "skills" / "deepscientist-mode" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    required = [
        "Agent runbook",
        "首次接手任务",
        "工具选择规则",
        "阶段推进规则",
        "项目本地存储",
        "<project>/DeepScientist/",
        "不要调用全局 npm `ds`",
        "不要暴露 raw MCP",
        "完成任务回复",
    ]
    for phrase in required:
        assert phrase in text
    for name in ["ds_doctor", "ds_new_quest", "ds_get_quest_state", "ds_memory_write", "ds_artifact_record", "ds_bash_exec"]:
        assert f"`{name}`" in text
    assert "daemon" not in text.lower()
