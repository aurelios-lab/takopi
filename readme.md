# takopi

🐙 *he just wants to help-pi*

telegram bridge for codex and claude code. runs the agent cli, streams progress, and supports resumable sessions.

## features

stateless resume, continue a thread in the chat or pick up in the terminal.

progress updates while agent runs (commands, tools, notes, file changes, elapsed time).

robust markdown rendering of output with a lot of quality of life tweaks.

parallel runs across threads, per thread queue support.

`/cancel` a running task.

## requirements

- `uv` for installation (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- at least one engine installed:
  - `codex` on PATH (`npm install -g @openai/codex` or `brew install codex`)
  - `claude` on PATH (`npm install -g @anthropic-ai/claude-code`)

## install

- `uv tool install takopi` to install as `takopi`
- or try it with `uvx takopi`

## setup

1. get `bot_token` from [@BotFather](https://t.me/BotFather)
2. get `chat_id` from [@myidbot](https://t.me/myidbot)
3. send `/start` to the bot (telegram won't let it message you first)
4. run your agent cli once interactively in the repo to trust the directory

## config

### config locations

takopi uses a **global + local override** config system:

1. **global config** (required): `~/.takopi/takopi.toml`
2. **local config** (optional): `./takopi.toml` or `./.takopi/takopi.toml` in cwd

local config values are **deep-merged** into global config, with local taking precedence.

### global config example

`~/.takopi/takopi.toml` - shared settings for all projects:

```toml
bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
chat_id = 123456789

[codex]
profile = "takopi"

[claude]
model = "sonnet"
dangerously_skip_permissions = true
```

### project-specific config

create `takopi.toml` in your project directory to override global settings:

```toml
# my-project/takopi.toml

[claude]
# custom system prompt for this project
system_prompt = """
You are a specialized assistant for this project.
Always read config.json before responding.
Be concise and direct.
"""

# can also override other settings
model = "opus"
```

### all claude options

```toml
[claude]
model = "sonnet"                        # claude model to use
allowed_tools = ["Bash", "Read", "Write", "WebSearch"]  # auto-approve these tools
dangerously_skip_permissions = false    # skip all permission prompts (use with caution)
use_api_billing = false                 # use API key billing instead of subscription
system_prompt = "..."                   # appended to claude's system prompt (--append-system-prompt)
```

## usage

start takopi in the repo you want to work on:

```sh
cd ~/dev/your-repo
takopi codex
# or
takopi claude
```

send a message to the bot.

to continue a thread, reply to a bot message containing a resume line.
you can also copy it to resume an interactive session in your terminal.

to stop a run, reply to the progress message with `/cancel`.

default: progress is silent, final answer is sent as a new message so you receive a notification, progress message is deleted.

if you prefer no notifications, `--no-final-notify` edits the progress message into the final answer.

## notes

* private chat only: the bot only responds to the configured `chat_id`
* run only one takopi instance per bot token: multiple instances will race telegram's `getUpdates` offsets and cause missed updates

## development

see [`docs/specification.md`](docs/specification.md) and [`docs/developing.md`](docs/developing.md).
