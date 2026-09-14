# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Jarvis is a personal AI assistant ("always listening", remembers context) being built for the
Nebius × NVIDIA AI Hackathon (Personal AI Track). Submission deadline: October 30, 2026.

**Current state: this repo is mostly a scaffold.** Most modules under `src/` are still an empty
file or a single-line comment describing intended purpose — there is no working implementation for
them yet. Two exceptions with real, working code: `src/knowledge/memory.py` (SQLite-backed memory)
and `training/prepare_data.py` (fine-tuning data prep), described below. Do not assume any other
described behavior actually exists; check the file contents before relying on them, and treat
comments in unimplemented files as design intent, not documented fact.

## Setup / running

```bash
pip install -r requirements.txt   # currently empty — no dependencies pinned yet
python -m src.main
```

There are no test, lint, or build commands configured in this repo yet (no test framework,
linter config, or CI present).

## Architecture (intended, per stub comments)

The design splits into a background service (always-on listening/agent loop) and a UI that talks
to it over IPC, plus a separate offline fine-tuning pipeline:

- `src/core/agent.py` — orchestration logic (the agent's decision loop)
- `src/core/nebius_client.py` — calls to the Nebius Token Factory API (the model backend)
- `src/audio/wake_word.py` — background wake-word listening
- `src/audio/stt.py` / `src/audio/tts.py` — speech-to-text / text-to-speech
- `src/knowledge/memory.py` — **implemented.** `MemoryManager` class, SQLite-backed (schema in
  `src/knowledge/memory_schema.sql`: `conversations`, `user_preferences`, `web_search_cache`
  tables), data file at `data/memory.db` (gitignored). `load_all_training_data()` loads every
  `training/data/raw/*.jsonl` file for keyword-based recall via
  `recall_relevant_conversations()`. `data/embeddings.db` remains reserved/unimplemented for
  future semantic (vector) search; `data/memories.json` is currently unused by this
  implementation.
- `src/knowledge/web_search.py` — web search integration
- `src/service/daemon.py` — main service loop entry point
- `src/service/event_loop.py` — async event handling
- `src/service/ipc_server.py` — socket server the UI connects to
- `src/ui/main_window.py` / `src/ui/tray.py` — desktop UI and system tray, communicate with the
  daemon via IPC (not directly with the agent)
- `deployment/` — service install files for macOS (launchd plist), Linux (systemd unit), and
  Windows (install.bat) — currently empty stubs

### Training / fine-tuning pipeline

`training/` is a separate pipeline for fine-tuning the assistant's model, decoupled from the
runtime app:

- `training/prepare_data.py` — **implemented.** `training/fine_tune.py` → `training/evaluate.py`
  are still empty (actually calling the Nebius fine-tune API needs credentials/config not yet
  present).
- Training data lives in 8 category files under `training/data/raw/*.jsonl` (`coding`,
  `debugging`, `technical_advice`, `web_search`, `memory_usage`, `task_planning`,
  `jarvis_reference_examples`, `legacy_memory_management` — 85 examples total), one JSON object
  per line:
  ```json
  {"memory_context": {"user_preferences": [...], "known_facts": [...], "past_conversations": [...]},
   "web_search_context": {"query": "...", "sources": [...]},
   "conversation": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
   "tags": [...], "primary_category": "...", "difficulty": "easy|medium|hard"}
  ```
  `memory_context`/`web_search_context` capture simulated memory/search state feeding the
  conversation, so examples build on each other's established preferences/facts.
  `memory_context`/`web_search_context`/`tags`/`primary_category`/`difficulty` are this project's
  own metadata for organizing examples — `prepare_data.py` strips all of it, keeping only
  `conversation` per Nebius's expected fine-tuning format, validates each example, drops exact
  duplicates, and writes a deterministic shuffled 90/10 split to
  `training/data/processed/train.jsonl` / `val.jsonl` (gitignored — regenerate by running the
  script; guideline: 300–500 high-quality examples, quality over quantity).
