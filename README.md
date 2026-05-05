<h1 align="center">
  DeepScientist × Hermes Agent
</h1>

<p align="center">
  <a href="https://github.com/ResearAI/DeepScientist">Upstream DeepScientist</a> |
  <a href="README.zh-CN.md">中文文档</a> |
  <a href="docs/USAGE.md">Hermes Usage</a> |
  <a href="docs/AGENT_PROJECT_INSTALL.md">Project Install</a> |
  <a href="DeepScientist-codex/README.md">Codex Adapter</a>
</p>

<p align="center">
  <a href="plugin.yaml"><img alt="Hermes native plugin" src="https://img.shields.io/badge/Hermes-Native%20Plugin-4D6A7A?style=for-the-badge"></a>
  <a href="DeepScientist-codex/README.md"><img alt="Codex native adapter" src="https://img.shields.io/badge/Codex-Native%20Adapter-2563EB?style=for-the-badge"></a>
  <a href="#what-this-project-is-not"><img alt="No raw MCP" src="https://img.shields.io/badge/Raw%20MCP-Not%20Exposed-2E7D32?style=for-the-badge"></a>
  <a href="#project-local-runtime"><img alt="Project local runtime" src="https://img.shields.io/badge/Runtime-Project%20Local-7C3AED?style=for-the-badge"></a>
</p>

<p align="center">
  <strong>One research runtime</strong> ·
  <strong>Two native agent surfaces</strong> ·
  <strong>Project-local quests</strong> ·
  <strong>Auditable experiments and artifacts</strong>
</p>

<p align="center">
  <strong>Hermes or Codex does the mechanical work. DeepScientist records the research meaning.</strong>
</p>

---

This repository adapts [DeepScientist](https://github.com/ResearAI/DeepScientist) into native agent integrations for Hermes Agent and Codex CLI.

DeepScientist is the upstream research operating system by ResearAI. This project keeps the retained headless DeepScientist research runtime and exposes it through high-level `ds_*` tools, packaged skills, project-local state, and agent-facing install/runbook documentation.

## Why this repository exists

Research work is long-lived: papers, baselines, experiment branches, logs, artifacts, memory, analysis, and writing rarely fit in a single chat turn. This repository keeps that structure available to modern coding agents without forcing users back into the original UI surfaces.

| Common pain point | What this integration keeps durable |
| --- | --- |
| A research idea disappears into chat history | Quests, requirements, stage state, and memory are persisted under `<project>/DeepScientist/`. |
| Experiments and baselines are hard to audit later | Baselines, experiment records, analysis slices, bash provenance, and milestones become DeepScientist artifacts. |
| Literature and paper work lives outside the agent loop | Strict-research ledgers, reliability cards, writing plans, reviews, and paper bundles are packaged as tools and skills. |
| Different agent CLIs need different installs | Hermes Agent gets a native plugin; Codex CLI gets `DeepScientist-codex/`, a separate native adapter. |

## At a glance

| Area | Hermes Agent path | Codex CLI path |
| --- | --- | --- |
| Entry point | `plugin.yaml`, `__init__.py`, `/ds ...`, Hermes `ds_*` tools | `DeepScientist-codex/scripts/dsctl.py` and a local-personal Codex plugin install |
| Operator skill | `deepscientist:deepscientist-mode` | `deepscientist-codex` |
| Runtime data | `<project>/DeepScientist/` | `<project>/DeepScientist/` |
| Tool naming | High-level `ds_*` Hermes tools | 48 public canonical `ds_*` tools; legacy `deepscientist_*` names are hidden compatibility aliases |
| Boundary | No raw MCP user surface, no global npm `ds` command for normal work | No `.mcp.json`, no MCP server transport, no FastMCP startup, no global npm `ds` command for normal work |

## What this project is

- A Hermes Agent directory plugin named `deepscientist`.
- A Hermes-native integration of the core DeepScientist research workflow.
- A self-contained plugin source tree with vendored headless runtime code under `vendor/deepscientist`.
- A curated Hermes toolset exposing high-level `ds_*` tools instead of raw MCP dispatch.
- A packaged DeepScientist skill set: stages, companions, strict literature research, `review`, `experiment-execution`, `quest-handoffs`, `writing-plans`, `paper-reliability-verification`, and a bundled `paper-reliability-verifier` workflow.
- A Codex-native adapter under `DeepScientist-codex/` for users whose operator is Codex CLI rather than Hermes Agent.
- A project-local runtime layout that follows upstream `ds --here` semantics: runtime data lives in `<project>/DeepScientist/`.

## What this project is not

- It is not the upstream DeepScientist npm package itself.
- It is not a wrapper that calls the globally installed `ds` command for normal operation.
- It does not expose raw MCP to the user.
- It does not provide Web UI, TUI, browser connector, or social connector entry points.
- It does not require modifying Hermes core.

## What can it help an agent get done?

### 1. Start a real research quest

- create a quest from a paper, repository, or natural-language research objective
- preserve the goal, mode, active stage, requirements, and accumulated context
- keep state in the project rather than in transient chat history

### 2. Reproduce baselines and run experiments with provenance

- attach or confirm baselines
- record main experiment runs, setup details, metrics, and conclusions
- use quest-local execution evidence when a command matters to the research record

### 3. Build a reviewable research memory

- write searchable memory cards and decision records
- record milestones and structured artifacts
- read quest documents, status, analysis campaigns, and event traces

### 4. Turn results into materials you can ship

- maintain paper bundles and outline state
- support strict literature research and reliability verification
- package writing plans, review workflows, and final report artifacts

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
skills/deepscientist-mode/          Compact operator skill for Hermes Agent
resources/skills/                   DeepScientist stage, companion, and support skills
resources/prompts/                  Prompt fragments used by the plugin
vendor/deepscientist/               Retained headless DeepScientist runtime
DeepScientist-codex/                Native Codex CLI adapter for the same headless runtime
docs/USAGE.md                       Agent-facing operation manual
docs/AGENT_PROJECT_INSTALL.md       Agent-facing project-local install manual
tests/                              Contract and regression tests
```

## Quick start

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

## Project-local runtime

DeepScientist state is intentionally project-local:

```text
<project>/DeepScientist/
```

This keeps quests, artifacts, memory, bash provenance, paper bundles, and runtime config beside the research code and data that produced them.

## Codex CLI native adapter

This repository also includes `DeepScientist-codex/`, a native Codex CLI adapter for the same retained DeepScientist headless runtime. Use it when the operator is Codex CLI rather than Hermes Agent.

Important boundaries:

- `DeepScientist-codex/` is not MCP. It does not create `.mcp.json`, does not register a server transport, and does not start the original FastMCP server.
- It does not call the external npm `ds` command for normal work.
- It provides Codex-native functional equivalents for the original DeepScientist Hermes MCP business surface through `scripts/dsctl.py` and canonical `ds_*` handlers.
- Public `list-tools` reports 48 canonical `ds_*` tools, including `ds_events`; legacy `deepscientist_*` names are hidden compatibility aliases.
- Research runtime data still lives in the target research project under `<project>/DeepScientist/`.

Install it into Codex from this repository:

```bash
cd <plugin-source>/DeepScientist-codex
bash scripts/install.sh
```

The installer copies the adapter to `~/.codex/plugins/deepscientist-codex`, backs up an existing installed copy as `~/.codex/plugins/deepscientist-codex.backup-<timestamp>`, registers a local marketplace entry in `~/.agents/plugins/marketplace.json`, enables `[plugins."deepscientist-codex@local-personal"]` in `~/.codex/config.toml`, and runs the bundled doctor check.

After install, initialize and verify it from the research project root:

```bash
bash ~/.codex/plugins/deepscientist-codex/scripts/init_project.sh /path/to/project
python ~/.codex/plugins/deepscientist-codex/scripts/dsctl.py --project-root /path/to/project doctor --format json
python ~/.codex/plugins/deepscientist-codex/scripts/dsctl.py --project-root /path/to/project list-tools --format json
```

The `list-tools` output should report `transport="codex-native-cli"`, `mcp=false`, `count=48`, `ds_events`, and no public `deepscientist_*` tools. For detailed usage, see `DeepScientist-codex/README.md`, `DeepScientist-codex/README.zh-CN.md`, `DeepScientist-codex/docs/INSTALL.md`, and `DeepScientist-codex/docs/USAGE.md`.

When asking an agent to install the Codex adapter, use this prompt and replace the paths:

```text
Please install the DeepScientist Codex native adapter for Codex CLI.
Source repository to fetch first: https://github.com/Rycen7822/DeepScientist-hermes
If the repository is not already cloned, clone it into a safe temporary or user-selected work directory. If it is already cloned, pull/update it. Use the cloned repository root as <plugin-source>; it must contain DeepScientist-codex/scripts/install.sh, DeepScientist-codex/docs/INSTALL.md, and DeepScientist-codex/docs/USAGE.md.
Read <plugin-source>/DeepScientist-codex/docs/INSTALL.md first and follow it exactly.
Run the installer from <plugin-source>/DeepScientist-codex with bash scripts/install.sh.
Do not create .mcp.json, do not configure MCP servers, do not start FastMCP, and do not use the external npm ds command as the normal runtime path.
After installation, initialize the target research project with ~/.codex/plugins/deepscientist-codex/scripts/init_project.sh <target-project> and verify doctor plus list-tools from that project.
Report the source clone path, installed Codex plugin directory, target research project, DeepScientist runtime directory, list-tools transport/mcp values, verification results, and completion time.
```

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

The tests check plugin registration, project-local runtime paths, removed Web/TUI/connector surfaces, source-load behavior, operator documentation, and project-local installation documentation.

## Upstream and license

- Upstream DeepScientist: https://github.com/ResearAI/DeepScientist
- This repository is an adaptation of the retained DeepScientist core into Hermes Agent and Codex-native integrations.
- License: Apache-2.0. See `LICENSE`.
