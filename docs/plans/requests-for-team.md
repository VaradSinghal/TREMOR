# Requests for the team

Changes Mokshad needs in files owned by others. Mokshad does not edit these files directly.

---

## Kostubh (baseline / detectors / severity / alerts)

### Blocking: eval harness (Phase 6, step 4)

`eval/run.py` replays scenarios through parser → window → baseline → detectors → alert manager.
It cannot be built until these interfaces exist, even as final signatures with stub bodies:

1. **Signal type.** This is what a detector returns: fields such as service, signal_type, value, z, window_s and ts.
2. **Detector call signature.** How a detector is constructed and invoked each tick, and what it takes (WindowEngine views, BaselineStore, TemplateMiner, clock?).
3. **`BaselineStore`.** Final signatures for `update` / `get` / `freeze` / `unfreeze` / `is_warm`.
4. **`AlertManager`.** Final signatures for `process_signal` / `resolve` / `get_active`.

### FYI: TemplateMiner API (`app/core/templates.py`)

- Template IDs are `int`, which matches `alerts.TemplateHint.template_id`.
- `add_message(message, *, service="_global", ts=None) -> int`
- `is_new(template_id, now=None) -> bool`: true when the template was first seen after warm-up, or was rare (below the rarity threshold) when it reappeared. The flag stays set for `novelty_ttl_s`.
- `new_templates_in_window(window_s, *, service=None) -> dict[int, int]`: returns `{template_id: count}` for new templates seen in the last `window_s` seconds. It is intended for the new_pattern detector's "K+ times in a window" rule.
- `count_in_window(template_id, window_s, *, service=None) -> int`
- `get_top_templates(n, *, service=None, window_s=None) -> list[TemplateInfo]`: for alert root-cause hints.
- `tick()`: call once per tick to evict old window buckets, the same as `WindowEngine.tick()`.

### Lint

- `app/core/alerts.py` has imports in the middle of the file (`from dataclasses import ...` after the enums). Ruff E402 will fail CI's `ruff check app/`.

---

## Config owner (`app/config.py`, `.env.example`)

- Please add settings for the template miner:
  - `TEMPLATE_MAX_CLUSTERS` (default 1000)
  - `TEMPLATE_RARITY_THRESHOLD` (default 0.001)
  - `TEMPLATE_NOVELTY_TTL_S` (default 300)
  - `TEMPLATE_STATE_PATH` (e.g. `./state/templates.json`)
- `app/config.py` line 13 (`class Settings(BaseSettings):   `) has trailing whitespace, so `black --check` fails.

---

## Everyone: CI lint status after `feat/mokshad-templates`

I fixed all ruff and black issues in my own files (`app/ingest/*`, `app/core/window.py`, `app/core/templates.py`, and their tests). These remain, and each one alone keeps CI red:

| File | ruff | black | Likely owner |
|---|---|---|---|
| `app/sinks/base.py` | 14 | reformat | Varad |
| `app/sinks/dryrun.py` | 2 | reformat | Varad |
| `tests/test_sinks.py` | 6 | reformat | Varad |
| `app/core/alerts.py` | 3 (E402) | reformat | Kostubh |
| `app/api/routes.py` | — | reformat | Sara |
| `app/main.py` | 1 | reformat | ? |
| `app/config.py` | 1 | reformat | ? |

Most of these clear with `ruff check --fix <file> && black <file>`.

---

## Lifespan owner (`app/main.py`)

- On startup, construct a `TemplateMiner(clock, ...)` and `await miner.restore(settings.template_state_path)` if the file exists.
- On shutdown, `await miner.persist(...)` next to the baseline persist.
