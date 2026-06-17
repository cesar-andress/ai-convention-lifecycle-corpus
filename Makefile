# AI convention lifecycle corpus — reproduction (v2 headline study)
ROOT := $(CURDIR)
export PYTHONPATH := $(ROOT)/scripts

ifeq ($(wildcard .venv/bin/python3),)
  PYTHON ?= python3
else
  PYTHON ?= .venv/bin/python3
endif

.PHONY: install analyze lifecycle-v2 verify-headline repository-typology-analysis prototype-cochange-dagster pilot-cochange-scope pilot-cochange-scope-v2 pilot-cochange-scope-v3 prepare-reference-validation prepare-reference-validation-sample2 summarize-reference-validation summarize-reference-validation-sample2 pilot-misguidance pilot-misguidance-v2 drift-candidate-audit validated-drift-package synchronization-spectrum-pilot prepare-sync-validation summarize-sync-validation prepare-sync-validation-blinded summarize-sync-agreement summarize-sync-metric-vs-human prepare-boundary20-validation summarize-boundary20-agreement summarize-boundary20-metric-vs-human clean

install:
	$(PYTHON) -m pip install -r requirements.txt

# Recompute analysis from frozen parquets (no network; no git clone)
analyze:
	$(PYTHON) scripts/lifecycle/adoption_maintenance_v2.py
	$(PYTHON) scripts/lifecycle/maturity_gap_v2.py
	$(PYTHON) scripts/lifecycle/bot_sensitivity_v2.py

repository-typology-analysis:
	$(PYTHON) scripts/lifecycle/repository_typology.py
	$(PYTHON) scripts/lifecycle/gaps_by_repository_typology.py

# Full v2 pipeline: discover → extract → build → analyze (requires git + network)
lifecycle-v2:
	$(PYTHON) scripts/lifecycle/run_v2.py

verify-headline:
	@$(PYTHON) -c "import json; s=json.load(open('results/lifecycle/adoption_maintenance_v2.json')); h=s['headline_primary_180']; assert h['n_repos']==209; print('OK: n_repos=209 artifact_gap=', round(h['artifact_gap_mature'],3))"

# Co-change feasibility prototype (isolated; does not modify lifecycle v2 outputs)
prototype-cochange-dagster:
	$(PYTHON) scripts/cochange/prototype_changed_files.py --csv
	$(PYTHON) scripts/cochange/prototype_sync_metric.py

pilot-cochange-scope:
	$(PYTHON) scripts/cochange/select_pilot_repos.py
	$(PYTHON) scripts/cochange/run_scope_sensitivity_pilot.py

pilot-cochange-scope-v2:
	$(PYTHON) scripts/cochange/run_scope_sensitivity_v2.py
	$(PYTHON) scripts/cochange/export_reference_samples.py

pilot-cochange-scope-v3:
	$(PYTHON) scripts/cochange/run_scope_sensitivity_v3.py

prepare-reference-validation:
	$(PYTHON) scripts/cochange/prepare_reference_validation.py

prepare-reference-validation-sample2:
	$(PYTHON) scripts/cochange/prepare_reference_validation.py \
		--input annotation/cochange_reference_validation_sample2.csv \
		--output annotation/cochange_reference_validation_sample2.md

summarize-reference-validation:
	$(PYTHON) scripts/cochange/summarize_reference_validation.py

summarize-reference-validation-sample2:
	$(PYTHON) scripts/cochange/summarize_reference_validation.py \
		--input annotation/cochange_reference_validation_sample2.csv \
		--json-out results/cochange/reference_validation_summary_sample2.json \
		--md-out results/cochange/reference_validation_summary_sample2.md

pilot-misguidance:
	$(PYTHON) scripts/misguidance/run_misguidance_pilot.py --extraction-mode v1 --out-dir results/misguidance/pilot

pilot-misguidance-v2:
	$(PYTHON) scripts/misguidance/run_misguidance_pilot.py --extraction-mode v2 --out-dir results/misguidance/pilot_v2

drift-candidate-audit:
	$(PYTHON) scripts/misguidance/build_drift_candidate_audit.py

validated-drift-package:
	$(PYTHON) scripts/misguidance/build_validated_drift_package.py

synchronization-spectrum-pilot:
	$(PYTHON) scripts/spectrum/select_pilot_repos.py
	$(PYTHON) scripts/spectrum/run_pilot.py

prepare-sync-validation:
	$(PYTHON) scripts/synchronization/prepare_sync_validation.py

summarize-sync-validation:
	$(PYTHON) scripts/synchronization/summarize_sync_validation.py

prepare-sync-validation-blinded:
	$(PYTHON) scripts/synchronization/prepare_sync_validation_blinded.py

summarize-sync-agreement:
	$(PYTHON) scripts/synchronization/summarize_sync_construct_agreement.py

summarize-sync-metric-vs-human:
	$(PYTHON) scripts/synchronization/summarize_sync_metric_vs_human.py

prepare-boundary20-validation:
	$(PYTHON) scripts/synchronization/prepare_boundary20_validation.py

summarize-boundary20-agreement:
	$(PYTHON) scripts/synchronization/summarize_boundary20_agreement.py

summarize-boundary20-metric-vs-human:
	$(PYTHON) scripts/synchronization/summarize_boundary20_metric_vs_human.py

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
