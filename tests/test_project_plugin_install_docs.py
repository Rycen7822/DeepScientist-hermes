from __future__ import annotations

from conftest import PLUGIN_ROOT


PROJECT_INSTALL_DOC = PLUGIN_ROOT / "docs" / "AGENT_PROJECT_INSTALL.md"
README = PLUGIN_ROOT / "README.md"


def test_agent_project_install_doc_exists_and_covers_project_plugin_flow():
    assert PROJECT_INSTALL_DOC.exists()
    text = PROJECT_INSTALL_DOC.read_text(encoding="utf-8")

    required_phrases = [
        "给 Hermes agent 的项目级安装手册",
        "不要安装到 `$HERMES_HOME/plugins/deepscientist`",
        "<target-project>/.hermes/plugins/deepscientist/",
        "HERMES_ENABLE_PROJECT_PLUGINS=true",
        "plugins.enabled",
        "$HERMES_HOME/config.yaml",
        "rsync -a --delete",
        "--exclude '__pycache__/'",
        "--exclude '.pytest_cache/'",
        "--exclude 'test/logs/'",
        "<target-project>/DeepScientist/",
        "deepscientist:deepscientist-mode",
        "/ds doctor",
        "/ds help",
        "source tree smoke",
        "不调用全局 npm `ds`",
        "不暴露 raw MCP",
        "不打开 Web UI",
        "不打开 TUI",
        "不要修改 Hermes core",
        "完成时间",
    ]
    for phrase in required_phrases:
        assert phrase in text

    forbidden_phrases = [
        "hermes plugins install",
        "hermes plugins enable deepscientist",
        "~/.hermes/plugins/deepscientist",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text


def test_readmes_contain_short_prompt_for_agent_project_install():
    readme = README.read_text(encoding="utf-8")
    zh_readme = (PLUGIN_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    assert "Agent prompt for project-local installation" in readme
    assert "docs/AGENT_PROJECT_INSTALL.md" in readme
    assert "target project directory" in readme
    assert "Do not install into the global Hermes plugin directory" in readme
    assert "HERMES_ENABLE_PROJECT_PLUGINS=true" in readme
    assert "<target-project>/.hermes/plugins/deepscientist/" in readme

    assert "项目级安装 prompt" in zh_readme
    assert "docs/AGENT_PROJECT_INSTALL.md" in zh_readme
    assert "目标项目目录" in zh_readme
    assert "不要安装到全局 Hermes plugin 目录" in zh_readme
    assert "HERMES_ENABLE_PROJECT_PLUGINS=true" in zh_readme
    assert "<target-project>/.hermes/plugins/deepscientist/" in zh_readme
