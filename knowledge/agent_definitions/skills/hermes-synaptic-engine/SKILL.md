---
name: hermes-synaptic-engine
description: Use this skill to query, navigate, and propose new skills into the Hermes Knowledge Hub (~/.hermes-hub) using Spreading Activation and FastMCP tools.
---

# Hermes Synaptic Engine Skill

## Purpose
This skill equips the agent to leverage the Spreading Activation Knowledge Graph in `~/.hermes-hub`.

## Procedures

### 1. Resolving Context Before Tasks
Call `resolve_context` with key terms from the prompt:
- `resolve_context(prompt="stripe webhook idempotency raw body", threshold=0.60, max_hops=2)`

### 2. Proposing a Quarantined Draft Skill
When discovering a reusable solution or fixing a tricky bug:
- `propose_skill(id="...", title="...", type="skill|pattern|antipattern", tags=[...], procedure_markdown="...")`

### 3. Promoting a Skill
When promoting a validated draft to active status:
- `validate_and_promote_skill(draft_id="...", related_nodes=["..."])`
