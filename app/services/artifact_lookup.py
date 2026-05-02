from pathlib import Path


def latest_artifact(candidates: list[Path]) -> Path | None:
    if not candidates:
        return None
    return max(candidates, key=lambda p: (p.stat().st_mtime, p.as_posix()))
