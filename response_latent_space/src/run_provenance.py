from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path.cwd(),
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown"


def _pip_freeze_snapshot() -> str:
    try:
        import importlib.util
        if importlib.util.find_spec("pip") is None:
            return "(pip not available)\n"
        out = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if out.returncode == 0:
            return out.stdout
    except (OSError, subprocess.SubprocessError):
        pass
    return "(pip freeze failed)\n"


def write_run_provenance(
    out_dir: Path | str,
    *,
    argv: list[str] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> Path:
    """
    Write a minimal provenance bundle for an analysis run (Phase 0: lightweight).

    Creates: git_commit.txt, command.txt, environment_export.txt, run_metadata.json
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    commit = _git_commit()
    (out / "git_commit.txt").write_text(commit + "\n", encoding="utf-8")

    cmd = argv if argv is not None else sys.argv
    (out / "command.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")

    env_lines = [
        f"python: {sys.version}",
        f"platform: {platform.platform()}",
        "",
        "--- pip freeze ---",
        _pip_freeze_snapshot(),
    ]
    (out / "environment_export.txt").write_text("\n".join(env_lines), encoding="utf-8")

    meta: dict[str, Any] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }
    if extra:
        meta["extra"] = dict(extra)
    (out / "run_metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    return out


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Write provenance files to a directory (smoke test).")
    ap.add_argument(
        "--out",
        type=Path,
        default=Path(".provenance_smoke"),
        help="Output directory (default: .provenance_smoke)",
    )
    args = ap.parse_args()
    write_run_provenance(args.out)
    print("ok", args.out)
