#!/usr/bin/env python3
"""Adoption-maintenance v2 analysis for MSR submission readiness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lifecycle.adoption_maintenance import (
    BOOTSTRAP_N,
    THRESHOLDS,
    add_states_and_flags,
    assign_state,
    build_funnel,
    enrich_present_in_head,
    gap_artifact_mature,
    gap_repo_level,
    load_am_config,
    table_by_cohort,
)
from lifecycle.analyze import load_artifact_frame
from lifecycle.detection import load_config
from lifecycle.fill_annotation import annotation_summary, fill_sheet

DEFAULT_V2 = ROOT / "protocol" / "adoption_maintenance_v2.yaml"
DEFAULT_AM = ROOT / "protocol" / "adoption_maintenance_v1.yaml"
DEFAULT_LC = ROOT / "protocol" / "lifecycle_v1.yaml"
DEFAULT_DISCOVERED_V2 = ROOT / "data" / "lifecycle" / "discovered_v2.csv"
EXTRACT_META = ROOT / "data" / "lifecycle" / "extract_meta.json"


def validate_extract_scale(
    discovered_path: Path,
    touch_path: Path,
    artifacts_path: Path,
    meta_path: Path = EXTRACT_META,
) -> dict:
    """Fail fast when downstream reads stale or incomplete extract outputs."""
    if not discovered_path.exists():
        raise SystemExit(f"missing discovered file: {discovered_path}")
    if not touch_path.exists() or not artifacts_path.exists():
        raise SystemExit(
            f"missing touch history or artifacts under {touch_path.parent}. "
            "Run extract_history.py and build_dataset.py first."
        )

    disc_n = len(pd.read_csv(discovered_path))
    touch_repos = int(pd.read_parquet(touch_path)["repo_id"].nunique())
    art_repos = int(pd.read_parquet(artifacts_path)["repo_id"].nunique())

    if touch_path.stat().st_mtime < discovered_path.stat().st_mtime:
        raise SystemExit(
            f"stale extract: {discovered_path.name} is newer than {touch_path.name} "
            f"({disc_n} discovered vs {touch_repos} repos in touch history). "
            "Re-run lifecycle/extract_history.py --discovered "
            f"{discovered_path} (or make lifecycle-v2)."
        )

    if art_repos != touch_repos:
        raise SystemExit(
            f"stale parquet mismatch: touch={touch_repos} artifacts={art_repos}. "
            "Re-run build_dataset.py after extract_history.py."
        )

    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        n_discovered = int(meta.get("n_discovered", 0))
        n_touch_repos = int(meta.get("n_repos_in_touch_history", 0))
        if n_discovered != disc_n:
            raise SystemExit(
                f"discovered.csv has {disc_n} repos but extract_meta reports n_discovered={n_discovered}. "
                f"Re-run extract_history.py --discovered {discovered_path}"
            )
        if touch_repos != n_touch_repos:
            raise SystemExit(
                f"extract_meta reports {n_touch_repos} repos but touch_history has {touch_repos}. "
                "Re-run extract_history.py and build_dataset.py."
            )
        if meta.get("complete") is False:
            raise SystemExit(
                f"incomplete extract: {meta.get('n_extract_ok', '?')} repos ok of {n_discovered} discovered. "
                "Re-run lifecycle/extract_history.py to finish."
            )
        return meta

    # Legacy extract (pre-meta): allow if touch history is at least as new as discovery.
    return {
        "discovered_path": str(discovered_path),
        "n_discovered": disc_n,
        "n_repos_in_touch_history": touch_repos,
        "inferred_without_meta": True,
    }


def load_v2(path: Path) -> dict:
    import yaml

    with path.open() as f:
        return yaml.safe_load(f)


def cluster_bootstrap_repo_gap(df: pd.DataFrame, t: int, n: int, seed: int) -> dict:
    repos = df["repo_id"].unique()
    groups = {r: df[df["repo_id"] == r] for r in repos}
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(n):
        picked = rng.choice(repos, size=len(repos), replace=True)
        boot = pd.concat([groups[r] for r in picked], ignore_index=True)
        g = gap_repo_level(boot, t)
        if g["gap_rate"] is not None:
            samples.append(g["gap_rate"])
    obs = gap_repo_level(df, t)["gap_rate"]
    if not samples:
        return {"observed": obs, "ci_95": {"low": None, "high": None}, "n_bootstrap": 0}
    arr = np.array(samples)
    return {
        "observed": obs,
        "ci_95": {"low": float(np.percentile(arr, 2.5)), "high": float(np.percentile(arr, 97.5))},
        "n_bootstrap": len(samples),
    }


def cluster_bootstrap_artifact_gap(df: pd.DataFrame, t: int, n: int, seed: int) -> dict:
    from lifecycle.adoption_maintenance import cluster_bootstrap_gap

    return cluster_bootstrap_gap(df, t, n=n, seed=seed)


def full_bootstrap(df: pd.DataFrame, thresholds: list[int], n: int, seed: int) -> dict:
    out = {}
    for t in thresholds:
        art = cluster_bootstrap_artifact_gap(df, t, n, seed)
        repo = cluster_bootstrap_repo_gap(df, t, n, seed)
        out[str(t)] = {
            "artifact_gap_mature": {
                "observed": art["observed_gap_rate_mature"],
                "maintenance_rate_observed": art["observed_maintenance_rate_mature"],
                "gap_ci_95": art["gap_rate_ci_95"],
                "maintenance_ci_95": art["maintenance_rate_ci_95"],
                "n_bootstrap": art["n_bootstrap"],
            },
            "repo_gap": repo,
        }
    return out


def leave_one_repo_out_v2(df: pd.DataFrame, t: int) -> pd.DataFrame:
    full_art = gap_artifact_mature(df, t)
    full_repo = gap_repo_level(df, t)
    rows = []
    for repo_id in sorted(df["repo_id"].unique()):
        sub = df[df["repo_id"] != repo_id]
        art = gap_artifact_mature(sub, t)
        repo = gap_repo_level(sub, t)
        rows.append(
            {
                "repo_id": repo_id,
                "n_artifacts_removed": int((df["repo_id"] == repo_id).sum()),
                "artifact_gap_mature": art["gap_rate"],
                "delta_artifact_gap_vs_full": (art["gap_rate"] - full_art["gap_rate"])
                if art["gap_rate"] is not None and full_art["gap_rate"] is not None
                else None,
                "repo_gap": repo["gap_rate"],
                "delta_repo_gap_vs_full": (repo["gap_rate"] - full_repo["gap_rate"])
                if repo["gap_rate"] is not None and full_repo["gap_rate"] is not None
                else None,
            }
        )
    loo = pd.DataFrame(rows)
    loo["abs_delta_artifact_gap"] = loo["delta_artifact_gap_vs_full"].abs()
    loo["abs_delta_repo_gap"] = loo["delta_repo_gap_vs_full"].abs()
    return loo.sort_values("abs_delta_artifact_gap", ascending=False)


def top_prompt_repos(df: pd.DataFrame, k: int) -> list[str]:
    prompts = df[df["artifact_type"] == "prompts"]
    if prompts.empty:
        return []
    return prompts.groupby("repo_id").size().sort_values(ascending=False).head(k).index.tolist()


def deleted_dormant_rates(df: pd.DataFrame, t: int) -> dict:
    ever = len(df)
    deleted = int(df["deleted"].sum())
    mature = df[df[f"mature_present_{t}"]]
    dormant = int((mature[f"state_{t}"] == "DORMANT").sum())
    return {
        "deleted_rate_ever_introduced": deleted / ever if ever else None,
        "dormant_present_rate_mature_present": dormant / len(mature) if len(mature) else None,
        "n_ever_introduced": ever,
        "n_deleted": deleted,
        "n_mature_present": len(mature),
        "n_dormant_mature_present": dormant,
    }


def cohort_gap_table(df: pd.DataFrame, t: int) -> pd.DataFrame:
    return table_by_cohort(df, t)


def type_gap_age_adjusted(
    df: pd.DataFrame,
    t: int,
    types: tuple[str, str] = ("prompts", "agents_md"),
    min_per_cell: int = 10,
) -> pd.DataFrame:
    rows: list[dict] = []
    a, b = types

    # By introduction quarter
    for cohort, grp in df.groupby("introduced_at_quarter", sort=True):
        row = {"stratum_type": "introduced_at_quarter", "stratum": cohort}
        ok = True
        for typ in (a, b):
            sub = grp[(grp["artifact_type"] == typ) & grp[f"mature_present_{t}"]]
            g = gap_artifact_mature(sub, t) if len(sub) else {"n_mature_present": 0, "gap_rate": None}
            row[f"n_mature_{typ}"] = g["n_mature_present"]
            row[f"gap_{typ}"] = g["gap_rate"]
            if g["n_mature_present"] < min_per_cell:
                ok = False
        row["comparable"] = ok
        row["gap_difference_prompts_minus_agents"] = (
            (row[f"gap_{a}"] - row[f"gap_{b}"]) if ok and row[f"gap_{a}"] is not None and row[f"gap_{b}"] is not None else None
        )
        rows.append(row)

    # By follow-up bin (among mature present)
    mature = df[df[f"mature_present_{t}"]].copy()
    bins = [180, 365, 545, 730, 10_000]
    labels = ["180-364", "365-544", "545-729", "730+"]
    mature["follow_up_bin"] = pd.cut(mature["follow_up_days"], bins=bins, labels=labels, right=False)
    for bname, grp in mature.groupby("follow_up_bin", observed=True):
        row = {"stratum_type": "follow_up_bin", "stratum": str(bname)}
        ok = True
        for typ in (a, b):
            sub = grp[grp["artifact_type"] == typ]
            g = gap_artifact_mature(sub, t) if len(sub) else {"n_mature_present": 0, "gap_rate": None}
            row[f"n_mature_{typ}"] = g["n_mature_present"]
            row[f"gap_{typ}"] = g["gap_rate"]
            if g["n_mature_present"] < min_per_cell:
                ok = False
        row["comparable"] = ok
        row["gap_difference_prompts_minus_agents"] = (
            (row[f"gap_{a}"] - row[f"gap_{b}"]) if ok and row[f"gap_{a}"] is not None and row[f"gap_{b}"] is not None else None
        )
        rows.append(row)

    return pd.DataFrame(rows)


def build_annotation_sheet(
    df: pd.DataFrame,
    t: int,
    n_dormant: int,
    n_active: int,
    seed: int,
    out: Path,
) -> pd.DataFrame:
    existing: dict[tuple[str, str], dict] = {}
    if out.exists():
        prev = pd.read_csv(out)
        for _, r in prev.iterrows():
            key = (str(r["repo_id"]), str(r["artifact_path"]))
            existing[key] = r.to_dict()

    rng = np.random.default_rng(seed)
    mature = df[df[f"mature_present_{t}"]].copy()
    rows = []
    for state, n_each in (("DORMANT", n_dormant), ("ACTIVE", n_active)):
        pool = mature[mature[f"state_{t}"] == state]
        if len(pool) < n_each:
            sample = pool
        else:
            sample = pool.sample(n=n_each, random_state=int(rng.integers(0, 2**31 - 1)))
        for _, r in sample.iterrows():
            key = (str(r["repo_id"]), str(r["artifact_path"]))
            base = {
                "repo_id": r["repo_id"],
                "artifact_type": r["artifact_type"],
                "artifact_path": r["artifact_path"],
                "state_180": r[f"state_{t}"],
                "introduced_at": r["introduced_at"],
                "last_touch_at": r["last_touch_at"],
                "days_since_last_touch": int(r["days_since_last_touch"]),
                "touch_count": int(r["touch_count"]),
                "present_in_head": bool(r["present_in_head"]),
                "git_state_correct": "",
                "substantial_last_touch": "",
                "apparent_semantic_relevance": "",
                "ambiguous": "",
                "annotator_notes": "",
            }
            if key in existing:
                for col in (
                    "git_state_correct",
                    "substantial_last_touch",
                    "apparent_semantic_relevance",
                    "ambiguous",
                    "annotator_notes",
                ):
                    val = existing[key].get(col, "")
                    if pd.notna(val) and str(val).strip():
                        base[col] = val
            rows.append(base)
    sheet = pd.DataFrame(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.to_csv(out, index=False)
    return sheet


def headline_metrics(df: pd.DataFrame, t: int) -> dict:
    art = gap_artifact_mature(df, t)
    repo = gap_repo_level(df, t)
    dd = deleted_dormant_rates(df, t)
    return {
        "threshold_days": t,
        "artifact_gap_mature": art["gap_rate"],
        "artifact_maintenance_rate_mature": art["maintenance_rate"],
        "repo_gap": repo["gap_rate"],
        "n_repos": int(df["repo_id"].nunique()),
        "n_ever_introduced": len(df),
        "n_present": int(df["present_in_head"].sum()),
        "n_mature_present": art["n_mature_present"],
        "n_dormant": art["n_dormant"],
        "n_active": art["n_active"],
        **dd,
    }


def assess_submission_readiness(v2_cfg: dict, summary: dict) -> dict:
    min_repos = int(v2_cfg["submission_readiness"]["min_repos"])
    n_repos = summary["n_repos"]
    checks = {
        "n_repos_at_least_200": n_repos >= min_repos,
        "bootstrap_present": bool(summary.get("bootstrap")),
        "loo_present": summary.get("loo_max_abs_delta_artifact_gap") is not None,
        "annotation_sheet_40_rows": summary.get("annotation_rows", 0) >= 40,
        "age_adjusted_comparable_strata": summary.get("n_comparable_age_strata", 0) >= 1,
        "discovery_funnel_recorded": summary.get("discovery_funnel") is not None,
    }
    passed = sum(checks.values())
    if all(checks.values()):
        label = "WEAK_ACCEPT_READY"
        note = "Meets minimum MSR v2 checklist; manual labels still required before submission."
    elif passed >= 4 and n_repos >= 150:
        label = "BORDERLINE"
        note = "Close; address failed checks before submission."
    else:
        label = "NOT_READY"
        note = "Scale or analyses incomplete."
    return {"label": label, "note": note, "checks": checks, "checks_passed": f"{passed}/{len(checks)}"}


def run_v2_analysis(
    df: pd.DataFrame,
    v2_cfg: dict,
    *,
    discovery_funnel: dict | None = None,
) -> tuple[dict, pd.DataFrame]:
    primary = int(v2_cfg["analysis"]["primary_threshold_days"])
    n_boot = int(v2_cfg["analysis"]["bootstrap_replicates"])
    seed = int(v2_cfg["analysis"]["manual_validation"]["seed"])
    top_k = int(v2_cfg["analysis"]["exclude_top_prompt_repos"])
    min_cell = int(v2_cfg["scale"].get("min_cohort_type_per_quarter", 10))

    df = add_states_and_flags(df, THRESHOLDS)

    bootstrap = full_bootstrap(df, THRESHOLDS, n_boot, seed)
    loo = leave_one_repo_out_v2(df, primary)
    cohort = cohort_gap_table(df, primary)
    age_adj = type_gap_age_adjusted(df, primary, min_per_cell=min_cell)

    excluded = top_prompt_repos(df, top_k)
    df_excl = df[~df["repo_id"].isin(excluded)] if excluded else df

    ann_path = ROOT / v2_cfg["outputs"]["annotation_sheet"]
    sheet = build_annotation_sheet(
        df,
        primary,
        int(v2_cfg["analysis"]["manual_validation"]["n_dormant"]),
        int(v2_cfg["analysis"]["manual_validation"]["n_active"]),
        seed,
        ann_path,
    )
    sheet = fill_sheet(sheet, overwrite=False)
    sheet.to_csv(ann_path, index=False)

    headline = headline_metrics(df, primary)
    headline_excl = headline_metrics(df_excl, primary) if len(excluded) else headline

    n_comparable = int(age_adj["comparable"].sum()) if not age_adj.empty and "comparable" in age_adj.columns else 0

    summary = {
        "paper_title": "Adoption Is Not Maintenance",
        "sample_descriptor": "GitHub OSS candidate repos from mixed AI-adopter and general seed pools with at least one detected AI convention path",
        "discovery_funnel": discovery_funnel,
        "headline_primary_180": headline,
        "sensitivity_exclude_top_prompt_repos": {
            "excluded_repos": excluded,
            "headline_180": headline_excl,
        },
        "by_threshold": {str(t): {"artifact": gap_artifact_mature(df, t), "repo": gap_repo_level(df, t)} for t in THRESHOLDS},
        "deleted_dormant_primary": deleted_dormant_rates(df, primary),
        "bootstrap": bootstrap,
        "loo_influential_top5_artifact_gap": loo.head(5).to_dict(orient="records"),
        "loo_max_abs_delta_artifact_gap": float(loo["abs_delta_artifact_gap"].max()) if len(loo) else None,
        "loo_max_abs_delta_repo_gap": float(loo["abs_delta_repo_gap"].max()) if len(loo) else None,
        "n_comparable_age_strata": n_comparable,
        "annotation_rows": len(sheet),
        "annotation_path": str(ann_path),
        "annotation_summary": annotation_summary(sheet),
        "claims_allowed": [
            "Adoption (HEAD presence) exceeds git-based maintenance among mature-present artifacts.",
            "Repo-level maintenance metrics can mask artifact-level dormancy.",
            "Gap magnitude varies by artifact type and introduction cohort where sample size permits.",
            "Deletion and git-dormant persistence are distinct outcomes.",
        ],
        "claims_forbidden": [
            "General OSS prevalence of AI governance.",
            "Semantic obsolescence or governance failure.",
            "Causal workflow effects.",
        ],
    }
    summary["n_repos"] = headline["n_repos"]
    summary["submission_readiness"] = assess_submission_readiness(v2_cfg, summary)

    return summary, df


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v2-config", type=Path, default=DEFAULT_V2)
    parser.add_argument("--lifecycle-config", type=Path, default=DEFAULT_LC)
    parser.add_argument("--discovered", type=Path, default=None)
    parser.add_argument("--repos-dir", type=Path, default=ROOT / "data" / "repos")
    parser.add_argument("--discovery-funnel-json", type=Path, default=None)
    args = parser.parse_args()

    v2_cfg = load_v2(args.v2_config)
    lc_cfg = load_config(str(args.lifecycle_config))

    artifacts_path = ROOT / lc_cfg["outputs"]["artifacts"]
    touch_path = ROOT / lc_cfg["outputs"]["touch_history"]
    discovered_path = args.discovered or DEFAULT_DISCOVERED_V2

    extract_meta = validate_extract_scale(discovered_path, touch_path, artifacts_path)

    df = load_artifact_frame(artifacts_path, touch_path)
    df = enrich_present_in_head(df, args.repos_dir)

    funnel_disc = None
    funnel_path = ROOT / v2_cfg["discovery"]["outputs"]["funnel"]
    if args.discovery_funnel_json and args.discovery_funnel_json.exists():
        funnel_disc = json.loads(args.discovery_funnel_json.read_text())
    elif funnel_path.exists():
        fdf = pd.read_csv(funnel_path)
        funnel_disc = {f"{r.stage}:{r.seed_pool}": int(r.count) for r in fdf.itertuples()}

    if args.discovered and args.discovered.exists():
        disc = pd.read_csv(args.discovered)
    elif discovered_path.exists():
        disc = pd.read_csv(discovered_path)
    else:
        disc = None
    if disc is not None:
        pool_map = disc.set_index("repo_id")["seed_pool"].to_dict() if "seed_pool" in disc.columns else {}
        df["seed_pool"] = df["repo_id"].map(pool_map).fillna("unknown")

    summary, df_out = run_v2_analysis(df, v2_cfg, discovery_funnel=funnel_disc)
    summary["extract_meta"] = extract_meta

    outs = v2_cfg["outputs"]
    out_dir = ROOT / "results" / "lifecycle"
    out_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / outs["summary"]).write_text(json.dumps(summary, indent=2, default=str) + "\n")

    build_funnel(df_out, THRESHOLDS).to_csv(ROOT / outs["funnel"], index=False)
    leave_one_repo_out_v2(df_out, int(v2_cfg["analysis"]["primary_threshold_days"])).to_csv(ROOT / outs["loo"], index=False)
    (ROOT / outs["bootstrap"]).write_text(json.dumps(summary["bootstrap"], indent=2) + "\n")
    cohort_gap_table(df_out, int(v2_cfg["analysis"]["primary_threshold_days"])).to_csv(ROOT / outs["cohort_gap"], index=False)
    type_gap_age_adjusted(
        df_out,
        int(v2_cfg["analysis"]["primary_threshold_days"]),
        min_per_cell=int(v2_cfg["scale"]["min_cohort_type_per_quarter"]),
    ).to_csv(ROOT / outs["type_gap_age_adjusted"], index=False)

    df_out.to_parquet(ROOT / "data" / "lifecycle" / "artifact_states_v2.parquet", index=False)

    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
