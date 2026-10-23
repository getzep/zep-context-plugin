# Zep Context

Zep Context gives the assistant context about you and your business from your
Zep account. It works in **Claude Code**, **Claude Desktop Chat**, **Claude
Cowork**, **Codex**, **ChatGPT Work**, and **Cursor**.

The plugin contains:

- The `zep-context` skill. It tells the assistant when to get context from Zep
  and when to save context to Zep.
- The Zep Context MCP Server at `https://api.getzep.com/mcp`.

## Terms and privacy

**Read these before you install or use this plugin.** They are the terms of
service and the privacy policy for this plugin and for the data that it sends
to Zep.

- **[Terms of Service](https://www.getzep.com/legal/terms/)**
- **[Privacy Policy](https://www.getzep.com/legal/privacy/)**

The plugin files (skill, manifests, and MCP configuration) are licensed
under the [Apache License 2.0](../../LICENSE).

## What the plugin does

| When | Zep tool calls | Data sent to Zep | Data saved in Zep |
|---|---|---|---|
| A request depends on you | `get_user_summary`, `search_graph` | A short search query | None |
| A request asks about your organization's own knowledge | `list_graphs`, `search_graph_in` | A short search query | None |
| You ask to save context, or you tell the assistant a lasting fact or preference about yourself or your work | `add_memory` | One short fact in your words | That fact, in your user graph |
| You ask to add a fact to a project or company graph | `add_memory_to_graph` | One short fact | That fact, in the selected standalone graph |

Each row is one kind of action. The assistant tells you in its reply each time
it saves a fact. The assistant does not save credentials, payment data,
government ID numbers, health data, files, tool results, or full conversations.
To stop saves, tell the assistant not to save context. To change a saved fact,
tell the assistant the correction. Zep Context does not replace the host's
built-in memory or other tools.

## Usage

After you install the plugin and sign in, try these prompts:

- What context do you have about me?
- Search my Zep context for this topic.
- Save this context to Zep: I prefer short answers with a summary first.
- What is in our company handbook graph about travel expenses?

The assistant calls Zep only when a request needs it. It does not call Zep at
the start of a session or for requests that a general answer completes.
Standalone graphs hold project and company-wide knowledge. The assistant
searches them with `list_graphs` and then `search_graph_in` when the project
enables them.

Install and product documentation:
[Context MCP Server](https://help.getzep.com/context-mcp-server).

## Configuration

No API keys, plugin variables, or other secrets belong in this package. The
host manages OAuth sign-in to `https://api.getzep.com/mcp`.

The first Context MCP call starts the Zep sign-in (work email, then identity
provider, then project). You need a Zep account with a project that has the
Context MCP Server enabled. Standalone graphs are available only when your
project has them.

## Troubleshooting

- The assistant says that Zep tools are not available: make sure that the
  plugin is enabled, then sign in to Zep again from the host's MCP settings.
- The assistant finds no context: make sure that you signed in to the correct
  Zep project.
- The assistant cannot find a standalone graph: make sure that your project
  has standalone graphs and that your account can read them.

## Support

- Documentation: [Context MCP Server](https://help.getzep.com/context-mcp-server)
- Issues: [getzep/zep-context-plugin](https://github.com/getzep/zep-context-plugin/issues)
