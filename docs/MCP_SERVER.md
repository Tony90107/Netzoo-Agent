# NetZoo Agent as a local MCP server

`./netzoo-mcp` serves the NetZoo agent over the
[Model Context Protocol](https://modelcontextprotocol.io). Any MCP client that
can start a local (stdio) server can use it: Claude Code, Claude Desktop, Codex,
Cursor, VS Code, Gemini CLI and others. You talk to your assistant as usual;
it passes your request to NetZoo, and NetZoo decides which method fits, asks
for what it needs, plans the run, and returns its answer for the assistant to
show you.

It is the same agent as `./netzoo-web` and `./netzoo-chat`: the same
conversation engine, the same checks, the same session files. A session started
from an MCP client appears in the desktop history with the tag `mcp`.

Contents: [Set up](#1-set-up) · [Connect a client](#2-connect-a-client) ·
[Use it without naming it](#2a-use-it-without-naming-it) ·
[A first conversation](#3-a-first-conversation) · [Tools](#4-tools) ·
[Running analyses](#5-running-analyses) · [Long turns](#6-long-turns) ·
[Sessions and modes](#7-sessions-and-modes) · [Files and paths](#8-files-and-paths) ·
[Settings](#9-settings) · [What the assistant is told](#10-what-the-assistant-is-told) ·
[Limits](#11-limits) · [Troubleshooting](#12-troubleshooting) ·
[For client developers](#13-for-client-developers)

## 1. Set up

You need three things, all of which `./setup` takes care of:

1. Docker installed and running.
2. The `netzoo_agent` image built.
3. A `.env` in the project folder with your OpenRouter key.

Then check that the server can start:

```bash
./netzoo-mcp --check
```

It prints `ready` and the project folder, or says what is missing. Nothing else
needs installing on your computer; the server runs inside the container.

## 2. Connect a client

Every client needs the same single fact: **the command is the absolute path of
`netzoo-mcp`, with no arguments, over stdio.** Use the absolute path, because
the client does not start the server from the project folder. Quote it if it
contains a space.

Your OpenRouter key stays in the project's `.env`. It is never part of a
client's configuration and never appears in a tool result.

### Claude Code

```bash
claude mcp add --scope user netzoo -- /absolute/path/to/netzoo_agent/netzoo-mcp
```

`--scope user` makes the server available in every folder. Without it the
server is registered only for the folder you ran the command in. Check with
`claude mcp list`, or `/mcp` inside a session. Start a new session after adding
it.

### Codex

```bash
codex mcp add netzoo -- /absolute/path/to/netzoo_agent/netzoo-mcp
```

This writes the following to `~/.codex/config.toml`, which you can also add by
hand. Check with `codex mcp list`.

```toml
[mcp_servers.netzoo]
command = "/absolute/path/to/netzoo_agent/netzoo-mcp"
```

Codex requires approval for tools that are not marked read-only, which includes
sending a message to NetZoo. `codex exec` cannot ask you, so there it refuses
those calls unless you run it with `--approve-for-me`.

### Claude Desktop

Settings → Developer → Edit Config, add the entry, then restart the app:

```json
{
  "mcpServers": {
    "netzoo": { "command": "/absolute/path/to/netzoo_agent/netzoo-mcp" }
  }
}
```

### Other clients

Cursor, VS Code, Gemini CLI, Cline and most others take a JSON entry of the same
shape as the Claude Desktop one: a server name and a `command`. Where that file
lives, and whether the top-level key is `mcpServers` or `servers`, depends on
the client; see its documentation for "add a local (stdio) MCP server".

### What has been tried

| Client | Result |
| --- | --- |
| Claude Code 2.1 | Works. Asked, planned, answered NetZoo's question, was told why it could not run a plan with execution off. |
| Codex CLI 0.164 | Works. Registered with `codex mcp add`, asked a method question through `codex exec --approve-for-me`. |
| Plain JSON-RPC over stdio | Works. Planned, previewed, ran PANDA on the toy data, listed and previewed the output. |
| Claude Desktop, Cursor, VS Code, Gemini CLI | Not tried. The server uses nothing beyond standard MCP tools over stdio. |

## 2a. Use it without naming it

Connecting the server does not mean your assistant will use it. A model
decides for each question whether a tool is worth calling, and it already
knows a lot about PANDA and LIONESS, so it tends to answer method questions
itself. Those answers skip NetZoo's checks and can be wrong: in one test a
model said PUMA "adds PPI information" (PANDA already uses PPI; PUMA adds
miRNA).

The server's own instructions tell the model when to ask NetZoo. Some clients
weigh those lightly, especially with many servers connected. What works
reliably is a line in the file your client always reads as your own
instructions:

| Client | File |
| --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` (all projects) or `CLAUDE.md` in one project |
| Codex | `~/.codex/AGENTS.md` (all projects) or `AGENTS.md` in one project |
| Others | the client's "rules" or "custom instructions" setting |

Add this:

```markdown
## NetZoo

When I ask about a Network Zoo method (PANDA, PUMA, LIONESS, OTTER, CONDOR, DRAGON,
GIRAFFE, BONOBO, COBRA, SAMBAR, PORCUPINE, SCORPION and the others), about which method
to use for gene-regulatory, transcription-factor or co-expression network analysis, or
ask to plan or run such an analysis, ask the `netzoo` MCP server (`netzoo_ask`) instead
of answering from your own knowledge, even when I do not mention NetZoo. Write to it in
English, pass on what I said without adding to it, and show me NetZoo's reply. General
biology or statistics questions that name no network method do not need it.
```

Measured with Claude Code on 2026-11-16, five questions that do not mention
NetZoo: three about methods or an analysis (should use NetZoo), one general
biology question and one programming question (should not).

| Model (low effort) | Server instructions only | With the lines above |
| --- | --- | --- |
| Haiku 4.5 | 2 of 3 asked NetZoo (0 of 3 before the server said when to) | not measured |
| Haiku 5.5 | 1 of 3, in both of two runs | 3 of 3, in both of two runs |

Neither control question was ever sent to NetZoo. Five questions are a small
sample; treat this as a direction, not a rate.

You can always tell which kind of answer you got. When NetZoo was asked, the
client shows a `netzoo_ask` tool call and the reply includes a part marked as
NetZoo's own words. Without either, the answer is the model's own.

## 3. A first conversation

Speak to your assistant in any language. It writes to NetZoo in English and
may translate the reply back.

**Ask which method fits.**

> I have expression data from tumour and normal tissue. Which NetZoo method
> shows which transcription factors regulate differently between the groups?
> Ask netzoo.

The assistant calls `netzoo_ask`. NetZoo replies with the methods that fit, what
each needs, and a question that would decide between them. The assistant shows
you the reply and the question, and sends your answer back with another
`netzoo_ask` in the same session.

**Plan a run on your own data.** Put the files inside the project folder first
(for example under `data/my-study/`), then name them:

> Run PANDA with data/my-study/expression.tsv, data/my-study/motif.tsv and
> data/my-study/ppi.tsv.

NetZoo checks the files, asks for anything missing, and returns a plan with the
exact command it would run. Nothing has run at this point.

**Try it on the bundled toy data.** Toy data is only used in test mode, whose
results are for testing the software and are not biological evidence:

> Use netzoo's test mode and run PANDA on the toy data in data/official-toy.

The assistant calls `netzoo_set_mode` with `test`, then `netzoo_ask`. NetZoo
lists the three files it found and asks whether to use them; after your yes it
returns the command preview.

**Run the plan**, if you have turned execution on (see
[Running analyses](#5-running-analyses)). The assistant shows you the plan and
calls `netzoo_execute` after you agree. When the run finishes:

> Show me the first rows of the result.

The assistant calls `netzoo_preview_output` on the file NetZoo reported.

**Come back later.** `netzoo_list_sessions` lists saved sessions, including
those from the desktop app and the terminal; giving a `session_id` to
`netzoo_ask` continues one.

### What a result looks like

Each conversation tool returns one text document. NetZoo's own words are fenced
off from what the server adds:

```
NetZoo session b7516cee | Test mode | waiting for the user

NetZoo's reply (its own words, unchanged):
----------------------------------------
PANDA · DRY RUN
...
Command
run-panda -e data/official-toy/ToyExpressionData.txt -m ... -o outputs/sessions/b7516cee/ToyExpressionData-panda.tsv
----------------------------------------

Plan: PANDA (status: ready)
Inputs:
  - expression_file = data/official-toy/ToyExpressionData.txt [provided]
  ...
plan_hash: 86d347d8ac11...

NetZoo is now asking:
Your PANDA plan is ready. ...

Options NetZoo offered:
1. Execute this plan: ...
   -> netzoo_execute with this plan_hash, after the user agrees

Notes from the NetZoo MCP server (not part of NetZoo's reply):
- A previewed plan is ready. Show the user the plan and the commands NetZoo listed, and call
  netzoo_execute with this session_id and plan_hash only after they agree to run it.
```

The first line gives the session, the mode, and whether NetZoo is waiting for
you, still running, or finished.

## 4. Tools

### Conversation

| Tool | Arguments | What it does |
| --- | --- | --- |
| `netzoo_ask` | `message`; optional `session_id`, `model`, `wait_seconds` | Sends a request, or the answer to NetZoo's question. Without `session_id` it starts a session; with one it continues that session, including a saved one. Returns NetZoo's reply, the question it now has open with its options, and the plan when one was previewed. Runs nothing. Slash commands are refused. |
| `netzoo_wait` | `session_id`; optional `wait_seconds` | Returns the rest of a turn that is still running. When nothing is running, returns the session's current state at once. |
| `netzoo_set_mode` | `mode` (`planning` or `test`); optional `session_id` | Switches mode. Without `session_id` it starts a session in that mode. |
| `netzoo_cancel` | `session_id` | Interrupts the running turn. Steps that had not finished are not reported as done. |
| `netzoo_execute` | `session_id`, `plan_hash`; optional `wait_seconds` | Runs the previewed plan once. **Present only when execution is turned on.** |

### Read-only

These call no model and cost nothing.

| Tool | Arguments | What it does |
| --- | --- | --- |
| `netzoo_list_workflows` | none | The registered workflows, their required and optional inputs, and what each produces. A catalog, not advice: to learn which fits a question, ask NetZoo. |
| `netzoo_list_sessions` | optional `limit`, `query` | Saved sessions, newest first, with status, tags and output files. |
| `netzoo_get_transcript` | `session_id`; optional `last` | The conversation a saved session kept. |
| `netzoo_list_outputs` | optional `path`, `offset` | Files and folders under `outputs/`. |
| `netzoo_preview_output` | `path`; optional `offset` | The start of one output file: up to 40 table rows, array shapes, or text. |

There are no tools that call PANDA, LIONESS or any other method directly. Every
request goes through NetZoo's input checks, planner and evaluator, exactly as
it does in the other interfaces.

## 5. Running analyses

By default a client can ask, plan and preview, but not run. To allow runs, add
this line to `.env`, then reconnect the server in your client (or restart the
client):

```
NETZOO_MCP_EXECUTE=on
```

`./netzoo-mcp --check` reports whether it is on.

A run still takes two separate steps. NetZoo first previews the plan and its
commands; `netzoo_execute` then has to name that plan by its `plan_hash`. A
hash for a plan that has since changed is refused, and the current plan is
returned to be shown again. The approval covers one run.

Two things to know before turning this on:

- NetZoo can check that the plan being approved is the plan that was previewed.
  It cannot check that you read it: that depends on your client asking you
  before it calls `netzoo_execute`. Keep that tool on "ask every time" in your
  client's permissions.
- Closing the client stops the server and interrupts a run in progress. For an
  analysis that takes hours, use `./netzoo-web` or `./netzoo-chat`, where the
  session keeps running.

With execution off, a previewed plan can still be run by opening the same
session in the desktop app.

## 6. Long turns

A tool call waits up to 45 seconds (`NETZOO_MCP_WAIT_SECONDS`) for a turn. If
the turn is not done, the result says the turn is still running and carries
what NetZoo has said so far; `netzoo_wait` returns the rest. Nothing is
returned twice, and the turn itself is not affected by the wait running out.

If your client gives a tool call less than 45 seconds, set
`NETZOO_MCP_WAIT_SECONDS` in `.env` to something shorter than its limit.

## 7. Sessions and modes

- A session is one conversation with NetZoo. Keep passing its `session_id` to
  stay in it; leave it out to start another.
- **Planning mode** is the default: real data, strict input checks. **Test
  mode** allows the bundled toy data and accepts gene labels it cannot verify.
- Sessions are saved as they go. After the server restarts, giving the
  `session_id` to `netzoo_ask` continues the saved session. It keeps the
  conversation and the plan, but not the mode: it is back in planning mode, and
  the first result says so. Switch to test mode again if that is where you were.
- A session left idle for 30 minutes is closed. If it had reached a saved
  state, it can be continued the same way.

## 8. Files and paths

NetZoo reads data only from inside the project folder, which is `/work` inside
the container. When you give a path under the project folder as it is on your
computer, the server rewrites that prefix to `/work` before NetZoo sees it.
Results list output files with both spellings. Files elsewhere on your computer
are not visible to NetZoo; copy them into `data/` first.

Outputs are written under `outputs/` in the project folder.

## 9. Settings

All of these go in the project's `.env`. Reconnect the server after changing
one.

| Variable | Default | Meaning |
| --- | --- | --- |
| `NETZOO_MCP_EXECUTE` | `off` | `on` adds `netzoo_execute`, which runs a previewed plan. |
| `NETZOO_MCP_WAIT_SECONDS` | `45` | How long a tool call waits for a turn before answering that it is still running. |
| `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, ... | as for the other interfaces | The models NetZoo itself uses. The MCP server adds no model of its own. |

## 10. What the assistant is told

The client's model sits between you and NetZoo, so the server gives it
standing instructions:

1. Pass on only what you said, without adding a method, a file or a setting you
   did not state.
2. Leave NetZoo's questions for you to answer, unless you already gave the
   answer.
3. Show NetZoo's reply as it is, and keep its own remarks apart from it.
4. Call `netzoo_execute` only after you have agreed to the plan shown.

These are instructions to a model, not guarantees, and how closely they are
followed depends on the client and its model. If a reply matters, read the part
marked as NetZoo's own words, or open the session in the desktop app, where the
conversation is shown without anything in between.

## 11. Limits

- One session cannot be continued from the desktop app and an MCP client at the
  same time; both would write the same session file.
- Every message to NetZoo uses the OpenRouter models configured in `.env`, as
  in the terminal. Results report the tokens used.
- The reasoning timeline is not sent to the client. Open the session in the
  desktop app to see it.
- Only stdio is offered. There is no network transport, because one would need
  its own authentication before it could be allowed to start analyses.
- `netzoo-mcp` is a Bash script. On Windows, run the client and the script in
  WSL.

## 12. Troubleshooting

Start with `./netzoo-mcp --check`. It reports the common causes: Docker not
installed or not running, no `.env`, or an image that has not been built. When
a client shows the server as failed, its server log holds the same messages;
everything the server prints other than the protocol goes there.

| What you see | Cause and fix |
| --- | --- |
| The server fails to start or shows as disconnected | Docker is not running, or was started after the client. Start Docker, then reconnect the server. |
| The server works in one folder but not another (Claude Code) | It was added without `--scope user`. Add it again with that option. |
| The assistant answers method questions itself | It decided not to use the tool. Add the lines in [Use it without naming it](#2a-use-it-without-naming-it), or say "ask netzoo" in the question. |
| "There is no tool that runs a plan" | Execution is off. See [Running analyses](#5-running-analyses). |
| "MCP tool call requires approval" (`codex exec`) | `codex exec` never asks. Run it with `--approve-for-me`, or use an interactive Codex session. |
| NetZoo cannot find your file | The file is outside the project folder. Copy it into `data/`. |
| "The LLM router was unavailable" | The container could not reach OpenRouter. Check your network and the key in `.env`. |
| A session is back in planning mode | It was continued after a restart. Switch mode again; see [Sessions and modes](#7-sessions-and-modes). |
| The client times out while the server starts | Starting the container takes a few seconds. Raise the client's start-up limit for this server (in Codex, `startup_timeout_sec` in the server's entry). |

## 13. For client developers

The server is a standard MCP server over stdio and can be driven without any
assistant. One JSON-RPC message per line:

```bash
{ printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"demo","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"netzoo_list_workflows","arguments":{}}}'; sleep 5; } \
  | ./netzoo-mcp
```

The `sleep` keeps stdin open until the answers are written: the server stops
as soon as its input closes, as it should when a client exits.

- Conversation tools return **text only**. A client given both text and
  structured content may show its model the structured form instead, and the
  text is where NetZoo's reply is marked as its own. The same fields are
  available to a program under `_meta["netzoo/turn"]`: `session_id`, `status`
  (`waiting_for_user`, `running`, `stopped`, `error`), `mode`, `reply`,
  `question`, `options`, `plan`, `plan_hash`, `previewed`, `can_execute`,
  `outputs`, `usage`, `errors`.
- Read-only tools return the same JSON as text and as structured content.
- A refused call sets `isError` and still describes the session's state.
- While a turn runs, the server sends progress notifications when the request
  carried a progress token.
- stdout carries only the protocol. Everything else the server or the agent
  prints goes to stderr.

The design is in `docs/superpowers/specs/2026-11-12-mcp-server-design.md`. In
short: the terminal and the desktop window are two drivers of one
`ConversationMachine`, and this is a third. `mcp_server/turn.py` adapts the
stream of events a worker publishes into the single result an MCP tool returns;
nothing below the existing `WorkerDriver` was changed.
