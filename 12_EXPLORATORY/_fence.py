"""EXPLORATORY fence: the only sanctioned write path for 12_EXPLORATORY scripts (see CHARTER.md rule 3)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def safe_out(path) -> Path:
    """Return `path` resolved, creating its parent, only if it lies inside 12_EXPLORATORY/."""
    p = Path(path)
    p = (p if p.is_absolute() else ROOT / p).resolve()
    if ROOT != p and ROOT not in p.parents:
        raise PermissionError(f"EXPLORATORY fence: refusing to write outside {ROOT}: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
