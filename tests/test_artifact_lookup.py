from app.services.artifact_lookup import latest_artifact


def test_latest_artifact_breaks_mtime_ties_by_path(tmp_path):
    a = tmp_path / "2026" / "01" / "01" / "doc.txt"
    b = tmp_path / "2026" / "01" / "02" / "doc.txt"
    a.parent.mkdir(parents=True)
    b.parent.mkdir(parents=True)
    a.write_text("a", encoding="utf-8")
    b.write_text("b", encoding="utf-8")

    # Same mtime to force tie-breaker.
    a_stat = a.stat().st_mtime
    b_stat = b.stat().st_mtime
    tied = max(a_stat, b_stat)
    import os
    os.utime(a, (tied, tied))
    os.utime(b, (tied, tied))

    assert latest_artifact([a, b]) == b
