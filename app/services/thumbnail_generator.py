import io
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = (300, 400)

_FILE_ICONS = {
    "pdf": "PDF", "docx": "DOCX", "doc": "DOC",
    "xlsx": "XLSX", "xls": "XLS", "pptx": "PPTX", "ppt": "PPT",
    "txt": "TXT",
}


class ThumbnailGenerator:
    def generate(self, file_path: Path, file_type: str) -> Optional[bytes]:
        ft = file_type.lower().lstrip(".")
        try:
            if ft == "pdf":
                return self._from_pdf(file_path)
            elif ft in ("jpg", "jpeg", "png", "gif", "tiff", "bmp"):
                return self._from_image(file_path)
            else:
                return self._generic(ft)
        except Exception as e:
            logger.error("Thumbnail generation failed for %s: %s", file_path, e)
            return None

    def _from_pdf(self, file_path: Path) -> Optional[bytes]:
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(str(file_path), dpi=72, first_page=1, last_page=1)
            if images:
                return self._resize(images[0])
        except Exception as e:
            logger.warning("PDF thumbnail failed, using generic: %s", e)
        return self._generic("pdf")

    def _from_image(self, file_path: Path) -> Optional[bytes]:
        try:
            from PIL import Image

            return self._resize(Image.open(file_path))
        except Exception as e:
            logger.error("Image thumbnail error: %s", e)
            return None

    def _resize(self, img) -> bytes:
        from PIL import Image

        img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        return buf.getvalue()

    def _generic(self, file_type: str) -> Optional[bytes]:
        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", THUMBNAIL_SIZE, (240, 240, 240))
            draw = ImageDraw.Draw(img)
            label = _FILE_ICONS.get(file_type, file_type.upper()[:4])

            # Draw colored header bar
            draw.rectangle([0, 0, THUMBNAIL_SIZE[0], 80], fill=(70, 130, 180))
            draw.text(
                (THUMBNAIL_SIZE[0] // 2, 40), label,
                fill=(255, 255, 255), anchor="mm",
            )

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return buf.getvalue()
        except Exception as e:
            logger.error("Generic thumbnail error: %s", e)
            return None


thumbnail_generator = ThumbnailGenerator()
