#!/usr/bin/env python3
"""Extract, analyze, and gate-check GitHub Actions workflow family on fixed 209-repo cohort."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import numpy as np
import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.adoption_maintenance import (
    THRESHOLDS,
    add_states_and_flags,
    enrich_present_in_head,
    gap_artifact_mature,
    gap_repo_level,
    gap_repo_maturity_matched_unrestricted,
    gap_repo_restricted,
)
from lifecycle.adoption_maintenance_v2 import full_bootstrap, leave_one_repo_out_extended
from lifecycle.build_dataset import build_artifacts, eligibility_summary
from lifecycle.corpus_paths import configure
from lifecycle.detection import is_bot, load_config, normalize_path

ROOT = configure()
DEFAULT_CFG = ROOT / "protocol" / "gh_actions_v1.yaml"
ATTRITION_V2 = ROOT / "results/lifecycle/extract_attrition_v2.csv"
DISCOVERED_V2 = ROOT / "data/lifecycle/discovered_v2.csv"

GATE_THRESHOLDS = {
    "min_adopted_repos": 80,
    "min_restricted_repos": 40,
    "min_mature_present_paths": 150,
    "max_top_repo_share_mature_present": 0.50,
}


def load_family_cfg(path: Path) -> dict:
    return load_config(str(path))


def build_cohort_csv(cfg: dict) -> Path:
    out = ROOT / cfg["outputs"]["cohort"]
    out.parent.mkdir(parents=True, exist_ok=True)
    attr = pd.read_csv(ATTRITION_V2)
    ok_ids = set(attr[attr["status"] == "ok"]["repo_id"])
    disc = pd.read_csv(DISCOVERED_V2)
    cohort = disc[disc["repo_id"].isin(ok_ids)].copy()
    cohort.to_csv(out, index=False)
    return out


def apply_panel_filter(df: pd.DataFrame, cfg: dict, *, include_nested: bool = False) -> pd.DataFrame:
    out = df.copy()
    if not include_nested and cfg.get("primary_analysis", {}).get("root_workflows_only", False):
        prefix = cfg["primary_analysis"].get("path_prefix", ".github/workflows/")
        out = out[out["artifact_path"].map(normalize_path).str.startswith(prefix)]
    return out


def top_workflow_repos(df: pd.DataFrame, k: int) -> list[str]:
    present = df[df["present_in_head"]]
    if present.empty or k <= 0:
        return []
    return present.groupby("repo_id").size().sort_values(ascending=False).head(k).index.tolist()


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
        "n_ever_introduced": len(df),
        "n_present_head": int(df["present_in_head"].sum()),
        "n_mature_present_paths": art["n_mature_present"],
        "n_repos_with_mature_present": restricted["n_repos_with_mature_present"],
        "median_paths_per_adopted_repo": float(median(adopted)) if len(adopted) else 0.0,
        "max_paths_per_adopted_repo": int(max(adopted_counts)),
        "artifact_gap_mature": art["gap_rate"],
        "artifact_maintenance_rate_mature": art["maintenance_rate"],
        "repo_gap_unguarded": repo["gap_rate"],
        "repo_gap_restricted": restricted["gap_rate"],
        "repo_gap_maturity_matched_unrestricted": maturity_matched["gap_rate"],
        "n_repos_with_active_mature_present": maturity_matched["n_repos_with_active_mature_present"],
    }


def concentration_top_repo_share(df: pd.DataFrame, t: int) -> dict:
    mature = df[df[f"mature_present_{t}"]]
    if mature.empty:
        return {"top_repo_id": None, "top_repo_share": None, "n_mature_present": 0}
    counts = mature.groupby("repo_id").size().sort_values(ascending=False)
    top_repo = counts.index[0]
    share = float(counts.iloc[0] / counts.sum())
    return {
        "top_repo_id": top_repo,
        "top_repo_share": share,
        "n_mature_present": int(counts.sum()),
        "top_repo_n_mature_present": int(counts.iloc[0]),
    }


def bot_filtered_headline(df: pd.DataFrame, touch_df: pd.DataFrame, cfg: dict, t: int) -> dict:
    rows = []
    for (repo_id, artifact_type, artifact_path), grp in touch_df.groupby(
        ["repo_id", "artifact_type", "artifact_path"], sort=True
    ):
        grp = grp.sort_values("committed_at")
        kept = grp[~grp.apply(lambda r: is_bot(r["author"], r["email"], cfg), axis=1)]
        if kept.empty:
            continue
        last_touch = kept["committed_at"].iloc[-1]
        row = df[
            (df.repo_id == repo_id)
            & (df.artifact_type == artifact_type)
            & (df.artifact_path == artifact_path)
        ]
        if row.empty:
            continue
        row = row.iloc[0].copy()
        row["last_touch_at"] = last_touch
        rows.append(row)
    if not rows:
        return {"artifact_gap_mature": None, "repo_gap_unguarded": None}
    sub = pd.DataFrame(rows)
    sub = add_states_and_flags(sub, THRESHOLDS)
    art = gap_artifact_mature(sub, t)
    repo = gap_repo_level(sub, t)
    return {
        "artifact_gap_mature": art["gap_rate"],
        "repo_gap_unguarded": repo["gap_rate"],
        "n_paths_retained": len(sub),
    }


def evaluate_gate(summary: dict, concentration: dict) -> dict:
    h = summary["headline_primary_180"]
    boot = summary.get("bootstrap", {}).get("180", {})
    checks = {
        "adopted_repos_ge_80": h["n_repos_adopted_head"] >= GATE_THRESHOLDS["min_adopted_repos"],
        "restricted_repos_ge_40": h["n_repos_with_mature_present"] >= GATE_THRESHOLDS["min_restricted_repos"],
        "mature_present_paths_ge_150": h["n_mature_present_paths"] >= GATE_THRESHOLDS["min_mature_present_paths"],
        "concentration_below_50pct": concentration["top_repo_share"] is not None
        and concentration["top_repo_share"] <= GATE_THRESHOLDS["max_top_repo_share_mature_present"],
        "artifact_bootstrap_present": bool(boot.get("artifact_gap_mature", {}).get("n_bootstrap")),
        "restricted_bootstrap_present": bool(boot.get("repo_gap_restricted", {}).get("n_bootstrap")),
        "unguarded_bootstrap_present": bool(boot.get("repo_gap", {}).get("n_bootstrap")),
    }
    passed = all(checks.values())
    return {
        "passed": passed,
        "checks": checks,
        "thresholds": GATE_THRESHOLDS,
        "concentration": concentration,
        "recommendation": "PROCEED" if passed else "ABORT_MANUSCRIPT_INTEGRATION",
    }


def render_summary_md(summary: dict, gate: dict, cfg: dict) -> str:
    h = summary["headline_primary_180"]
    b = summary["bootstrap"]["180"]
    art = b["artifact_gap_mature"]
    rest = b["repo_gap_restricted"]
    repo = b["repo_gap"]
    lines = [
        f"# GitHub Actions family summary ({cfg['family_id']})",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Primary panel (root `.github/workflows/`, example paths excluded)",
        "",
        f"- Repos adopted (HEAD): **{h['n_repos_adopted_head']}**",
        f"- Repos with ≥1 mature-present workflow: **{h['n_repos_with_mature_present']}**",
        f"- Mature-present workflow paths: **{h['n_mature_present_paths']}**",
        f"- Median workflows per adopted repo: **{h['median_paths_per_adopted_repo']:.1f}**",
        f"- Artifact gap @ T=180: **{h['artifact_gap_mature']*100:.1f}%** "
        f"CI [{art['gap_ci_95']['low']*100:.1f}, {art['gap_ci_95']['high']*100:.1f}]",
        f"- Restricted repo gap: **{h['repo_gap_restricted']*100:.1f}%** "
        f"CI [{rest['ci_95']['low']*100:.1f}, {rest['ci_95']['high']*100:.1f}]",
        f"- Unguarded repo gap: **{h['repo_gap_unguarded']*100:.1f}%** "
        f"CI [{repo['ci_95']['low']*100:.1f}, {repo['ci_95']['high']*100:.1f}]",
        f"- Maturity-matched unrestricted repo gap: **{h['repo_gap_maturity_matched_unrestricted']*100:.1f}%**",
        f"- LOO max |Δ| artifact / unguarded / restricted: "
        f"**{summary['loo_max_abs_delta_artifact_gap']:.3f} / "
        f"{summary['loo_max_abs_delta_repo_gap_unguarded']:.3f} / "
        f"{summary['loo_max_abs_delta_repo_gap_restricted']:.3f}**",
        "",
        "## Gate decision",
        "",
        f"- **{gate['recommendation']}**",
        "",
    ]
    for k, v in gate["checks"].items():
        lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    if gate["concentration"]["top_repo_id"]:
        lines.append(
            f"- Top-repo concentration: `{gate['concentration']['top_repo_id']}` "
            f"({gate['concentration']['top_repo_share']*100:.1f}% of mature-present paths)"
        )
    return "\n".join(lines) + "\n"


def run_extract(cfg: dict) -> int:
    cohort = build_cohort_csv(cfg)
    discovered_out = ROOT / cfg["outputs"]["discovered"]
    discovered_out.parent.mkdir(parents=True, exist_ok=True)
    pd.read_csv(cohort).to_csv(discovered_out, index=False)
    cmd = [
        sys.executable,
        str(ROOT / "scripts/lifecycle/extract_history.py"),
        "--config",
        str(ROOT / "protocol/gh_actions_v1.yaml"),
        "--discovered",
        str(discovered_out),
        "--touch-out",
        str(ROOT / cfg["outputs"]["touch_history"]),
        "--covariates-out",
        str(ROOT / cfg["outputs"]["repo_covariates"]),
        "--attrition-out",
        str(ROOT / cfg["outputs"]["attrition"]),
        "--meta-out",
        str(ROOT / cfg["outputs"]["extract_meta"]),
        "--resume",
    ]
    return subprocess.call(cmd, cwd=ROOT)


def run_build(cfg: dict) -> int:
    touch_path = ROOT / cfg["outputs"]["touch_history"]
    artifacts_path = ROOT / cfg["outputs"]["artifacts"]
    full_path = ROOT / cfg["outputs"]["artifacts_full"]
    if not touch_path.exists():
        print(f"missing {touch_path}", file=sys.stderr)
        return 1
    touch_df = pd.read_parquet(touch_path)
    for col in ("committed_at", "observation_end"):
        touch_df[col] = pd.to_datetime(touch_df[col], utc=True)
    artifacts = build_artifacts(touch_df, THRESHOLDS)
    artifacts_path.parent.mkdir(parents=True, exist_ok=True)
    export_cols = [
        "repo_id",
        "artifact_type",
        "artifact_path",
        "introduced_at",
        "last_touch_at",
        "touch_count",
        "active_days",
        "stasis_90",
        "stasis_180",
        "stasis_365",
    ]
    artifacts[export_cols].to_parquet(artifacts_path, index=False)
    artifacts.to_parquet(full_path, index=False)
    meta = {
        "n_artifacts": len(artifacts),
        "n_repos": int(artifacts["repo_id"].nunique()),
        "eligibility_by_threshold": eligibility_summary(artifacts, THRESHOLDS),
    }
    (artifacts_path.parent / "artifacts_build_meta_gh_actions.json").write_text(
        json.dumps(meta, indent=2) + "\n"
    )
    print(json.dumps(meta, indent=2))
    return 0


def run_analyze(cfg: dict) -> int:
    repos_dir = ROOT / cfg["extraction"]["repos_dir"]
    touch_path = ROOT / cfg["outputs"]["touch_history"]
    full_path = ROOT / cfg["outputs"]["artifacts_full"]
    primary_t = int(cfg["analysis"]["primary_threshold_days"])
    n_boot = int(cfg["analysis"]["bootstrap_replicates"])
    seed = int(cfg["analysis"]["bootstrap_seed"])
    top_k = int(cfg["analysis"]["exclude_top_workflow_repos"])

    df = pd.read_parquet(full_path)
    for col in ("introduced_at", "last_touch_at", "observation_end"):
        df[col] = pd.to_datetime(df[col], utc=True)
    df = enrich_present_in_head(df, repos_dir)
    df = apply_panel_filter(df, cfg, include_nested=False)
    df = add_states_and_flags(df, THRESHOLDS)

    bootstrap = full_bootstrap(df, THRESHOLDS, n_boot, seed)
    loo = leave_one_repo_out_extended(df, primary_t)
    concentration = concentration_top_repo_share(df, primary_t)
    headline = headline_bundle(df, primary_t)

    excluded = top_workflow_repos(df, top_k)
    df_excl = df[~df["repo_id"].isin(excluded)] if excluded else df
    headline_excl = headline_bundle(df_excl, primary_t) if excluded else headline

    touch_df = pd.read_parquet(touch_path)
    for col in ("committed_at", "observation_end"):
        touch_df[col] = pd.to_datetime(touch_df[col], utc=True)
    touch_df = touch_df[touch_df["artifact_path"].isin(df["artifact_path"].unique())]
    bot = bot_filtered_headline(df, touch_df, cfg, primary_t)

    nested_df = pd.read_parquet(full_path)
    for col in ("introduced_at", "last_touch_at", "observation_end"):
        nested_df[col] = pd.to_datetime(nested_df[col], utc=True)
    nested_df = enrich_present_in_head(nested_df, repos_dir)
    nested_df = apply_panel_filter(nested_df, cfg, include_nested=True)
    nested_df = add_states_and_flags(nested_df, THRESHOLDS)
    nested_headline = headline_bundle(nested_df, primary_t)

    summary = {
        "study_id": cfg["family_id"],
        "family_label": cfg["family_label"],
        "panel": "primary_root_workflows_example_excluded",
        "headline_primary_180": headline,
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
        "loo_max_abs_delta_artifact_gap": float(loo["abs_delta_artifact_gap"].max()) if len(loo) else None,
        "loo_max_abs_delta_repo_gap_unguarded": float(loo["abs_delta_repo_gap_unguarded"].max())
        if len(loo)
        else None,
        "loo_max_abs_delta_repo_gap_restricted": float(loo["abs_delta_repo_gap_restricted"].max())
        if len(loo)
        else None,
        "sensitivity_exclude_top_workflow_repos": {
            "excluded_repos": excluded,
            "headline_180": headline_excl,
        },
        "sensitivity_nested_subtree_workflows": nested_headline,
        "bot_filtered_primary_180": bot,
        "concentration_primary_180": concentration,
    }

    out_dir = ROOT / "results/lifecycle_gh_actions"
    out_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / cfg["outputs"]["summary"]).write_text(json.dumps(summary, indent=2, default=str) + "\n")
    (ROOT / cfg["outputs"]["bootstrap"]).write_text(json.dumps(bootstrap, indent=2) + "\n")
    loo.to_csv(ROOT / cfg["outputs"]["loo"], index=False)
    (ROOT / cfg["outputs"]["bot_sensitivity"]).write_text(json.dumps(bot, indent=2) + "\n")
    df.to_parquet(ROOT / cfg["outputs"]["artifact_states"], index=False)

    gate = evaluate_gate(summary, concentration)
    (ROOT / cfg["outputs"]["gate_report"]).write_text(json.dumps(gate, indent=2, default=str) + "\n")
    (ROOT / cfg["outputs"]["summary_md"]).write_text(render_summary_md(summary, gate, cfg))

    print(json.dumps({"gate": gate, "headline": headline}, indent=2, default=str))
    return 0 if gate["passed"] else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub Actions artifact-family pipeline")
    parser.add_argument("--config", type=Path, default=DEFAULT_CFG)
    parser.add_argument(
        "--stage",
        choices=["all", "cohort", "extract", "build", "analyze"],
        default="all",
    )
    args = parser.parse_args()
    cfg = load_family_cfg(args.config)

    if args.stage in ("all", "cohort"):
        build_cohort_csv(cfg)
        if args.stage == "cohort":
            return 0

    if args.stage in ("all", "extract"):
        rc = run_extract(cfg)
        if rc != 0:
            return rc
        if args.stage == "extract":
            return 0

    if args.stage in ("all", "build"):
        rc = run_build(cfg)
        if rc != 0:
            return rc
        if args.stage == "build":
            return 0

    if args.stage in ("all", "analyze"):
        return run_analyze(cfg)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
