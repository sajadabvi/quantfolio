"""macOS desktop notifications via osascript."""

from __future__ import annotations

import shlex
import subprocess
import sys


def notify_desktop(title: str, message: str, subtitle: str | None = None) -> bool:
    """
    Fire a native macOS notification. Returns True on success, False otherwise.
    Silent no-op on non-darwin platforms.
    """
    if sys.platform != "darwin":
        return False

    # osascript's "display notification" requires the literal strings inside the
    # AppleScript source; escape quotes to prevent injection.
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    parts = [f'display notification "{_esc(message)}" with title "{_esc(title)}"']
    if subtitle:
        parts.append(f'subtitle "{_esc(subtitle)}"')
    script = " ".join(parts)
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception:
        return False
