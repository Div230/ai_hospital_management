"""Bounded content validation shared by all medical document uploads."""
import io
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import pymupdf

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 5
MAX_PIXELS = 20_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class DocumentError(ValueError):
    pass


def validate_document(data: bytes, filename: str) -> str:
    if not data or len(data) > MAX_BYTES:
        raise DocumentError('Upload a nonempty document of at most 10 MB.')
    suffix = Path(filename).suffix.lower()
    if suffix == '.pdf':
        if not data.startswith(b'%PDF-'):
            raise DocumentError('The file content does not match PDF format.')
        try:
            with pymupdf.open(stream=data, filetype='pdf') as doc:
                if doc.needs_pass or not 1 <= len(doc) <= MAX_PAGES:
                    raise DocumentError('PDF must be unencrypted and contain 1–5 pages.')
                if doc.embfile_count() or any(marker in data for marker in (b'/JavaScript', b'/JS', b'/Launch', b'/RichMedia')):
                    raise DocumentError('Active content and embedded files are unsupported.')
                for page in doc:
                    if max(page.rect.width, page.rect.height) > 3000 or page.rect.is_empty:
                        raise DocumentError('PDF page dimensions are unsupported.')
        except (RuntimeError, ValueError) as exc:
            if isinstance(exc, DocumentError):
                raise
            raise DocumentError('The PDF is damaged or unsupported.') from exc
        return 'application/pdf'
    if suffix not in ('.png', '.jpg', '.jpeg'):
        raise DocumentError('Supported file types: PNG, JPG, JPEG, PDF.')
    try:
        with Image.open(io.BytesIO(data)) as img:
            expected = 'PNG' if suffix == '.png' else 'JPEG'
            if img.format != expected or img.width * img.height > MAX_PIXELS:
                raise DocumentError('Image format or dimensions are unsupported.')
            img.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise DocumentError('The image is damaged or too large.') from exc
    return 'image/png' if suffix == '.png' else 'image/jpeg'


def validate_upload(upload):
    data = upload.read(MAX_BYTES + 1)
    upload.seek(0)
    return validate_document(data, upload.name)
