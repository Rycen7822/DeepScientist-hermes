# DeepScientist Hermes Plugin

English | [中文](README.zh-CN.md)

This repository packages a Hermes Agent native plugin for [DeepScientist](https://github.com/ResearAI/DeepScientist).

DeepScientist is the upstream research operating system by ResearAI. This project adapts the retained headless DeepScientist research runtime into a Hermes Agent plugin so that Hermes becomes the only working entry point for research quests, memory, artifacts, experiments, analysis, and writing workflows.

## What this project is

- A Hermes Agent directory plugin named `deepscientist`.
- A Hermes-native integration of the core DeepScientist research workflow.
- A self-contained plugin source tree with vendored headless runtime code under `vendor/deepscientist`.
- A curated Hermes toolset exposing high-level `ds_*` tools instead of raw MCP dispatch.
- A set of DeepScientist stage skills packaged as plugin resources.
- A project-local runtime layout that follows upstream `ds --here` semantics: runtime data lives in `<project>/DeepScientist/`.

## What this project is not

- It is not the upstream DeepScientist npm package.
- It is not a wrapper that calls the globally installed `ds` command for normal operation.
- It does not expose raw MCP to the user.
- It does not provide Web UI, TUI, browser connector, or social connector entry points.
- It does not require modifying Hermes core.

## Repository layout

```text
plugin.yaml                         Hermes plugin manifest
__init__.py                         Plugin registration entry point
commands.py                         /ds slash command handler
tools.py                            Hermes-native ds_* tool handlers
config.py                           Project-local runtime configuration
runtime.py                          Vendored runtime service factory
mode.py                             DeepScientist mode hooks
stage_router.py                     Stage and companion skill routing
prompt_adapter.py                   Prompt/tool-name adaptation
schemas.py                          Tool schemas and constants
skills/deepscientist-mode/          Compact operator skill for Hermes agent
resources/skills/                   DeepScientist stage skills
resources/prompts/                  Prompt fragments used by the plugin
vendor/deepscientist/               Retained headless DeepScientist runtime
docs/USAGE.md                       Agent-facing operation manual
docs/AGENT_PROJECT_INSTALL.md       Agent-facing project-local install manual
tests/                              Contract and regression tests
```

## Quick start for users

The plugin source repository is:

```text
https://github.com/Rycen7822/DeepScientist-hermes
```

When asking another Hermes agent to install this plugin, explicitly tell it to clone or update that repository first. The cloned repository root is the plugin source directory; it must contain `plugin.yaml`, `__init__.py`, `docs/USAGE.md`, and `docs/AGENT_PROJECT_INSTALL.md`.

The recommended install style is project-local. Install the plugin into the research project that should own the DeepScientist workspace:

```text
<target-project>/.hermes/plugins/deepscientist/
```

Runtime data is stored separately under:

```text
<target-project>/DeepScientist/
```

That runtime tree contains memory, quests, artifacts, config, runtime files, logs, cache, and the Hermes session map.

Because Hermes project-plugin loading is currently opt-in, launch Hermes from the target project with:

```bash
cd <target-project>
HERMES_ENABLE_PROJECT_PLUGINS=true hermes
```

Standalone plugins must still be enabled through the active Hermes home config, unless you use a project-local `HERMES_HOME`. See `docs/AGENT_PROJECT_INSTALL.md` for the exact project-local steps and trade-offs.

A global install is also possible when you want this plugin available from the active Hermes home. In that case the plugin code lives under `${HERMES_HOME:-$HOME/.hermes}/plugins/deepscientist/`, the plugin name `deepscientist` must be enabled in `$HERMES_HOME/config.yaml`, and Hermes should still be launched from the research project directory whose DeepScientist runtime should live in `<research-project>/DeepScientist/`.

## Agent installation prompts

### Project-local installation prompt

Copy this prompt to a Hermes agent and replace the target path:

```text
Please install the DeepScientist Hermes native plugin into this target project directory: <target-project>.
Source repository to fetch first: https://github.com/Rycen7822/DeepScientist-hermes
If the repository is not already cloned, clone it into a safe temporary or user-selected work directory. If it is already cloned, pull/update it. Use the cloned repository root as <plugin-source>; it must contain plugin.yaml, __init__.py, docs/USAGE.md, and docs/AGENT_PROJECT_INSTALL.md.
Read <plugin-source>/docs/AGENT_PROJECT_INSTALL.md first and follow it exactly.
Install the plugin code into <target-project>/.hermes/plugins/deepscientist/.
Do not install into the global Hermes plugin directory and do not modify Hermes core.
Enable project plugin scanning with HERMES_ENABLE_PROJECT_PLUGINS=true.
After installation, verify /ds help, /ds doctor, and deepscientist:deepscientist-mode.
Report the source clone path, plugin directory, DeepScientist runtime directory, verification results, whether $HERMES_HOME/config.yaml was changed or a project-local HERMES_HOME was used, and the completion time.
```

### Global installation prompt

Copy this prompt to a Hermes agent when you want a normal global Hermes plugin install for the current Hermes user:

```text
Please install the DeepScientist Hermes native plugin globally for the active Hermes user.
Source repository to fetch first: https://github.com/Rycen7822/DeepScientist-hermes
If the repository is not already cloned, clone it into a safe temporary or user-selected work directory. If it is already cloned, pull/update it. Use the cloned repository root as <plugin-source>; it must contain plugin.yaml, __init__.py, docs/USAGE.md, and vendor/deepscientist/.
Install the plugin code into ${HERMES_HOME:-$HOME/.hermes}/plugins/deepscientist/; if HERMES_HOME is set, use $HERMES_HOME/plugins/deepscientist/.
Enable the standalone plugin by adding deepscientist to plugins.enabled in $HERMES_HOME/config.yaml, preserving existing config and removing deepscientist from plugins.disabled if present.
Do not modify Hermes core. Do not call the globally installed npm ds command as the normal runtime path. Do not enable Web UI, TUI, or raw MCP surfaces.
Restart Hermes after installation. Launch Hermes from the research project directory whose DeepScientist runtime should live in <research-project>/DeepScientist/.
After restart, verify /ds help, /ds doctor, and deepscientist:deepscientist-mode.
Report the source clone path, global plugin directory, active Hermes home, config changes, DeepScientist runtime directory, verification results, and the completion time.
```

## Operating inside Hermes

After the plugin is installed and loaded, the Hermes agent should use:

```text
deepscientist:deepscientist-mode
```

Useful slash commands:

```text
/ds help
/ds doctor
/ds list
/ds new <goal>
/ds active [quest_id]
/ds status [quest_id]
/ds stage [stage]
/ds docs <quest_id>
```

The full agent runbook is in `docs/USAGE.md`.

## Testing

From the repository root:

```bash
PYTHONPATH=/path/to/hermes-agent pytest tests -q
python -m compileall -q .
```

The tests check plugin registration, project-local runtime paths, no Web/TUI/connector surface, source-load behavior, operator documentation, and project-local installation documentation.

## Upstream and license

- Upstream DeepScientist: https://github.com/ResearAI/DeepScientist
- This repository is an adaptation of the retained DeepScientist core into a Hermes Agent plugin.
- License: Apache-2.0. See `LICENSE`.
