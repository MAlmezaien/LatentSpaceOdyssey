from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """
    Walk upward from ``start`` (default: cwd) until we find either:
    - ``pyproject.toml`` whose project name is ``ppi-network-approaches``, or
    - a ``.git`` directory (file or dir).

    Raises FileNotFoundError if not found within a reasonable depth.
    """
    if start is None:
        cur = Path.cwd().resolve()
    else:
        p = start.resolve()
        cur = p if p.is_dir() else p.parent
    for _ in range(64):
        py = cur / "pyproject.toml"
        if py.is_file():
            try:
                text = py.read_text(encoding="utf-8")
            except OSError:
                pass
            else:
                if 'name = "ppi-network-approaches"' in text or "name = 'ppi-network-approaches'" in text:
                    return cur
        git = cur / ".git"
        if git.exists():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    raise FileNotFoundError(
        "Could not find repository root (expected pyproject.toml for ppi-network-approaches or .git) "
        f"starting from {start!r}"
    )


def as_repo_relative(path: Path, repo_root: Path) -> str:
    """Path as POSIX string relative to repo root (portable across machines)."""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
