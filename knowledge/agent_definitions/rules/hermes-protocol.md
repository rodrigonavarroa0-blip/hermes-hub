---
description: Mandatory Spreading Activation context retrieval and skill proposal protocol for Hermes Knowledge Hub.
trigger: always_on
---

# Hermes Knowledge Hub Protocol

## Mandatory Workflow for AI Agents

1. **Context Resolution (Pre-Planning)**:
   - Always call `hermes-context-engine:resolve_context(prompt=...)` with the core concepts of the user request before proposing solutions or editing files.
   - Respect and incorporate active patterns and antipattern mitigations retrieved by the synaptic engine.

2. **Global Memory Compliance**:
   - Check `hermes-context-engine:get_global_memory()` to follow the developer's exact tech stack, typing conventions, and security rules.

3. **Knowledge Capture (Post-Execution)**:
   - When completing non-trivial implementations, call `hermes-context-engine:propose_skill(...)` to quarantine new reusable procedures in `drafts/`.
