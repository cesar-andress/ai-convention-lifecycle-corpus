#!/usr/bin/env python3
"""Survival analysis and pilot decision for instruction-lifecycle."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.duration.hazard_regression import PHReg
from statsmodels.duration.survfunc import SurvfuncRight

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lifecycle.build_dataset import STASIS_THRESHOLDS, build_artifacts, eligibility_summary
from lifecycle.detection import load_config

DEFAULT_CONFIG = ROOT / "protocol" / "lifecycle_v1.yaml"
MIN_ELIGIBLE_180 = 30


def load_artifact_frame(artifacts_path: Path, touch_path: Path) -> pd.DataFrame:
    full_path = artifacts_path.with_name("artifacts_full.parquet")
    if full_path.exists():
        df = pd.read_parquet(full_path)
    elif artifacts_path.exists() and touch_path.exists():
        artifacts = pd.read_parquet(artifacts_path)
        touch_df = pd.read_parquet(touch_path)
        for col in ("committed_at", "observation_end"):
            if col in touch_df.columns:
                touch_df[col] = pd.to_datetime(touch_df[col], utc=True)
        df = build_artifacts(touch_df, STASIS_THRESHOLDS)
    else:
        raise FileNotFoundError(f"missing artifacts: {artifacts_path}")

    for col in ("introduced_at", "last_touch_at", "observation_end", "first_touch_after_intro"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)
    return df


def kaplan_meier_by_type(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    strata_col: str,
    eligible_col: str,
) -> dict:
    curves: dict = {}
    eligible = df[df[eligible_col]].copy()
    for name, grp in eligible.groupby(strata_col):
        if len(grp) < 2:
            curves[name] = {"error": "insufficient_n", "n": len(grp)}
            continue
        sf = SurvfuncRight(grp[duration_col].astype(float), grp[event_col].astype(int))
        curves[name] = {
            "n": int(len(grp)),
            "n_events": int(grp[event_col].sum()),
            "survival_times": [float(x) for x in sf.surv_times[:50]],
            "survival_probs": [float(x) for x in sf.surv_prob[:50]],
            "median_survival_time": _median_from_step(sf.surv_times, sf.surv_prob),
        }
    return curves


def _median_from_step(times, probs) -> float | None:
    if len(times) == 0:
        return None
    for t, p in zip(times, probs):
        if p <= 0.5:
            return float(t)
    return float(times[-1])


def pooled_median_survival(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    eligible_col: str,
) -> float | None:
    eligible = df[df[eligible_col]]
    if eligible.empty:
        return None
    sf = SurvfuncRight(eligible[duration_col].astype(float), eligible[event_col].astype(int))
    return _median_from_step(sf.surv_times, sf.surv_prob)


def fit_cox(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    eligible_col: str,
    covariates: list[str],
) -> dict:
    use = df[df[eligible_col]].dropna(subset=[duration_col, event_col]).copy()
    if use.empty:
        return {"error": "no_rows", "n": 0}

    for col in covariates:
        if col not in use.columns:
            continue
        if use[col].isna().all():
            use[col] = 0.0
        else:
            use[col] = use[col].fillna(use[col].median())

    use = use.dropna(subset=covariates)
    if len(use) < 10 or use[event_col].sum() < 3:
        return {"error": "insufficient_events", "n": len(use), "n_events": int(use[event_col].sum())}

    exog = use[covariates].astype(float)
    exog = (exog - exog.mean()) / exog.std(ddof=0).replace(0, 1.0)

    time = use[duration_col].astype(float).values
    status = use[event_col].astype(int).values
    try:
        model = PHReg(time, exog, status=status)
        result = model.fit()
    except (ValueError, np.linalg.LinAlgError) as exc:
        return {
            "error": "fit_failed",
            "n": len(use),
            "n_events": int(status.sum()),
            "message": str(exc),
        }

    hr = {}
    for i, col in enumerate(covariates):
        beta = float(result.params[i])
        hr[col] = {
            "hazard_ratio": float(math.exp(beta)),
            "coef": beta,
            "p_value": float(result.pvalues[i]) if result.pvalues is not None else None,
        }

    return {
        "n": int(len(use)),
        "n_events": int(use[event_col].sum()),
        "covariates": covariates,
        "hazard_ratios": hr,
        "concordance": float(result.concordance_index_) if hasattr(result, "concordance_index_") else None,
    }


def decide(eligibility: dict, cfg: dict, primary: int = 180) -> dict:
    crit = cfg["decision_criteria"]
    hi = float(crit["proceed_scale_n500"]["min_fraction_stasis_180_within_window"])
    lo = float(crit["hypothesis_unsupported"]["max_fraction_stasis_180_within_window"])
    stats = eligibility[str(primary)]
    n_elig = stats["n_eligible_T"]
    rate_elig = stats["stasis_T_rate_eligible"]

    if n_elig < MIN_ELIGIBLE_180:
        return {
            "label": "INSUFFICIENT_FOLLOWUP",
            "stasis_180_rate_eligible": rate_elig,
            "stasis_180_rate_all": stats["stasis_T_rate_all"],
            "n_eligible_180": n_elig,
            "min_eligible_required": MIN_ELIGIBLE_180,
            "thresholds": {"proceed": hi, "reject": lo},
            "rationale": f"n_eligible_180={n_elig} < {MIN_ELIGIBLE_180}; follow-up too short for primary decision",
        }

    if rate_elig >= hi:
        label = "PROCEED_N500"
        rationale = crit["proceed_scale_n500"]["description"]
    elif rate_elig < lo:
        label = "HYPOTHESIS_UNSUPPORTED"
        rationale = crit["hypothesis_unsupported"]["description"]
    else:
        label = "INCONCLUSIVE_PILOT"
        rationale = crit["otherwise"]

    return {
        "label": label,
        "stasis_180_rate_eligible": rate_elig,
        "stasis_180_rate_all": stats["stasis_T_rate_all"],
        "n_eligible_180": n_elig,
        "censoring_rate_180": stats["censoring_rate_T"],
        "min_eligible_required": MIN_ELIGIBLE_180,
        "thresholds": {"proceed": hi, "reject": lo},
        "rationale": rationale,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--artifacts", type=Path, default=None)
    parser.add_argument("--touch-history", type=Path, default=None)
    parser.add_argument("--covariates", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    cfg = load_config(str(args.config))
    artifacts_path = args.artifacts or ROOT / cfg["outputs"]["artifacts"]
    touch_path = args.touch_history or ROOT / cfg["outputs"]["touch_history"]
    cov_path = args.covariates or ROOT / cfg["outputs"]["repo_covariates"]
    out_path = args.out or ROOT / cfg["outputs"]["analysis"]

    if not artifacts_path.exists() and not artifacts_path.with_name("artifacts_full.parquet").exists():
        print(f"missing artifacts: {artifacts_path}", file=sys.stderr)
        return 1

    primary = int(cfg["analysis"]["primary_threshold_days"])
    thresholds = STASIS_THRESHOLDS
    duration_col = f"survival_days_{primary}"
    event_col = f"event_stasis_{primary}"
    eligible_col = f"eligible_{primary}"

    try:
        surv = load_artifact_frame(artifacts_path, touch_path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if cov_path.exists():
        cov = pd.read_parquet(cov_path)
        surv = surv.merge(cov, on="repo_id", how="left", suffixes=("", "_repo"))

    eligibility = eligibility_summary(surv, thresholds)

    # A1 Kaplan-Meier (eligible artifacts only)
    km = kaplan_meier_by_type(
        surv, duration_col, event_col, cfg["analysis"]["kaplan_meier_strata"], eligible_col
    )

    # A2 Median survival (eligible only)
    median_all = pooled_median_survival(surv, duration_col, event_col, eligible_col)
    median_by_type = {k: v.get("median_survival_time") for k, v in km.items() if "error" not in v}

    # A4 Cox model (eligible only)
    cox_covs = [c for c in cfg["analysis"]["cox_covariates"] if c in surv.columns]
    cox = (
        fit_cox(surv, duration_col, event_col, eligible_col, cox_covs)
        if cox_covs
        else {"error": "no_covariates"}
    )

    decision = decide(eligibility, cfg, primary)

    output = {
        "n_artifacts": len(surv),
        "n_repos": int(surv["repo_id"].nunique()),
        "primary_threshold_days": primary,
        "eligibility_by_threshold": eligibility,
        "A1_kaplan_meier_by_artifact_type_eligible_only": km,
        "A2_median_survival_days_eligible_only": {
            "pooled": median_all,
            "by_artifact_type": median_by_type,
        },
        "A3_stasis_rates": eligibility,
        "A4_cox_model_eligible_only": cox,
        "decision": decision,
        "artifact_type_counts": surv["artifact_type"].value_counts().to_dict(),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, default=str) + "\n")
    print(json.dumps(output, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
