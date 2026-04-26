# 给 Hermes agent 的项目级安装手册

本文档是给 Hermes agent 执行 DeepScientist 原生插件“项目级安装”时看的操作手册。目标是把插件代码安装到用户指定研究项目目录中，而不是安装成全局 Hermes 插件。

## 0. 绝对约束

1. 不要修改 Hermes core，也就是不要写入或 patch `$HERMES_HOME/hermes-agent` 或 Hermes 安装目录下的核心源码。
2. 不要安装到 `$HERMES_HOME/plugins/deepscientist` 或默认全局 Hermes plugin 目录。
3. 不要用 `hermes plugins` 的全局安装流程来复制本插件。
4. 不调用全局 npm `ds` 作为正常工作路径。
5. 不暴露 raw MCP。
6. 不打开 Web UI。
7. 不打开 TUI。
8. 不写入 DeepScientist runtime 数据到 Hermes core 目录。
9. 默认保持 `memory.sync_to_hermes_memory: false`，不要把 DeepScientist 项目记忆同步进 Hermes 自己的长期记忆。
10. 如果需要修改 `$HERMES_HOME/config.yaml` 来加入 `plugins.enabled`，只改启用 allow-list，不要复制插件到全局 plugin 目录；如果用户要求零全局配置变更，使用本文的“严格项目本地 Hermes home 模式”。

## 1. 输入参数

执行安装前，agent 必须明确两个路径：

```text
<plugin-source>   DeepScientist 原生插件源码目录
<target-project>  用户指定的研究项目目录
```

如果 agent 正在本仓库中执行，`<plugin-source>` 就是当前仓库根目录，也就是包含 `plugin.yaml`、`__init__.py` 和 `docs/AGENT_PROJECT_INSTALL.md` 的目录。

目标安装目录必须是：

```text
<target-project>/.hermes/plugins/deepscientist/
```

DeepScientist runtime 数据默认会落在：

```text
<target-project>/DeepScientist/
```

二者含义不同：

- `<target-project>/.hermes/plugins/deepscientist/` 保存 Hermes 插件代码、插件文档、插件内置 skills、vendored runtime。
- `<target-project>/DeepScientist/` 保存 quest、memory、artifact、config、runtime files、logs、cache、Hermes session map。

## 2. 推荐安装模式：项目插件目录 + 当前 Hermes home 启用 allow-list

适用场景：用户接受在当前 `$HERMES_HOME/config.yaml` 中启用插件名，但插件代码必须只放在项目目录。

### 2.1 前置检查

```bash
cd <target-project>
pwd
test -f <plugin-source>/plugin.yaml
test -f <plugin-source>/__init__.py
test -f <plugin-source>/docs/USAGE.md
test -f <plugin-source>/docs/AGENT_PROJECT_INSTALL.md
```

检查目标目录，确认不会误删用户数据：

```bash
test "$(realpath <target-project>/.hermes/plugins/deepscientist 2>/dev/null || true)" != "$(realpath ${HERMES_HOME:-$HOME/.hermes}/plugins/deepscientist 2>/dev/null || true)"
```

如果 `<target-project>/.hermes/plugins/deepscientist/` 已存在，先判断它是否就是旧版 DeepScientist 项目插件。不要盲目覆盖不相关目录。

### 2.2 复制插件代码到项目目录

用 `rsync -a --delete` 保持目标目录与插件源码一致，同时排除 transient 文件：

```bash
mkdir -p <target-project>/.hermes/plugins
rsync -a --delete \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude 'test/logs/' \
  --exclude '*.pyc' \
  <plugin-source>/ \
  <target-project>/.hermes/plugins/deepscientist/
```

注意：`--delete` 只应该作用在 `<target-project>/.hermes/plugins/deepscientist/`，不要把目标写成 `<target-project>/.hermes/plugins/` 或 `<target-project>/`。

### 2.3 启用项目插件扫描

Hermes 目前只有在环境变量开启时才扫描项目插件目录。启动 Hermes 时必须包含：

```bash
HERMES_ENABLE_PROJECT_PLUGINS=true
```

推荐从目标项目目录启动：

```bash
cd <target-project>
HERMES_ENABLE_PROJECT_PLUGINS=true hermes
```

或者给用户创建一个项目本地启动脚本：

```bash
cat > <target-project>/.hermes/run-hermes-with-deepscientist.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export HERMES_ENABLE_PROJECT_PLUGINS=true
exec hermes "$@"
EOF
chmod +x <target-project>/.hermes/run-hermes-with-deepscientist.sh
```

### 2.4 配置 `plugins.enabled`

Hermes 目前的 standalone 插件仍需出现在 `$HERMES_HOME/config.yaml` 的 `plugins.enabled` 中。agent 可以用 YAML 安全方式添加：

```yaml
plugins:
  enabled:
    - deepscientist
```

要求：

- 保留已有配置，不要重写整个 config。
- 如果 `plugins.disabled` 中有 `deepscientist`，需要移除它。
- 不要把插件代码复制到全局 plugin 目录。
- 修改前后可显示 diff 给用户核对。

如果用户不允许动当前 `$HERMES_HOME/config.yaml`，不要强行修改，改用下一节“严格项目本地 Hermes home 模式”。

### 2.5 安装后验证

在 `<target-project>` 目录下执行不依赖全局 npm `ds` 的 source tree smoke：

```bash
cd <target-project>
HERMES_ENABLE_PROJECT_PLUGINS=true python - <<'PY'
from pathlib import Path
import os

root = Path.cwd()
plugin = root / '.hermes' / 'plugins' / 'deepscientist'
assert plugin.exists(), plugin
assert (plugin / 'plugin.yaml').exists()
assert (plugin / '__init__.py').exists()
assert (plugin / 'docs' / 'USAGE.md').exists()
assert (plugin / 'docs' / 'AGENT_PROJECT_INSTALL.md').exists()
hermes_home = Path(os.environ.get('HERMES_HOME', Path.home() / '.hermes'))
assert not (hermes_home / 'plugins' / 'deepscientist').exists()
print('project plugin files ok:', plugin)
print('project runtime home:', root / 'DeepScientist')
PY
```

然后新开 Hermes session，从 `<target-project>` 目录启动：

```bash
cd <target-project>
HERMES_ENABLE_PROJECT_PLUGINS=true hermes
```

在 Hermes 里验证：

```text
/ds help
/ds doctor
/skill deepscientist:deepscientist-mode
```

期望：

- `/ds help` 能显示 DeepScientist 命令。
- `/ds doctor` 能检查 native runtime。
- `deepscientist:deepscientist-mode` 可加载。
- DeepScientist runtime home 显示或推导为 `<target-project>/DeepScientist/`。

## 3. 严格项目本地 Hermes home 模式

适用场景：用户不想修改默认 `~/.hermes/config.yaml`，希望启用配置也留在项目目录。

做法：把该项目的 Hermes home 放在：

```text
<target-project>/.hermes/hermes-home/
```

创建项目本地 config：

```bash
mkdir -p <target-project>/.hermes/hermes-home
python - <<'PY'
from pathlib import Path
import yaml

home = Path('<target-project>/.hermes/hermes-home')
config = home / 'config.yaml'
if config.exists():
    data = yaml.safe_load(config.read_text(encoding='utf-8')) or {}
else:
    data = {}
plugins = data.setdefault('plugins', {})
enabled = plugins.setdefault('enabled', [])
if 'deepscientist' not in enabled:
    enabled.append('deepscientist')
disabled = plugins.get('disabled')
if isinstance(disabled, list):
    plugins['disabled'] = [x for x in disabled if x != 'deepscientist']
config.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding='utf-8')
print(config)
PY
```

启动方式：

```bash
cd <target-project>
HERMES_HOME=<target-project>/.hermes/hermes-home \
HERMES_ENABLE_PROJECT_PLUGINS=true \
hermes
```

权衡：

- 优点：不污染默认 `~/.hermes/config.yaml`。
- 优点：插件代码、启用配置、DeepScientist runtime 数据都在项目目录。
- 缺点：Hermes sessions、Hermes skills、Hermes memory、provider config 也会跟随这个项目本地 `HERMES_HOME`，可能需要额外配置 API/provider。

## 4. 给后续 Hermes agent 的执行顺序

当用户给出目标项目目录并要求安装本插件时，agent 应按以下顺序执行：

1. 读取本文档。
2. 确认 `<plugin-source>` 和 `<target-project>`。
3. 检查 `<plugin-source>/plugin.yaml`、`__init__.py`、`docs/USAGE.md`、`docs/AGENT_PROJECT_INSTALL.md`。
4. 检查目标安装目录是 `<target-project>/.hermes/plugins/deepscientist/`。
5. 用 `rsync -a --delete` 复制插件源码，并排除 `.git/`、`__pycache__/`、`.pytest_cache/`、`test/logs/`、`*.pyc`。
6. 根据用户偏好选择：
   - 当前 Hermes home allow-list 模式；或
   - 严格项目本地 Hermes home 模式。
7. 确保启动命令包含 `HERMES_ENABLE_PROJECT_PLUGINS=true`。
8. 执行 source tree smoke。
9. 提醒用户新开 Hermes session 或从项目目录重新启动 Hermes。
10. 在最终回复中写明：插件安装目录、DeepScientist runtime 目录、启用方式、验证结果、是否修改 `$HERMES_HOME/config.yaml`、完成时间。

## 5. README 短 prompt 的用法

README 中的“项目级安装 prompt”是给用户复制给 Hermes agent 的简短指令。agent 收到后必须先阅读本文档，再执行安装。不要只凭 README 短 prompt 猜测安装步骤。

## 6. 最终回复模板

```text
已完成 DeepScientist 原生插件项目级安装。

插件代码目录：<target-project>/.hermes/plugins/deepscientist/
DeepScientist runtime 目录：<target-project>/DeepScientist/
项目插件扫描：通过 HERMES_ENABLE_PROJECT_PLUGINS=true 启用
插件 allow-list：<说明是否修改了 $HERMES_HOME/config.yaml，或是否使用项目本地 HERMES_HOME>
验证：<列出 source tree smoke、/ds help、/ds doctor 等结果>
未执行：未安装到全局 Hermes plugin 目录；未修改 Hermes core；未调用全局 npm ds；未启用 Web UI/TUI/raw MCP。
完成时间：<YYYY-MM-DD HH:MM:SS +0800>
```
