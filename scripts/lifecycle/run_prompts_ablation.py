#!/usr/bin/env python3
"""AI-convention ablation excluding prompts/ paths on frozen artifact_states_v2.parquet."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.adoption_maintenance import (
    THRESHOLDS,
    gap_artifact_mature,
    gap_repo_level,
    gap_repo_maturity_matched_unrestricted,
    gap_repo_restricted,
)
from lifecycle.adoption_maintenance_v2 import full_bootstrap, leave_one_repo_out_extended
from lifecycle.corpus_paths import configure

ROOT = configure()
FROZEN = ROOT / "data/lifecycle/artifact_states_v2.parquet"
OUT_DIR = ROOT / "results/lifecycle_ablation_no_prompts"
PROMPTS_PATH_RE = re.compile(r"(^|/)prompts/")
PRIMARY_T = 180
BOOT_N = 5000
BOOT_SEED = 42

CANONICAL = {
    "artifact_gap": 0.560,
    "restricted_gap": 0.214,
    "unguarded_gap": 0.072,
    "maturity_matched_gap": 0.684,
    "n_mature_present": 577,
    "n_repos": 209,
}


def is_prompt_path(row: pd.Series) -> bool:
    if str(row.get("artifact_type", "")) == "prompts":
        return True
    return bool(PROMPTS_PATH_RE.search(str(row.get("artifact_path", ""))))


def concentration_top_repo_share(df: pd.DataFrame, t: int) -> dict:
    mature = df[df[f"mature_present_{t}"]]
    if mature.empty:
        return {"top_repo_id": None, "top_repo_share": None, "n_mature_present": 0}
    counts = mature.groupby("repo_id").size().sort_values(ascending=False)
    return {
        "top_repo_id": counts.index[0],
        "top_repo_share": float(counts.iloc[0] / counts.sum()),
        "n_mature_present": int(counts.sum()),
        "top_repo_n_mature_present": int(counts.iloc[0]),
    }


def headline_bundle(df: pd.DataFrame, t: int) -> dict:
    art = gap_artifact_mature(df, t)
    repo = gap_repo_level(df, t)
    restricted = gap_repo_restricted(df, t)
    maturity_matched = gap_repo_maturity_matched_unrestricted(df, t)
    adopted = df[df["present_in_head"]].groupby("repo_id").size()
    adopted_counts = adopted.tolist() if len(adopted) else [0]
    return {
        "threshold_days": t,
        "n_repos_in_panel": int(df["repo_id"].nunique()),
        "n_repos_adopted_head": int(df.groupby("repo_id")["present_in_head"].any().sum()),
        "n_mature_present_paths": art["n_mature_present"],
        "n_repos_with_mature_present": restricted["n_repos_with_mature_present"],
        "median_paths_per_adopted_repo": float(median(adopted)) if len(adopted) else 0.0,
        "max_paths_per_adopted_repo": int(max(adopted_counts)),
        "artifact_gap_mature": art["gap_rate"],
        "artifact_maintenance_rate_mature": art["maintenance_rate"],
        "repo_gap_unguarded": repo["gap_rate"],
        "repo_gap_restricted": restricted["gap_rate"],
        "repo_gap_maturity_matched_unrestricted": maturity_matched["gap_rate"],
    }


def pct_ci(boot: dict, key: str) -> dict:
    if key == "artifact_gap_mature":
        obs = boot[key]["observed"]
        lo = boot[key]["gap_ci_95"]["low"]
        hi = boot[key]["gap_ci_95"]["high"]
    else:
        obs = boot[key]["observed"]
        lo = boot[key]["ci_95"]["low"]
        hi = boot[key]["ci_95"]["high"]
    return {
        "point_pct": round(obs * 100, 1) if obs is not None else None,
        "ci_low_pct": round(lo * 100, 1) if lo is not None else None,
        "ci_high_pct": round(hi * 100, 1) if hi is not None else None,
    }


def evaluate_ablation(full_h: dict, ablated_h: dict) -> dict:
    full_spread = (full_h["artifact_gap_mature"] or 0) - (full_h["repo_gap_restricted"] or 0)
    ablated_spread = (ablated_h["artifact_gap_mature"] or 0) - (ablated_h["repo_gap_restricted"] or 0)
    spread_retained_pct = (ablated_spread / full_spread * 100) if full_spread else 0.0
    qualitative_remains = ablated_spread >= 0.10 and ablated_h["artifact_gap_mature"] > ablated_h["repo_gap_restricted"]
    if qualitative_remains and spread_retained_pct >= 50:
        rec = "INTEGRATE_AS_ROBUSTNESS_ROW"
    elif qualitative_remains:
        rec = "INTEGRATE_WITH_CAVEAT"
    else:
        rec = "KEEP_OUT_OF_MAIN_PAPER"
    return {
        "full_artifact_minus_restricted_pp": round(full_spread * 100, 1),
        "ablated_artifact_minus_restricted_pp": round(ablated_spread * 100, 1),
        "spread_retained_pct": round(spread_retained_pct, 1),
        "qualitative_pattern_remains": qualitative_remains,
        "recommendation": rec,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df_full = pd.read_parquet(FROZEN)
    prompt_mask = df_full.apply(is_prompt_path, axis=1)
    n_prompts_removed = int(prompt_mask.sum())
    df = df_full[~prompt_mask].copy()

    headline_full = headline_bundle(df_full, PRIMARY_T)
    headline = headline_bundle(df, PRIMARY_T)
    bootstrap = full_bootstrap(df, THRESHOLDS, BOOT_N, BOOT_SEED)
    loo = leave_one_repo_out_extended(df, PRIMARY_T)
    concentration = concentration_top_repo_share(df, PRIMARY_T)
    b180 = bootstrap[str(PRIMARY_T)]
    decision = evaluate_ablation(headline_full, headline)

    summary = {
        "study_id": "ai-conventions-no-prompts-ablation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_panel": str(FROZEN.relative_to(ROOT)),
        "n_paths_removed_prompts": n_prompts_removed,
        "canonical_full_detector_unchanged": CANONICAL,
        "headline_primary_180": headline,
        "headline_full_detector_reference": headline_full,
        "by_threshold": {
            str(t): {
                "artifact": gap_artifact_mature(df, t),
                "repo_unguarded": gap_repo_level(df, t),
                "repo_restricted": gap_repo_restricted(df, t),
                "repo_maturity_matched": gap_repo_maturity_matched_unrestricted(df, t),
            }
            for t in THRESHOLDS
        },
        "bootstrap": bootstrap,
        "bootstrap_primary_180_summary": {
            "artifact_gap_mature": pct_ci(b180, "artifact_gap_mature"),
            "repo_gap_restricted": pct_ci(b180, "repo_gap_restricted"),
            "repo_gap_unguarded": pct_ci(b180, "repo_gap"),
        },
        "loo_max_abs_delta_artifact_gap": float(loo["abs_delta_artifact_gap"].max()) if len(loo) else None,
        "loo_max_abs_delta_repo_gap_unguarded": float(loo["abs_delta_repo_gap_unguarded"].max())
        if len(loo)
        else None,
        "loo_max_abs_delta_repo_gap_restricted": float(loo["abs_delta_repo_gap_restricted"].max())
        if len(loo)
        else None,
        "concentration_primary_180": concentration,
        "decision": decision,
    }

    (OUT_DIR / "adoption_maintenance_no_prompts.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    (OUT_DIR / "bootstrap_no_prompts.json").write_text(json.dumps(bootstrap, indent=2) + "\n")
    loo.to_csv(OUT_DIR / "loo_no_prompts.csv", index=False)
    df.to_parquet(OUT_DIR / "artifact_states_no_prompts.parquet", index=False)

    print(json.dumps({"headline": headline, "decision": decision}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
