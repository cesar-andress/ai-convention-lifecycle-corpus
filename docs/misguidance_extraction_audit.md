# Misguidance extraction audit

Audit of how parser v2 drops references **before** the misguidance detector runs.

Sources: `scripts/cochange/content_refs.py`, `scripts/misguidance/detect_stale_references.py`

Pilot v1 used default `extract_content_references()` (misguidance_mode=False).

---

## Summary

Parser v2 was tuned for **scope sensitivity** (precision over recall). Several filters remove tokens that do not resolve at HEAD. When the same output feeds the misguidance detector, **stale references are largely invisible**, producing a severe lower bound on stale rate.

Misguidance pilot v2 sets `misguidance_mode=True` to decouple extraction from HEAD validation.

---

## Discard points in `content_refs.py` (default mode)

| Location | Rule | Effect |
|----------|------|--------|
| `extract_from_text_block` → markdown links | Skip `http://`, `https://`, `mailto:`, `#` anchors only | External/anchor links discarded (expected) |
| `extract_from_text_block` → code spans | `if conf == "low" and not exists: continue` | **Major filter:** backtick tokens that do not resolve at HEAD are dropped |
| `extract_from_text_block` → explicit paths | `if conf == "low": continue` | Non-resolving explicit paths dropped (includes absent paths) |
| `extract_from_text_block` → common directories | `if conf == "low": continue` | Directory names absent at HEAD dropped |
| `extract_from_text_block` → config scan | `if exists:` only | Config filenames mentioned but absent at HEAD never emitted |
| `extract_from_text_block` → make commands | Requires Makefile/makefile in HEAD | Commands retained only when Makefile exists |
| `_is_plausible_path_token` | Metaphors, URLs, ALL_CAPS noise | Obvious garbage discarded (retained in misguidance mode when path-like) |
| `_backtick_confidence` | NOISE_BACKTICK set | Many tokens forced to `low` → then dropped if absent |
| `resolve_reference` | Returns `(raw, False)` not `(None, …)` for failed match | Resolution proceeds but `exists_in_head=False`; downstream filters drop |
| `to_row` → `used_for_scope` | Requires exists + medium/high | Scope pipeline ignores absent refs (co-change only) |

---

## Confidence filters (default)

| Pattern | Confidence when absent | Kept? |
|---------|------------------------|-------|
| Markdown link | `low` | Yes (only absent pattern kept today) |
| Code span | `low` | **No** |
| Explicit path | `low` | **No** |
| Common directory | `low` | **No** |
| Config mention | n/a (not emitted) | **No** |
| Make → Makefile | n/a | **No** if Makefile missing |

Result: among non-markdown patterns, **absent paths are almost never extracted**.

---

## Existence filters (default)

1. **Extraction stage:** drop rows with `exists_in_head=False` for most rules (see above).
2. **Scope stage (`used_for_scope`):** false when not in HEAD.
3. **Misguidance detector:** re-checks existence via `reference_exists_at_head()` but cannot classify stale refs that were never extracted.

---

## Resolution filters (default)

| Issue | Parser behavior | Misguidance impact |
|-------|-----------------|------------------|
| Leading dot stripped (`.github/…` → `github/…`) | `resolve_reference` may match wrong prefix or fail | False valid or dropped |
| Relative paths | Joined with instruction base dir | Usually OK |
| Doc-site routes (`/v3/concepts/flows`) | Stored as resolved path without `docs/` | Often absent + low conf; only markdown path kept |
| URL fragments | Discarded at link parse | Not misguidance targets |

---

## Misguidance detector filters (`detect_stale_references.py`)

| Rule | Effect |
|------|--------|
| `resolution_uncertain` + low confidence | Classified `ambiguous`, not `stale` |
| Documentation refs | Status `doc_reference`, excluded from primary stale rate |
| Commands | `unknown_command` unless Makefile mapping exists |
| Historical check (v1) | Only on `stale` / `doc_reference` statuses |

---

## `misguidance_mode=True` changes (v2 extraction)

| Change | Behavior |
|--------|----------|
| Code spans | Retain path-like tokens even when absent; assign `medium` confidence |
| Explicit paths | Retain absent plausible paths as `medium` |
| Common directories | Retain absent directory mentions as `medium` |
| Config scan | Emit absent config filenames as `medium` |
| Make commands | Emit even when Makefile absent (`exists_in_head=False`) |
| Provenance fields | `extracted_reference`, `resolution_status`, `exists_in_head` always populated |
| Garbage filter | Still discard metaphors, HTTP verbs, prose fragments |

---

## `resolution_status` values (misguidance mode)

| Value | Meaning |
|-------|---------|
| `resolved` | Resolved path exists at HEAD |
| `resolved_intended` | Raw/intended path exists though resolver output differs |
| `partial_resolution` | Dot-prefix or similar resolver distortion |
| `not_in_head` | Confident path-like reference absent at HEAD |
| `unresolved` | No repository-relative path (URL, empty) |

---

## Expected pilot impact

| Metric | Pilot v1 (biased extraction) | Pilot v2 (misguidance extraction) |
|--------|------------------------------|-------------------------------------|
| References extracted | ~404 | Higher (absent paths retained) |
| Valid | ~401 | Lower share |
| Stale | ~0 | Should increase if drift present |
| Ambiguous | ~3 | May increase for low-confidence retained tokens |

---

## Files

| Path | Role |
|------|------|
| `scripts/cochange/content_refs.py` | `misguidance_mode` flag (default False; co-change unchanged) |
| `scripts/misguidance/detect_stale_references.py` | Uses misguidance extraction; history on stale + unresolved |
| `scripts/misguidance/run_misguidance_pilot.py` | `--extraction-mode v1|v2` |
| `results/misguidance/pilot/` | v1 outputs |
| `results/misguidance/pilot_v2/` | v2 outputs |

Run v2: `make pilot-misguidance-v2`
