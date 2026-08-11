# Requirements — One-Word Relay (working title)

**Version:** 0.1
**Status:** draft
**Date:** 2026-08-11
**Owner:** Wattanit
**Companion documents:** Technical Specification v0.1 (downstream, draft)

This document owns WHAT the One-Word Relay POC must do and WHY it exists. It defers HOW the system is built to the Technical Specification. Per the SFD scale rule (G-2), no separate Design Guideline is produced: this project has no human-facing surface beyond a plain CLI, so the minimal voice/naming decisions it needs are folded into this document instead.

## Purpose and Motivation

1. Validate, cheaply, whether a controlled-divergence mechanism — private per-player intent, a shared transcript, and randomized forgetfulness/confusion — can make several LLM agents playing a one-word-at-a-time game actually derail each other the way humans do, rather than converging on a bland shared answer. This is the risk the project exists to test; if it fails, nothing else about the system matters.
2. Keep the divergence mechanism tunable — one global "drunk" parameter plus per-player multipliers — so the funny setting can be found by experimentation instead of fixed by hand.
3. Keep the POC cheap to build and change (CLI only, one configurable model endpoint) so playtesting iterations are fast.

## Scope

**In scope:** a single-session, single-process CLI program implementing the round-robin one-word game with private intent, forgetfulness, confusion, the drunk parameter, and a complete session log (FR-1 through FR-21, HC-1 through HC-3 below).

**Explicitly deferred** (door named for each):
- Mid-game intent updates (letting a player's private intent drift or be revised during a session) — deferred until the fixed, one-shot intent in this version is shown to produce the intended disruption. Door: a future version's turn engine, once FR-3's single-shot approach has been playtested.
- Per-player model override (different players backed by different models) — deferred until shared-model divergence (personas + intent + impurities alone) is shown insufficient. Door: an extension of FR-19/FR-20's configuration schema.
- A more deliberate stopping condition (an external judge call, or a player empowered to end the round) beyond the fixed budget + sentence-boundary pause — deferred until the FR-14/FR-15 approach is shown too abrupt or too loose in playtesting. Door: a future version's flow-control subsystem.
- Multi-session history or persistence across games — deferred until a single session's mechanic is validated as funny at all. Door: a future version's session/config layer.

**Out of scope** (reason given):
- A graphical or web front end — the POC's only open question is whether the divergence mechanic is funny; a UI layer spends engineering effort without helping answer that.
- Human participants taking a turn in the round-robin — this would turn the system from "test an LLM behavior" into a party-game product, a different validation question than this POC exists to answer.
- A dedicated content-moderation layer beyond whatever the configured model endpoint itself enforces — this POC runs against an endpoint the owner controls (e.g. a local Ollama instance); duplicating the provider's own moderation responsibility inside an internal tool isn't justified here.
- Persona or model learning across sessions — no persistence requirement exists yet in this version, so designing for it now would be speculative.

## Hard Constraints

- **HC-1.** A player's private intent, and any candidate words discarded during selection, must never appear in the shared transcript or in any other player's model context — only the single extracted word per turn crosses that boundary. This is the mechanism the entire premise depends on; leaking either breaks the "each player only ever sees the group's actual output" premise that makes the disruption effect meaningful. A release that violates this is defective. This constraint governs what crosses between the game's own components — a private log written for the human owner's later review (FR-21) is never read by any agent during play and does not violate it.
- **HC-2.** The system must work against any endpoint that speaks the OpenAI-compatible chat-completions API — reachable through configuration (base URL, model name, optional API key) alone, with no code change — including but not limited to a local Ollama instance. Hard-coding one provider defeats the stated reason this system exists as a custom-endpoint design. A release that requires code changes to switch endpoints is defective.
- **HC-3.** With the global drunk parameter set to 0, no forgetfulness or confusion may trigger for any player for the entire session, implemented as an explicit deterministic bypass rather than a probability calculation that merely evaluates to zero. Drunk=0 is the sober control condition this POC's central claim is tested against; any accidental leak invalidates that comparison. A release where this leaks is defective.

## Functional Requirements

### Game Setup

- **FR-1.** At session start, the CLI collects the number of players (2–6 inclusive) and the single prompt/question the group must answer, before the first turn begins.
- **FR-2.** Each player is configured with a persona profile (name plus a personality prompt) loaded from a config file at session start; no in-session persona creation is required for the POC.
- **FR-3.** Each player is initialized with a private intent — a self-decided direction for its answer — via one model call per player, made after persona/prompt loading and before the first turn. This intent is generated once per session and is not regenerated mid-game.

### Turn Mechanics

- **FR-4.** Turns proceed in a fixed round-robin order across all players, set once at session start and unchanged for the session's duration.
- **FR-5.** Exactly one whole word is appended to the shared transcript per turn, attributed to the acting player.
- **FR-6.** Word extraction respects real word boundaries in the model's decoded output; a partial word (a broken token fragment) is never appended.

### Context Assembly

- **FR-7.** On a normal turn, the acting player's model call is given that player's persona prompt, its private intent, the original prompt/question, and the full shared transcript so far.
- **FR-8.** On a turn where forgetfulness triggers (FR-11), the acting player's model call instead receives only its persona prompt, its private intent, and the last *k* words of the shared transcript — the original question and earlier words are withheld, though framing that tells the player it is mid-answer is preserved so the output reads as a lost thread, not disconnected noise.

### Word Selection and Impurities

- **FR-9.** Each turn generates multiple (2 or 3) short candidate continuations from independent model calls using the same turn context, before any single word is chosen.
- **FR-10.** On an unaffected turn, the word chosen is the majority word among the candidates; ties are broken by taking the first-generated candidate.
- **FR-11.** Forgetfulness and confusion are each rolled independently, once per turn, with a probability equal to the global drunk parameter times that player's own forgetfulness/confusion multiplier from its persona profile. Either, both, or neither may trigger on a given turn.
- **FR-12.** On a turn where confusion triggers, the word chosen is one of the non-majority candidate words, chosen at random among them; if every candidate agrees (no minority word exists), confusion has no visible effect that turn.
- **FR-13.** Setting the global drunk parameter to zero must deterministically disable both forgetfulness and confusion for the entire session, regardless of any per-player multiplier (see HC-3).

### Stopping and Flow

- **FR-14.** After every word is appended, the system checks whether that word ends in sentence-terminal punctuation (`.` `!` `?`); if so, the session pauses and asks the user whether to continue.
- **FR-15.** The system also enforces a configurable fixed turn budget; if the budget is reached without a sentence boundary having occurred, the session pauses and asks the same continue/stop question, rather than cutting the transcript off mid-word or mid-sentence.
- **FR-16.** Choosing to continue resumes turn order exactly where it left off; choosing to stop ends the session and prints the complete transcript as built so far.

### CLI Interaction

- **FR-17.** Each newly appended word is printed as it's produced, attributed to the acting player's name, so the user watches the answer assemble turn by turn rather than seeing only a final result.
- **FR-18.** CLI output stays plain, unadorned text — no color, animation, or decorative chrome is required for the POC — consistent with the project's ceremony-free interface preference.

### Model Client

- **FR-19.** Every model call in the system (persona-intent init and per-turn candidate generation alike) is made against one user-configured OpenAI-compatible chat-completions endpoint, using one shared model for every player — no per-player model override exists in this version.
- **FR-20.** The drunk parameter, per-player probability multipliers, turn budget, forgetfulness window size (*k*), and candidate count per turn must all be configurable by the user without code changes.

### Logging

- **FR-21.** The system writes a complete log of every session: every player's persona and generated private intent, and for every turn — whether forgetfulness/confusion rolled, the exact context assembled, every candidate completion generated, the selected word, and which rule selected it. The log exists so the user can review and tune personas, prompts, and parameters after the fact, and it is retained even if the session halts on an error partway through (see Technical Specification's error handling policy).

## Deliverables and Document Plan

This document is followed by a Technical Specification (v0.1, draft) that defines the module layout, data models, and concrete defaults (drunk, *k*, candidate count) satisfying the requirements above. Per the standard's writing order (G-8), Requirements is written first because the decisions here — what must diverge, what must never leak, what "sober" means — constrain the technical structure more than the reverse. No separate Design Guideline is produced (see charter).

## Open Questions

- Should each player's private intent be revealed at session end, as a comedic payoff once the user chooses to stop? Resolve: owner (Wattanit).
- Should the FR-10 tie-break (first-generated candidate wins) instead favor whichever candidate is closest to that player's own private intent, to keep "sober" turns persona-consistent rather than arbitrary? Resolve: owner, likely after first playtest.
- Is a fixed persona config file (FR-2) sufficient for the POC, or does the owner want an interactive persona-builder step in the CLI? Resolve: owner.
- Does this project need a real name, or does "One-Word Relay" stand as a working title through the POC phase? Resolve: owner.
- Is FR-21's log read-only for human review in this version, or should a halted session (per the error handling policy) be resumable from it? Resolve: owner.
