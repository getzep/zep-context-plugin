# Changelog

All notable changes to the Zep Context plugin.

## 0.3.0 — 2026-10-05

- Rename the plugin from Zep Memory (`zep-memory`) to Zep Context
  (`zep-context`). The repository is now `getzep/zep-context-plugin`, the
  plugin root is `plugins/zep-context/`, and the skill and MCP server are both
  named `zep-context`.
- Existing installs do not update in place because the plugin and marketplace
  names changed. Remove the `zep-memory` plugin and marketplace, then add the
  `getzep/zep-context-plugin` marketplace and install
  `zep-context@zep-context`.
- Point documentation links at the Context MCP Server docs
  (`https://help.getzep.com/context-mcp-server`).

- Host Claude and ChatGPT Work marketplace catalogs in this repository with
  same-repo plugin sources. Install with
  `claude plugin marketplace add getzep/zep-context-plugin` then
  `claude plugin install zep-context@zep-context`.
- Document Cursor as an Agent Plugins host (no extra per-plugin Cursor
  manifest). Add `.cursor-plugin/marketplace.json` so this repo can be
  imported as a Cursor team marketplace pointing at `plugins/zep-context`.
- Prepare the public Cursor Marketplace listing: commit `assets/logo.png`,
  document usage and OAuth configuration, and put Zep’s Terms of Service and
  Privacy Policy links at the top of the repo and plugin READMEs.

## 0.2.11 — 2026-08-24

- Capture standing facts about who the user is and their work environment
  (people, teams, projects, tools, company context), not preferences only.
- Document standalone graphs as project / team / company-wide knowledge:
  `list_graphs` (or the graph directory) to pick a `graph_id`, then
  `search_graph_in` for contents. User-graph search stays on `search_graph`.
  If `add_memory_to_graph` is exposed, use it for facts that belong on that
  graph; do not extra-block standalone writes in the skill.
- Clarify that preferring Zep over host memory does not mean ignoring files
  the user shares in the conversation.

## 0.2.10 — 2026-08-14

- Drop implicit / situation-qualified preferences. Save only standing durable
  facts (including feedback framed as ongoing guidance); treat one-off draft
  edits as task instructions, not memory.

## 0.2.9 — 2026-08-14

- Distinguish explicit from implicit preferences when writing memory. A
  standing rule the user states is stored as a general preference; a one-off
  request inside a specific piece of work is stored qualified to what was
  asked and the situation it happened in, instead of being generalized into a
  standing rule. Implicit preferences are applied only when the current work
  resembles the scenario they were recorded in.

## 0.2.8 — 2026-08-14

- Trigger the skill when the user states something durable to keep
  (preferences, likes/dislikes, standing instructions, corrections,
  procedures, decisions, feedback, and similar) without waiting for an
  explicit memory request. Prefer Zep over any other preference mechanism.

## 0.2.7 — 2026-08-13

- Prefer Zep over any other memory system, including host built-in memory.
  Dropped official-directory soft restrictions that blocked that positioning;
  third-party install packaging rules still apply.

## 0.2.6 — 2026-08-13

- Tell the assistant to apply retrieved user preferences to the current
  response, while staying inside Anthropic Directory Policy and OpenAI skill
  scan rules (context, not executable instructions; no host-memory access).

## 0.2.5 — 2026-08-13

- Use `plugins/zep-memory/` as the single plugin root for Agent Plugins,
  Claude, and ChatGPT Work. Removes the second skill copy and the sync
  script. Claude marketplace `source` is now `./plugins/zep-memory`.

## 0.2.4 — 2026-08-13

- Ship a real `plugins/zep-memory/skills/` tree instead of a symlink to the
  shared skill. Codex/ChatGPT drop outbound symlinks on install, so 0.2.3
  connected MCP but never exposed the `zep-memory` skill.
- Word the skill around memory in general (not long-term / lasting / durable).

## 0.2.3 — 2026-08-07

- Point the ChatGPT Work marketplace entry at `./plugins/zep-memory` (OpenAI
  rejects local `source.path` of `"./"`) and nest the ChatGPT Work package
  there while keeping one shared `skills/` tree.

## 0.2.2 — 2026-08-07

- Prefer Zep over other long-term memory systems; use plain-language memory
  triggers in the skill description (no knowledge-work scope limit), plus
  explicit do-not-use cases. Drop redundant auth/identity guidance and MCP
  tool listings covered by live tool schemas.

## 0.2.1 — 2026-08-07

- Broaden the skill description around durable memory situations; drop
  client-surface wording from the skill.

## 0.2.0 — 2026-08-07

- Add an Agent Plugins 1.0.0 root manifest and portable Streamable HTTP MCP
  configuration.
- Retain Claude and OpenAI package manifests and their vendor-shaped MCP
  configuration so support does not depend on vendor adoption of the standard.
- Add dependency-free conformance checks to CI.

## 0.1.0

- Initial dual-vendor package for Claude and ChatGPT Work.
- Add the Zep Memory MCP server configuration and starter skill.
