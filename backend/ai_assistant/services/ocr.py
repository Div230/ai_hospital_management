"""Local OCR with explicit failure, bounded PDF rendering and image normalization."""
import ctypes
import ctypes.util
import io
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
import pymupdf
from core.documents import validate_document


class OCRUnavailable(RuntimeError):
    pass


def render_pages(data: bytes, filename: str) -> list[Image.Image]:
    mime = validate_document(data, filename)
    if mime == 'application/pdf':
        with pymupdf.open(stream=data, filetype='pdf') as pdf:
            pages = []
            for page in pdf:
                scale = min(2, 2400 / max(page.rect.width, page.rect.height))
                pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
                pages.append(Image.frombytes('RGB', (pix.width, pix.height), pix.samples))
            return pages
    with Image.open(io.BytesIO(data)) as img:
        return [ImageOps.exif_transpose(img).convert('RGB')]


def preprocess(image: Image.Image) -> Image.Image:
    gray = ImageOps.autocontrast(image.convert('L'))
    if max(gray.size) < 1600:
        scale = min(2, 1600 / max(gray.size))
        gray = gray.resize((int(gray.width * scale), int(gray.height * scale)))
    return gray.filter(ImageFilter.MedianFilter(3))


def _library_ocr(image: Image.Image) -> str:
    """Use Tesseract's public C API where the CLI is not installed."""
    libname = ctypes.util.find_library('tesseract')
    if not libname:
        raise OCRUnavailable('Local Tesseract OCR is unavailable.')
    lib = ctypes.CDLL(libname)
    lib.TessBaseAPICreate.restype = ctypes.c_void_p
    lib.TessBaseAPIInit3.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
    lib.TessBaseAPISetImage.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lib.TessBaseAPIGetUTF8Text.argtypes = [ctypes.c_void_p]
    lib.TessBaseAPIGetUTF8Text.restype = ctypes.c_void_p
    lib.TessDeleteText.argtypes = [ctypes.c_void_p]
    lib.TessBaseAPIDelete.argtypes = [ctypes.c_void_p]
    api = lib.TessBaseAPICreate()
    if not api:
        raise OCRUnavailable('OCR initialization failed.')
    try:
        if lib.TessBaseAPIInit3(api, None, b'eng') != 0:
            raise OCRUnavailable('Tesseract English language data is unavailable.')
        pixels = ctypes.create_string_buffer(image.tobytes())
        lib.TessBaseAPISetImage(api, pixels, image.width, image.height, 1, image.width)
        text_ptr = lib.TessBaseAPIGetUTF8Text(api)
        if not text_ptr:
            return ''
        try:
            return ctypes.string_at(text_ptr).decode('utf-8')
        finally:
            lib.TessDeleteText(text_ptr)
    finally:
        lib.TessBaseAPIDelete(api)


def recognize(image: Image.Image) -> str:
    normalized = preprocess(image)
    command = os.environ.get('TESSERACT_CMD', 'tesseract')
    if shutil.which(command):
        buf = io.BytesIO()
        normalized.save(buf, format='PNG')
        result = subprocess.run([command, 'stdin', 'stdout', '-l', 'eng'], input=buf.getvalue(),
                                capture_output=True, timeout=35, check=False)
        if result.returncode:
            raise OCRUnavailable('Tesseract could not process this image.')
        return result.stdout.decode('utf-8').strip()
    return _library_ocr(normalized).strip()


def extract_text_from_file(file_path: str) -> str:
    data = Path(file_path).read_bytes()
    return '\n\n'.join(recognize(page) for page in render_pages(data, file_path))
