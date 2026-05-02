from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.text_extractor import TextExtractor


def test_docx_extracts_paragraphs_and_table_cells(tmp_path):
    extractor = TextExtractor()
    fake_doc = MagicMock()
    fake_doc.paragraphs = [MagicMock(text="Para 1"), MagicMock(text="   "), MagicMock(text="Para 2")]

    row1 = MagicMock(cells=[MagicMock(text="R1C1"), MagicMock(text="")])
    row2 = MagicMock(cells=[MagicMock(text="  R2C1  "), MagicMock(text="R2C2")])
    fake_table = MagicMock(rows=[row1, row2])
    fake_doc.tables = [fake_table]

    with patch("docx.Document", return_value=fake_doc):
        text, page_count, word_count = extractor.extract(tmp_path / "doc.docx", "docx")

    assert page_count is None
    assert text == "Para 1\nPara 2\nR1C1\nR2C1\nR2C2"
    assert word_count == len(text.split())


def test_legacy_office_formats_report_unsupported():
    extractor = TextExtractor()
    for ext in ("doc", "xls", "ppt"):
        text, page_count, word_count = extractor.extract(Path(f"/tmp/a.{ext}"), ext)
        assert text is None
        assert page_count is None
        assert word_count is None


def test_xlsx_uses_read_only_data_only(tmp_path):
    extractor = TextExtractor()
    fake_sheet = MagicMock()
    fake_sheet.iter_rows.return_value = [("A", None, "B"), (None, None, None), ("C",)]
    fake_wb = MagicMock(worksheets=[fake_sheet])

    with patch("openpyxl.load_workbook", return_value=fake_wb) as load_wb:
        text, page_count, word_count = extractor.extract(tmp_path / "book.xlsx", "xlsx")

    load_wb.assert_called_once_with(tmp_path / "book.xlsx", data_only=True, read_only=True)
    assert text == "A | B\nC"
    assert page_count == 1
    assert word_count == len(text.split())


def test_ocr_failure_logs_without_raw_content(tmp_path, caplog):
    extractor = TextExtractor()
    sample_image = tmp_path / "scan.png"
    sample_image.write_bytes(b"not-a-real-image")

    with patch("PIL.Image.open", side_effect=RuntimeError("image open failed secret-text")):
        text, page_count, word_count = extractor.extract(sample_image, "png")

    assert text is None
    assert page_count is None
    assert word_count is None
    messages = "\n".join(rec.message for rec in caplog.records)
    assert "Image OCR attempted and failed" in messages
    assert "raw extracted" not in messages.lower()
