# POSIX make; on Windows use Git Bash or `make` from GnuWin32 if installed.

.PHONY: help setup install-smoke

help:
	@echo "setup          - pip install -e . from repo root"
	@echo "install-smoke  - verify src.run_provenance import"

setup:
	python -m pip install -U pip
	python -m pip install -e .

install-smoke:
	python -c "from src.run_provenance import write_run_provenance; print('ok')"
