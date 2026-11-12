"""W111.2 (B-077, DOCTRINE.md §1b, operator D-05): user-facing labels must not use
verdict words about a pattern that lost to the market. A losing pattern is
"fade arm closed (routed)", never "ruled out" / "no edge" / "loses to the market".

Allowlist: the registry enum tokens (RULED_OUT, ruled_out, NO EFFECT NET keys) contain
underscores or are status keys, not display text, and frozen result files are not scanned.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "04_EXECUTION/visual_dashboard/body.html",
    "04_EXECUTION/visual_dashboard/script.js",
    "scripts/web_dashboard.py",
    ".claude/commands/vision.md",
    ".claude/commands/status.md",
]
BANNED = re.compile(
    r"\bno edge\b|ruled out|disproven|not mispriced|loses? to the market|\bHARMFUL\b|can.?t beat the market",
    re.IGNORECASE,
)


def test_no_banned_verdict_words_in_user_facing_labels():
    hits = []
    for rel in FILES:
        for i, line in enumerate((ROOT / rel).read_text(encoding="utf-8").splitlines(), 1):
            if BANNED.search(line) and "does the model beat the market" not in line:
                hits.append(f"{rel}:{i}: {line.strip()[:120]}")
    assert not hits, "banned verdict words (DOCTRINE §1b):\n" + "\n".join(hits)
