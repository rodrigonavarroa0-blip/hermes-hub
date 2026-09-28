# Antigravity Loop Specification & PRD - Hermes Research Loop

## 1. Objective
Integrate, upgrade, and embed the Repo Research Loop into Hermes Knowledge Hub, enabling automated GitHub pattern discovery, Google Gemini LLM distillation, and native Obsidian notes generation (`~/.hermes-hub/patterns/`).

## 2. Global Execution Rules
* **Atomic Processing:** Complete exactly ONE sub-task per iteration loop.
* **Context Preservation:** Always read `progress.txt` at the beginning of a cycle and update it before exiting.
* **Verification Gate:** Run local test suites or validation commands immediately after modifying files. Do not proceed if tests fail.

## 3. Implementation Checklist
- [x] **Task 1: Design & Architecture** -> Align design decisions and define implementation plan via `/grill-me`.
- [x] **Task 2: Core Research Modules** -> Build `github_source.py`, `distill.py` (Gemini + fallback), `memory_store.py` (Obsidian Vault integration), and `loop.py`.
- [x] **Task 3: Hermes CLI Integration** -> Create `~/.hermes-hub/bin/hermes_research.py` and connect it to Hermes Hub.
- [x] **Task 4: Validation & Verification** -> Run end-to-end research cycle, verify generated Obsidian notes in `~/.hermes-hub/patterns/`, and validate memory query functionality.
