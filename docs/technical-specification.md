# Technical Specification — One-Word Relay (working title)

**Version:** 0.1
**Status:** draft
**Date:** 2026-08-11
**Owner:** Wattanit
**Companion documents:** Requirements v0.1 (upstream, draft)

This document owns HOW the One-Word Relay POC is built. Every choice below cites the upstream Requirements ID it satisfies. It does not restate WHAT or WHY — see Requirements v0.1 for that.

## System Structure

A single Python process, run from source (no packaging for a POC — satisfies Requirements' CLI-only scope). Modules:

- `config.py` — loads session and persona settings from a config file (FR-2, FR-20).
- `llm_client.py` — thin wrapper over an OpenAI-compatible `/v1/chat/completions` endpoint (HC-2, FR-19).
- `agent.py` — `PersonaConfig` and `AgentState` (private intent, per-player multipliers).
- `wordsel.py` — candidate generation, word-boundary extraction, and the forgetfulness/confusion rolls (FR-6, FR-9–FR-13).
- `transcript.py` — shared transcript state, context assembly for normal vs. forgetful turns (FR-7, FR-8), sentence-boundary detection (FR-14).
- `logger.py` — append-only session log writer (FR-21).
- `session.py` — the turn loop and stop/continue flow (FR-4, FR-5, FR-15, FR-16).
- `cli.py` — entry point: setup prompts, live turn-by-turn printing, final transcript (FR-1, FR-17, FR-18).

## Execution Model

Fully synchronous, single-threaded, strict round-robin (FR-4). Concurrency is not used for the POC: FR-5 requires exactly one word appended per turn in a fixed order, and a CLI POC has no latency budget that justifies the complexity of concurrent transcript writes. Within one turn, the 2–3 candidate calls (FR-9) are issued sequentially to the LLM client — initial choice, tune with use (see Open Items).

## Data Models

- **`SessionConfig`**: `prompt: str`, `num_players: int` (2–6, FR-1), `turn_budget: int` (FR-15), `k_forgetfulness: int` (FR-8), `num_candidates: int` (FR-9), `drunk: float` (FR-13).
- **`PersonaConfig`**: `name: str`, `personality_prompt: str`, `forgetfulness_multiplier: float`, `confusion_multiplier: float` (FR-2, FR-11).
- **`AgentState`**: `persona: PersonaConfig`, `private_intent: str` — populated once during init (FR-3), held only in process memory, never serialized into the transcript (HC-1).
- **`Transcript`**: an ordered list of `(word: str, player_name: str)` tuples (FR-5). Two renderings are derived from it: a plain joined string for model context (FR-7), and the attributed form for CLI display (FR-17).
- **`CandidateSet`**: the list of raw candidate completions returned for one turn, held only long enough to extract one word each; discarded from working state immediately after selection — it lives on only in the log (FR-21), never in the transcript or any other player's context (HC-1).
- **`LogEntry`**: one JSON object per logged event. An `init` entry per player: `player_name`, `persona_prompt`, `private_intent`. A `turn` entry per turn: `turn_index`, `player_name`, `forgetfulness_triggered: bool`, `confusion_triggered: bool`, `context_sent: str`, `candidates: list[str]`, `selected_word: str`, `selection_rule: "majority" | "confusion" | "fallback"`.

## Subsystem: LLM Client

`llm_client.py` sends every call — intent init and per-turn candidates alike — to one configured `base_url` + `model` (+ optional `api_key`) via `/v1/chat/completions` (HC-2, FR-19). One shared client/model config object serves all players (FR-19; no per-player override in this version). Each request: `messages = [{"role": "system", "content": persona_prompt}, {"role": "user", "content": assembled_context}]`, a small `max_tokens` (initial value ~20, tune with use — enough to extract one clean word), and nonzero `temperature` (initial value ~0.9, tune with use) so repeated candidate calls on the same context naturally disagree sometimes, which is what FR-10/FR-12's majority/minority selection needs.

## Subsystem: Intent Initialization

Runs once per player before the turn loop starts (FR-3). One call per player: system message is that player's persona prompt; user message is the original prompt plus an instruction to silently decide a private direction and answer with only that intent, nothing else. The response is stored as `AgentState.private_intent` and is never included in the shared transcript, never sent as part of any other player's context, and never printed by the CLI during play (HC-1). It is written to the session log as an `init` entry (FR-21) immediately after generation. Whether it is printed to the CLI at session end is a separate open question (see Requirements' Open Questions) and is not implemented in v0.1.

## Subsystem: Turn Engine

Per turn, in round-robin order (FR-4):

1. Roll forgetfulness: `random() < drunk * agent.forgetfulness_multiplier`. If `drunk == 0`, skip the roll entirely via an explicit `if drunk == 0: forgetfulness = confusion = False` early return — not a probability evaluating to zero — so HC-3 holds regardless of any multiplier or floating-point edge case.
2. Assemble context per FR-7 (normal) or FR-8 (forgetfulness triggered), using `transcript.py`.
3. Issue `num_candidates` sequential calls to the LLM client with that context; from each response, extract the first whole word using a word-boundary-safe split (regex on whitespace/punctuation, not the model's raw tokens) — satisfies FR-6.
4. Roll confusion the same way as step 1.
5. Select the turn's word: if confusion did not trigger, take the majority word among candidates, first-generated candidate breaking ties (FR-10). If confusion triggered, pick uniformly at random among the non-majority words if any exist; if all candidates agree, fall back to the majority word and confusion has no visible effect this turn (FR-12 — this fallback is the honesty clause: confusion is not guaranteed to be visible every time it fires).
6. Append `(word, player_name)` to the transcript and print it immediately (FR-5, FR-17).
7. Write a `turn` log entry capturing the context sent, every candidate, the selected word, the selection rule, and both roll outcomes (FR-21) — written before step 6's print returns, so a log entry exists even if the process is killed immediately after.

## Subsystem: Session Logger

`logger.py` appends one JSON object per line (JSONL) to a session log file, one line per `LogEntry` (FR-21): one `init` line per player, then one `turn` line per turn, in the order they occur. Each line is written and flushed to disk immediately rather than buffered — an append-only, flush-per-line file is crash-safe and streamable, and it means the error handling policy's "print the transcript built so far" on a halt already has a matching complete log on disk with no separate save step. The logger is write-only from the game's perspective: nothing in `session.py`, `agent.py`, or `wordsel.py` ever reads the log back during play, which is what keeps FR-21 from reopening HC-1.

## Subsystem: Stopping and Flow Control

After every append: check the word for a trailing `.`, `!`, or `?` (FR-14); separately check the turn count against `turn_budget` (FR-15). Either condition pauses the loop and prompts the CLI user (continue/stop). Continuing resumes the round-robin pointer without resetting any state (FR-16); stopping prints the final transcript and exits.

## Configuration

A single JSON config file, loaded at startup — JSON is the initial choice since Requirements states no format preference and it needs no extra dependency (tune with use if personas prove painful to hand-write; see Open Items). Contains a `session` block (`turn_budget`, `k_forgetfulness`, `num_candidates`, `drunk` — `prompt` and `num_players` are collected interactively per FR-1 instead) and a `personas` array (`name`, `personality_prompt`, `forgetfulness_multiplier`, `confusion_multiplier`). Endpoint config (`base_url`, `model`, `api_key`) is read separately from environment variables (or a `.env` file), kept out of the persona file so credentials are never committed alongside personas. The log file path defaults to `sessions/<start-timestamp>.jsonl` relative to the working directory (initial value, tune with use) and is overridable in the `session` config block.

## Error Handling Policy

If any LLM call fails (unreachable endpoint, non-200 response): retry once, and if it still fails, halt the session and print the transcript built so far — never silently substitute a fake word for a failed call. Faking a turn would corrupt the exact thing this POC exists to observe (the model's real behavior), so a visible halt is preferred over a quiet cover-up. Because the logger flushes per line (see Session Logger subsystem), every turn logged before the failing one is already durable on disk when the halt happens — satisfying FR-21's retention-on-error clause with no extra recovery logic. No further resilience (backoff, request queuing) is in scope for a local, single-user POC.

## Dependencies

`requests` for HTTP calls to the OpenAI-compatible endpoint — no vendor SDK, since HC-2 exists specifically to avoid provider lock-in and an SDK reintroduces it. Standard library only otherwise (`random`, `json`, `re`). Any further third-party dependency must justify itself against Requirements' first priority (proving the comedic mechanic) before being accepted.

## Build and Release

No packaging or release process for v0.1: run directly from a source checkout (e.g. `python -m onewordrelay.cli`). The deliverable is the running script plus this document suite, matching Requirements' CLI-only, single-session scope.

## Testing Strategy

Automated unit tests cover only the deterministic logic: word-boundary extraction (FR-6), majority/minority selection including the confusion fallback (FR-10, FR-12), the `drunk == 0` bypass (HC-3), sentence-boundary detection (FR-14), turn-budget pausing (FR-15), and log line schema validity — every emitted line parses as JSON and matches the `LogEntry` shape (FR-21). Behavior that depends on the live model — intent quality, candidate variety, whether forgetfulness actually reads as "lost the thread" — is checked by manual playtest against a running Ollama instance, since what's being tested (funniness) has no automatable pass/fail; the log is what that manual review is read from.

## Milestones

- **M1** — Turn engine runs end-to-end against a stub LLM client returning fixed responses, `drunk=0`, and writes a complete, schema-valid log alongside the transcript. Proves the mechanical skeleton (FR-4, FR-5, FR-7, FR-14–FR-17, FR-21) independent of any real model.
- **M2** — Wired to a live Ollama endpoint through the OpenAI-compatible client (HC-2), intent init working, `drunk=0`. Proves the real-model integration in the sober control condition that HC-3 depends on.
- **M3** — Forgetfulness and confusion active with `drunk > 0`, tunable per persona. Proves the actual comedic mechanic this POC exists to test.

## Open Items

- Whether candidate generation (step 3 of the turn engine) should run concurrently once real Ollama latency is measured against realistic `turn_budget` sizes, or whether sequential calls are fast enough for a CLI POC. Resolve: owner, after first live playtest.
- Whether JSON remains sufficient for the persona config file, or a more forgiving format (e.g. YAML) is worth the added dependency once personas are hand-written more often. Resolve: owner.
