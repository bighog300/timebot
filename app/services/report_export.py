from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from textwrap import wrap

from app.models.chat import GeneratedReport


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_report_lines(report: GeneratedReport) -> list[str]:
    lines = [
        report.title.strip() or "Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]
    if report.sections and isinstance(report.sections, dict):
        section_order = [
            ("executive_summary", "Executive Summary"),
            ("summary", "Summary"),
            ("timeline_analysis", "Timeline Analysis"),
            ("timeline", "Timeline"),
            ("relationship_analysis", "Relationship Analysis"),
            ("relationships", "Relationships"),
        ]
        for key, title in section_order:
            content = report.sections.get(key)
            if isinstance(content, str) and content.strip():
                lines.extend([title, content.strip(), ""])
    if len(lines) <= 3:
        lines.extend((report.content_markdown or "").strip().splitlines())
    return lines


def generate_report_pdf(report: GeneratedReport) -> bytes:
    lines = _build_report_lines(report)
    wrapped_lines: list[str] = []
    for line in lines:
        if not line:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(wrap(line, width=100) or [""])
    page_height = 792
    top_margin = 48
    bottom_margin = 48
    line_height = 14
    max_lines_per_page = max(1, (page_height - top_margin - bottom_margin) // line_height)

    pages: list[list[str]] = []
    for i in range(0, len(wrapped_lines), max_lines_per_page):
        pages.append(wrapped_lines[i : i + max_lines_per_page])
    if not pages:
        pages = [["Report content unavailable."]]

    objects: list[bytes] = []
    page_object_ids: list[int] = []
    content_object_ids: list[int] = []
    catalog_id = 1
    pages_id = 2
    next_id = 3
    font_id = next_id
    next_id += 1

    for _ in pages:
        page_object_ids.append(next_id)
        next_id += 1
        content_object_ids.append(next_id)
        next_id += 1

    total_objects = next_id - 1

    objects.append(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("latin-1"))
    kids = " ".join(f"{pid} 0 R" for pid in page_object_ids)
    objects.append(f"<< /Type /Pages /Kids [ {kids} ] /Count {len(page_object_ids)} >>".encode("latin-1"))
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for idx, page_lines in enumerate(pages):
        page_id = page_object_ids[idx]
        content_id = content_object_ids[idx]
        page_obj = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        )
        objects.append(page_obj.encode("latin-1"))

        text_lines = [b"BT", b"/F1 11 Tf", f"72 {page_height - top_margin} Td".encode("latin-1")]
        for line in page_lines:
            escaped = _escape_pdf_text(line)
            text_lines.append(f"({escaped}) Tj".encode("latin-1"))
            text_lines.append(f"0 -{line_height} Td".encode("latin-1"))
        text_lines.append(b"ET")
        content_stream = b"\n".join(text_lines)
        content_obj = b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content_stream), content_stream)
        objects.append(content_obj)

    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode("latin-1"))
        out.write(obj)
        out.write(b"\nendobj\n")
    xref_start = out.tell()
    out.write(f"xref\n0 {total_objects + 1}\n".encode("latin-1"))
    out.write(b"0000000000 65535 f \n")
    for i in range(1, total_objects + 1):
        out.write(f"{offsets[i]:010d} 00000 n \n".encode("latin-1"))
    out.write(
        (
            f"trailer\n<< /Size {total_objects + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("latin-1")
    )
    return out.getvalue()
