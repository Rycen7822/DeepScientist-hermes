# DeepScientist Hermes 插件

[English](README.md) | 中文

本仓库把 [DeepScientist](https://github.com/ResearAI/DeepScientist) 改造成 Hermes Agent 原生插件。

DeepScientist 是 ResearAI 的科研操作系统。本项目保留 DeepScientist 的核心 headless 研究运行时，并把它适配成 Hermes Agent 插件，使 Hermes 成为唯一工作入口，用来管理 research quest、memory、artifact、实验、分析与论文写作流程。

## 这个项目是什么

- 一个名为 `deepscientist` 的 Hermes Agent 目录插件。
- 一个 Hermes-native 的 DeepScientist 核心科研流程集成。
- 一个自包含插件源码树，保留的 headless runtime 位于 `vendor/deepscientist`。
- 一组高层 `ds_*` Hermes 工具，不向用户暴露 raw MCP 调度。
- 一组随插件打包的 DeepScientist 阶段技能。
- 一套项目本地 runtime 布局，默认遵循上游 `ds --here` 语义：运行数据位于 `<project>/DeepScientist/`。

## 这个项目不是什么

- 不是上游 DeepScientist npm 包本身。
- 正常工作时不是调用全局安装的 `ds` 命令。
- 不向用户暴露 raw MCP。
- 不提供 Web UI、TUI、browser connector 或 social connector 入口。
- 不需要修改 Hermes core。

## 仓库结构

```text
plugin.yaml                         Hermes 插件 manifest
__init__.py                         插件注册入口
commands.py                         /ds slash command 处理器
tools.py                            Hermes-native ds_* 工具处理器
config.py                           项目本地 runtime 配置
runtime.py                          vendored runtime service factory
mode.py                             DeepScientist mode hooks
stage_router.py                     阶段和 companion skill 路由
prompt_adapter.py                   prompt/tool-name 适配
schemas.py                          工具 schema 和常量
skills/deepscientist-mode/          给 Hermes agent 的紧凑操作 skill
resources/skills/                   DeepScientist 阶段 skills
resources/prompts/                  插件使用的 prompt fragments
vendor/deepscientist/               保留的 headless DeepScientist runtime
docs/USAGE.md                       给 agent 的详细操作手册
docs/AGENT_PROJECT_INSTALL.md       给 agent 的项目级安装手册
tests/                              合同测试和回归测试
```

## 快速开始

插件源码仓库是：

```text
https://github.com/Rycen7822/DeepScientist-hermes
```

把安装任务交给另一个 Hermes agent 时，必须明确告诉它先 clone 或更新这个仓库。clone 下来的仓库根目录就是插件源码目录；该目录必须包含 `plugin.yaml`、`__init__.py`、`docs/USAGE.md` 和 `docs/AGENT_PROJECT_INSTALL.md`。

推荐使用项目级安装。把插件安装到需要 DeepScientist 工作区的研究项目中：

```text
<target-project>/.hermes/plugins/deepscientist/
```

运行数据单独保存在：

```text
<target-project>/DeepScientist/
```

这个 runtime 目录保存 memory、quests、artifacts、config、runtime files、logs、cache 和 Hermes session map。

由于 Hermes 当前的项目插件加载需要显式启用，请从目标项目目录启动：

```bash
cd <target-project>
HERMES_ENABLE_PROJECT_PLUGINS=true hermes
```

standalone 插件仍需要在当前 Hermes home config 中启用，除非使用项目本地 `HERMES_HOME`。项目级安装的完整步骤和取舍见 `docs/AGENT_PROJECT_INSTALL.md`。

如果希望插件对当前 Hermes 用户全局可用，也可以做全局安装。全局安装时，插件代码位于 `${HERMES_HOME:-$HOME/.hermes}/plugins/deepscientist/`，并且需要在 `$HERMES_HOME/config.yaml` 的 `plugins.enabled` 中启用 `deepscientist`；但具体研究任务仍应从对应研究项目目录启动 Hermes，使 DeepScientist runtime 位于 `<research-project>/DeepScientist/`。

## 给 agent 的安装 prompts

### 项目级安装 prompt

把下面这段 prompt 交给 Hermes agent，并替换目标项目路径：

```text
请把 DeepScientist Hermes 原生插件按项目级方式安装到目标项目目录：<target-project>。
需要先拉取的源码仓库：https://github.com/Rycen7822/DeepScientist-hermes
如果本机还没有 clone 该仓库，请 clone 到安全的临时目录或用户指定工作目录；如果已经 clone，请先 pull/update。使用 clone 后的仓库根目录作为 <plugin-source>；它必须包含 plugin.yaml、__init__.py、docs/USAGE.md 和 docs/AGENT_PROJECT_INSTALL.md。
请先阅读 <plugin-source>/docs/AGENT_PROJECT_INSTALL.md，并严格按该文档执行。
安装目标必须是 <target-project>/.hermes/plugins/deepscientist/。
不要安装到全局 Hermes plugin 目录，不要修改 Hermes core。
需要启用项目级插件扫描：HERMES_ENABLE_PROJECT_PLUGINS=true。
安装后请验证 /ds help、/ds doctor 和 deepscientist:deepscientist-mode。
最终回复请给出源码 clone 路径、插件目录、DeepScientist runtime 目录、验证结果、是否修改了 $HERMES_HOME/config.yaml 或是否使用项目本地 HERMES_HOME，以及完成时间。
```

### 全局安装 prompt

如果希望给当前 Hermes 用户做常规全局插件安装，把下面这段 prompt 交给 Hermes agent：

```text
请把 DeepScientist Hermes 原生插件全局安装到当前 Hermes 用户环境。
需要先拉取的源码仓库：https://github.com/Rycen7822/DeepScientist-hermes
如果本机还没有 clone 该仓库，请 clone 到安全的临时目录或用户指定工作目录；如果已经 clone，请先 pull/update。使用 clone 后的仓库根目录作为 <plugin-source>；它必须包含 plugin.yaml、__init__.py、docs/USAGE.md 和 vendor/deepscientist/。
把插件代码安装到 ${HERMES_HOME:-$HOME/.hermes}/plugins/deepscientist/；如果设置了 HERMES_HOME，则使用 $HERMES_HOME/plugins/deepscientist/。
通过把 deepscientist 加入 $HERMES_HOME/config.yaml 的 plugins.enabled 来启用 standalone 插件；必须保留已有配置，如果 plugins.disabled 里有 deepscientist，需要移除。
不要修改 Hermes core。不要把全局 npm ds 命令作为正常 runtime 路径。不要启用 Web UI、TUI 或 raw MCP surface。
安装后重启 Hermes。请从实际研究项目目录启动 Hermes，使该项目的 DeepScientist runtime 位于 <research-project>/DeepScientist/。
重启后请验证 /ds help、/ds doctor 和 deepscientist:deepscientist-mode。
最终回复请给出源码 clone 路径、全局插件目录、当前 Hermes home、配置变更、DeepScientist runtime 目录、验证结果和完成时间。
```

## Hermes 内使用方式

插件安装并加载后，Hermes agent 应优先加载和遵循：

```text
deepscientist:deepscientist-mode
```

常用 slash commands：

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

完整 agent runbook 见 `docs/USAGE.md`。

## 测试

在仓库根目录运行：

```bash
PYTHONPATH=/path/to/hermes-agent pytest tests -q
python -m compileall -q .
```

测试覆盖插件注册、项目本地 runtime 路径、Web/TUI/connector surface 移除、源码加载、操作文档和项目级安装文档。

## 上游与许可证

- 上游 DeepScientist：https://github.com/ResearAI/DeepScientist
- 本仓库是把保留的 DeepScientist 核心能力适配为 Hermes Agent 插件的改造项目。
- 许可证：Apache-2.0。见 `LICENSE`。
