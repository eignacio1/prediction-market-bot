"""Read-only intake of Muse's sports-intel archive (W113.4, B-087).

The archive is read, never written, and always at a pinned commit.  Nothing
read here feeds a model until ``grade`` marks the table family VERIFIED by
recompute from the bot's own free data (charter §3, §5).
"""
from .archive import Archive, ArchiveError
from .fetch import ensure_clone

__all__ = ["Archive", "ArchiveError", "ensure_clone"]
