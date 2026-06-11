# AI convention lifecycle corpus — reproduction (v2 headline study)
ROOT := $(CURDIR)
export PYTHONPATH := $(ROOT)/scripts

ifeq ($(wildcard .venv/bin/python3),)
  PYTHON ?= python3
else
  PYTHON ?= .venv/bin/python3
endif

.PHONY: install analyze lifecycle-v2 verify-headline clean

install:
	$(PYTHON) -m pip install -r requirements.txt

# Recompute analysis from frozen parquets (no network; no git clone)
analyze:
	$(PYTHON) scripts/lifecycle/adoption_maintenance_v2.py
	$(PYTHON) scripts/lifecycle/maturity_gap_v2.py
	$(PYTHON) scripts/lifecycle/bot_sensitivity_v2.py

# Full v2 pipeline: discover → extract → build → analyze (requires git + network)
lifecycle-v2:
	$(PYTHON) scripts/lifecycle/run_v2.py

verify-headline:
	@$(PYTHON) -c "import json; s=json.load(open('results/lifecycle/adoption_maintenance_v2.json')); h=s['headline_primary_180']; assert h['n_repos']==209; print('OK: n_repos=209 artifact_gap=', round(h['artifact_gap_mature'],3))"

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
