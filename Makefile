# POSIX make; on Windows use Git Bash or `make` from GnuWin32 if installed.

.PHONY: help setup install-smoke stage1-5-smoke

help:
	@echo "setup            - pip install -e . from repo root"
	@echo "install-smoke    - verify src.run_provenance import"
	@echo "stage1-5-smoke   - write results/analysis_runs/<run_id>/ with provenance + tables/smoke.txt"

setup:
	python -m pip install -U pip
	python -m pip install -e .

install-smoke:
	python -c "from src.run_provenance import write_run_provenance; print('ok')"

stage1-5-smoke:
	python scripts/analysis/smoke_analysis_run.py --force --run-id stage1_5_smoke_ci
