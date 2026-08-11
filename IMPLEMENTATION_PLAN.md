# Implementation Plan - One-Word Relay

This document outlines the step-by-step implementation of the One-Word Relay POC, following the milestones defined in the Technical Specification.

## M1: Core Skeleton with Stub LLM Client
Goal: Prove the mechanical skeleton (turn loop, transcript, logging, selection rules) without needing a live LLM.

### 1.1 Project Structure & Configuration
- [ ] Create package directory `onewordrelay/`.
- [ ] Implement `config.py`:
    - Define `SessionConfig` and `PersonaConfig` data classes.
    - Implement JSON loading for persona configs.
    - Implement environment variable loading for LLM endpoint settings.
- [ ] Create a sample `personas.json` for testing.

### 1.2 Core Data Models & State
- [ ] Implement `agent.py`:
    - `PersonaConfig` (loaded from config).
    - `AgentState` (stores private intent).
- [ ] Implement `transcript.py`:
    - `Transcript` class to manage the list of `(word, player_name)`.
    - Method to render transcript as a plain string (full vs. last *k* words).
    - Sentence-boundary detection (`.`, `!`, `?`).

### 1.3 Stub LLM Client & Word Selection
- [ ] Implement `llm_client.py` (Stub version):
    - A mock client that returns a predefined list of words or random words to simulate candidates.
- [ ] Implement `wordsel.py`:
    - Word-boundary extraction (regex).
    - Majority selection logic (FR-10).
    - Confusion selection logic (FR-12).
    - Probability rolls for forgetfulness/confusion (FR-11) with the `drunk=0` bypass (HC-3).

### 1.4 Logging & Session Loop
- [ ] Implement `logger.py`:
    - JSONL append-only writer with immediate flush.
    - Schema for `init` and `turn` entries.
- [ ] Implement `session.py`:
    - Round-robin turn loop.
    - Integration of `wordsel`, `transcript`, and `logger`.
    - Turn budget enforcement.
    - Stop/Continue flow.

### 1.5 CLI Entry Point
- [ ] Implement `cli.py`:
    - User input for prompt and number of players.
    - Live turn-by-turn printing.
    - Final transcript display.
- [ ] Verify M1 via automated tests for selection logic and a manual run of the stubbed game.

---

## M2: Live LLM Integration and Intent Init
Goal: Move from stubs to real model calls and implement the private intent phase.

### 2.1 Real LLM Client
- [ ] Update `llm_client.py` to use `requests` for OpenAI-compatible `/v1/chat/completions`.
- [ ] Implement error handling: retry once $\rightarrow$ halt and print transcript.

### 2.2 Intent Initialization
- [ ] Implement the intent generation phase in `session.py`:
    - One model call per player before the game starts.
    - Store result in `AgentState.private_intent`.
    - Log `init` entry immediately.

### 2.3 Context Assembly
- [ ] Update `transcript.py` and `session.py` to assemble the prompt:
    - Normal: Persona + Intent + Prompt + Full Transcript.
    - Forgetful: Persona + Intent + Last *k* words.

---

## M3: Forgetfulness and Confusion Mechanics
Goal: Activate the "drunk" parameters and verify the comedic effect.

### 3.1 Probability Tuning
- [ ] Connect the `drunk` parameter from `SessionConfig` to the rolls in `wordsel.py`.
- [ ] Ensure per-player multipliers from `PersonaConfig` are applied.

### 3.2 Playtesting & Refinement
- [ ] Manual playtests with various `drunk` levels.
- [ ] Review session logs to analyze candidate variety and divergence.
- [ ] Tune `max_tokens` and `temperature` in `llm_client.py` for optimal word generation.

## Verification Matrix
| Requirement | Component | Verification Method |
| :--- | :--- | :--- |
| HC-1 (Isolation) | `session.py` / `transcript.py` | Manual code review: ensure private intent never enters `Transcript`. |
| HC-2 (API) | `llm_client.py` | Run against a local Ollama instance. |
| HC-3 (Sober) | `wordsel.py` | Unit test: `drunk=0` must force `forgetfulness=False`. |
| FR-6 (Words) | `wordsel.py` | Unit test: regex extraction on messy LLM output. |
| FR-21 (Log) | `logger.py` | Verify JSONL output contains all candidates and rules. |
