# Zep Context plugin maintainer instructions

This repository hosts marketplace catalogs at the root and **one plugin
package** at `plugins/zep-context/`. That directory is the plugin root for
Agent Plugins 1.0.0 (including Cursor), Claude Desktop Chat / Cowork, and
ChatGPT Work.

## Package architecture

- Keep a single plugin root: `plugins/zep-context/`. Do not put `plugin.json`,
  `mcp.json`, `.mcp.json`, or `skills/` at the repository root (ChatGPT
  rejects marketplace `source.path` of `"./"`).
- Keep one skill file: `plugins/zep-context/skills/zep-context/SKILL.md`.
  Do not symlink it outside the plugin root — Codex/ChatGPT drop outbound
  symlinks on install (openai/codex#24770).
- Keep the plugin name `zep-context` and version identical in:
  - `plugins/zep-context/plugin.json`
  - `plugins/zep-context/.claude-plugin/plugin.json`
  - `plugins/zep-context/.codex-plugin/plugin.json`
- Keep `plugins/zep-context/plugin.json` and `plugins/zep-context/mcp.json`
  conformant to Agent Plugins 1.0.0.
- Preserve `plugins/zep-context/.claude-plugin/plugin.json` and
  `plugins/zep-context/.mcp.json`; Claude support must not depend on Claude
  adopting the portable format.
- Preserve `plugins/zep-context/.codex-plugin/plugin.json`; OpenAI support
  must not depend on OpenAI adopting the portable format.
- `.codex-plugin/` is the package format used by ChatGPT Work; this plugin is not
  positioned for Codex coding workflows.
- Keep every `.mcp.json` and `mcp.json` pointed at the production Zep Context MCP Server
  endpoint `https://api.getzep.com/mcp` (HTTP / `streamable-http` as required).
- Cursor loads the Agent Plugins package as-is. Do not add
  `plugins/zep-context/.cursor-plugin/` unless we need Cursor-only components
  (rules, agents, commands, hooks, or variables). Auth stays client-managed
  OAuth; do not put API keys or `${VAR}` headers in `mcp.json`.
- Keep `plugins/zep-context/assets/logo.png` and reference it from
  `.cursor-plugin/marketplace.json` (`logo`: `assets/logo.png`). Agent Plugins
  `plugin.json` has no logo field.
- Keep Terms of Service and Privacy Policy links highly visible in
  `README.md` and `plugins/zep-context/README.md`, pointing at
  https://www.getzep.com/legal/terms/ and
  https://www.getzep.com/legal/privacy/. Do not invent a plugin-only legal
  page; this plugin uses the Zep Context MCP Server.
- This repository hosts its own marketplace catalogs
  (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
  and `.cursor-plugin/marketplace.json`). Plugin `source` entries must stay
  same-repo paths so install does not require a second GitHub clone. Claude
  and ChatGPT catalogs point at `./plugins/zep-context`; the Cursor catalog
  uses `metadata.pluginRoot` `plugins` and `source` `zep-context`.

## Releasing

### Repo ritual (always)

For runtime content changes (skill, manifests, MCP package config):

1. Run `python3 scripts/plugin_manifests.py set <version>`.
2. Add a `CHANGELOG.md` entry.
3. Validate the Claude plugin package and the marketplace catalog separately.
   Repo-root `.claude-plugin/` is the marketplace only;
   `claude plugin validate .` checks the catalog:

   ```bash
   claude plugin validate plugins/zep-context/.claude-plugin/plugin.json --strict
   claude plugin validate . --strict
   ```

4. Run `python3 scripts/plugin_manifests.py --check` (includes marketplace
   same-repo source checks).
5. Run `python3 scripts/validate_agent_plugin.py` and confirm
   `.github/workflows/test-plugin.yml` passes.
6. Open a PR and merge to the default branch.

There is no npm publish, GitHub Release, or required git tag for this package.
The Context MCP Server at `https://api.getzep.com/mcp` ships separately —
server-only changes do not require a plugin version bump unless package
metadata or the skill change too.

Bump the synced `version` fields whenever you want installed clients to treat
the package as new. With an explicit version set, hosts often cache by that
string and skip updates if it is unchanged.

### Distribution channels

How a merge reaches users depends on the channel. This repo is the source of
truth; channels differ in what happens after merge.

#### Claude Team / Enterprise org marketplace (primary internal path)

Not Anthropic's official curated marketplace. Org owners distribute via a
manual ZIP marketplace and/or a private GitHub-synced marketplace.

- **GitHub-synced marketplace:** connect a private repo (this plugin repo, or a
  marketplace catalog that points at it). Manual **Update** always works.
  Optional **Sync automatically** runs only when a PR that includes a plugin
  **version bump** is merged to the default branch — direct pushes do not
  auto-sync. Syncs can take up to ~30 minutes.
- **Manual ZIP upload:** uploading a package with the same plugin name
  overwrites the previous org copy; no GitHub merge required for that path.

#### This repository as Claude marketplace

```bash
claude plugin marketplace add getzep/zep-context-plugin
claude plugin install zep-context@zep-context
```

Marketplace entries must stay free of `version`; the host resolves the release
from this package's manifests. Ordinary plugin releases do not need a separate
marketplace PR elsewhere. This is still not Anthropic's official marketplace.

#### Anthropic official marketplace (later)

Curated by Anthropic; inclusion and updates are not "merge this repo and it
ships." Treat as a separate submission / review process when public listing
is in scope.

#### ChatGPT Work — workspace share and local / repo marketplaces (internal)

Not the universal public Plugins Directory.

- **Workspace share:** install/test from the ChatGPT desktop app (Work), then
  Share to members or groups. GitHub merge alone does not propagate the
  package; re-share or refresh the local install as needed.
- **Local / repo / personal marketplaces** (`.agents/plugins/marketplace.json`
  or git-backed marketplace sources): the entry's `source.path` must be
  `./plugins/zep-context` (not `"./"`). Update the package or marketplace
  source, then restart / refresh so the host reloads. OpenAI caches installed
  copies by marketplace + name + version.

#### OpenAI universal public Plugins Directory (later)

Official public listing. Submit through the OpenAI plugin submission portal
(review → Publish). Updates require a new draft with a **new** manifest
`version`, release notes, resubmit, approval, then Publish again. Merging to
GitHub does not update the live directory listing by itself. Skills may be
snapshotted at review time; live MCP tool calls still hit the production
Context MCP Server endpoint.

#### Cursor — local install and team marketplace

Cursor loads Agent Plugins from `plugins/zep-context/` with no extra per-plugin
manifest. Local development:

```bash
mkdir -p ~/.cursor/plugins/local
ln -s "$(pwd)/plugins/zep-context" ~/.cursor/plugins/local/zep-context
```

Reload the Cursor window, then confirm the skill and MCP server under
**Customize**. The Context MCP Server uses OAuth; the first tool call should
open Zep sign-in.

- **Team marketplace:** import this GitHub repository. Cursor reads
  `.cursor-plugin/marketplace.json` and resolves `source` `zep-context` under
  `pluginRoot` `plugins`.
- **Official Cursor Marketplace:** submit this GitHub repository at
  [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish)
  while signed into the Cursor account that should own the listing. Cursor
  reviews identity, code, and every later update; request a re-index after
  changes. Merging to GitHub does not publish or update the public listing.
  The plugin must stay free, Apache-2.0, and public. Keep ToS/privacy links
  visible in the READMEs.
