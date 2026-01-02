# CLAUDE.md - Takopi Fork

This is a personal fork of [banteg/takopi](https://github.com/banteg/takopi).

## Feature Implementation Process

**CRITICAL: Interview before implementing**

Before implementing any new feature from the roadmap or user request:

1. **Read the roadmap** - understand the planned design
2. **Ask clarifying questions** using AskUserQuestion tool:
   - Confirm the approach/architecture
   - Clarify any ambiguous requirements
   - Present options if multiple valid approaches exist
   - Verify scope (what's in, what's out)
3. **Wait for user approval** before writing code
4. **Then implement** based on confirmed requirements

Do NOT autonomously implement features without this interview step.

## Git Workflow

**CRITICAL: Fork-Only Development**

This is a personal fork. **NEVER create PRs to the upstream repository (banteg/takopi).** All work stays on this fork only.

**Remotes:**
- `origin` = `aurelios-lab/takopi` (this fork) - push here
- `upstream` = `banteg/takopi` (original) - NEVER push or PR here

**Rules:**
- Commit directly to `main` branch on this fork
- Push to `origin` only
- **NO PRs to upstream** unless user explicitly requests it
- Feature branches are optional

**If user explicitly requests a PR to upstream:**
- Only then create a PR with `[CC]` prefix in title
- Wait for explicit permission before any operations
