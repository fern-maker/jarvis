# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Jarvis is a personal AI assistant ("always listening", remembers context) being built for the
Nebius × NVIDIA AI Hackathon (Personal AI Track). Submission deadline: October 30, 2026.

**Current state: this repo is a scaffold.** Nearly every module under `src/` and `training/` is an
empty file or a single-line comment describing its intended purpose — there is no working
implementation yet. Do not assume any described behavior actually exists; check the file contents
before relying on them, and treat the comments below as design intent, not documented fact.

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
- `src/knowledge/memory.py` — persistent memory, backed by `data/memories.json` and
  `data/embeddings.db` (both gitignored)
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

- `training/prepare_data.py` → `training/fine_tune.py` → `training/evaluate.py`
- Training data lives in `training/data/raw/training_data.jsonl`, one JSON object per line:
  ```json
  {"memory_context": {"user_preferences": [...], "known_facts": [...]},
   "conversation": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
   "tags": [...], "category": "...", "difficulty": "easy|medium|hard"}
  ```
  `memory_context` captures the simulated memory state going into the conversation, so examples
  build on each other's established preferences/facts. Nebius fine-tuning expects JSONL with the
  `conversation` field; `memory_context`/`tags`/`category`/`difficulty` are this project's own
  metadata for organizing examples (guideline: 300–500 high-quality examples, quality over
  quantity).
