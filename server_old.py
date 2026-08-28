from __future__ import annotations

import logging
from typing import Optional, Any
from io import BytesIO
import zipfile
import re
import os
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response, FileResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.requests import Request
from PIL import Image, ImageOps, UnidentifiedImageError

# -------------------------
# Logging
# -------------------------
logger = logging.getLogger("uvicorn.error")

# Optional: HEIC/HEIF support if installed
try:
    import pillow_heif  # noqa: F401
    HAVE_HEIF = True
except Exception:
    HAVE_HEIF = False

# Optional: PDF compression via pikepdf
try:
    import pikepdf
    from pikepdf import Pdf, Name, Dictionary
    HAVE_PDF = True
except Exception:
    HAVE_PDF = False

app = FastAPI(title="Universal Compressor", version="1.4.0")

# -------------------------
# Global exception handlers
# -------------------------

@app.exception_handler(HTTPException)
async def _http_exc_handler(request: Request, exc: HTTPException):
    logger.warning("HTTPException: %s %s -> %s", request.method, request.url.path, exc.detail)
    return await http_exception_handler(request, exc)

@app.exception_handler(Exception)
async def _any_exc_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return Response(
        content=f'{{"detail": "Internal error: {type(exc).__name__}: {str(exc)}"}}',
        media_type="application/json",
        status_code=500,
    )


# -------------------------
# Image utilities
# -------------------------

def strip_metadata(img: Image.Image) -> Image.Image:
    if img.mode == "P":
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    data = list(img.getdata())
    clean = Image.new(img.mode, img.size)
    clean.putdata(data)
    return clean

def save_jpeg(img: Image.Image, quality: int) -> bytes:
    buf = BytesIO()
    img.convert("RGB").save(
        buf, format="JPEG", quality=quality,
        subsampling="4:2:0", progressive=True, optimize=True
    )
    return buf.getvalue()

def save_webp(img: Image.Image, quality: int) -> bytes:
    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=6)
    return buf.getvalue()

def save_png_optimized(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    return buf.getvalue()

def save_png_quantized_if_useful(img: Image.Image) -> bytes:
    base = img if img.mode in ("RGB", "RGBA") else img.convert("RGBA")
    pal = base.convert("P", palette=Image.ADAPTIVE, colors=256, dither=Image.FLOYDSTEINBERG)
    buf = BytesIO()
    pal.save(buf, format="PNG", optimize=True, compress_level=9)
    return buf.getvalue()

def q_search(saver, img: Image.Image, target_bytes: int, q_min=60, q_max=90):
    best = None
    lo, hi = q_min, q_max
    for _ in range(10):
        if lo > hi:
            break
        q = (lo + hi) // 2
        data = saver(img, q)
        if len(data) <= target_bytes:
            best = (q, data); lo = q + 1
        else:
            hi = q - 1
    return best

def open_image_from_upload(file: UploadFile) -> Image.Image:
    data = file.file.read()
    file.file.seek(0)
    if not data:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    if HAVE_HEIF and re.search(r"\.(heic|heif)$", (file.filename or "").lower()):
        import pillow_heif
        pillow_heif.register_heif_opener()

    try:
        img = Image.open(BytesIO(data))
        img.load()
        img = ImageOps.exif_transpose(img)
        return img
    except Image.DecompressionBombError as e:
        raise HTTPException(status_code=413, detail=f"Image too large: {e}") from e
    except UnidentifiedImageError as e:
        raise HTTPException(status_code=415, detail="Unsupported or corrupt image.") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image: {e}") from e

def compress_image(
    file: UploadFile,
    target_kb: int,
    max_w: Optional[int],
    max_h: Optional[int],
    allow_png_quantize: bool,
):
    img_in = open_image_from_upload(file)
    img = img_in

    orig_fmt = (getattr(img_in, "format", None) or "PNG").upper()
    if orig_fmt == "JPG":
        orig_fmt = "JPEG"

    supported = {"JPEG", "PNG", "WEBP", "GIF", "BMP", "TIFF", "ICO"}
    if HAVE_HEIF:
        supported.add("HEIF")
    if orig_fmt not in supported:
        orig_fmt = "PNG" if ("A" in img.getbands()) else "JPEG"

    if max_w or max_h:
        w, h = img.size
        nw, nh = w, h
        if max_w and w > max_w:
            s = max_w / w; nw, nh = int(w*s), int(h*s)
        if max_h and nh > max_h:
            s = max_h / nh; nw, nh = int(nw*s), int(nh*s)
        if (nw, nh) != (w, h):
            img = img.resize((nw, nh), Image.LANCZOS)

    img = strip_metadata(img)
    target_bytes = max(1, target_kb) * 1024

    if orig_fmt in ("JPEG", "BMP", "TIFF", "ICO"):
        res = q_search(save_jpeg, img, target_bytes)
        data = res[1] if res else save_jpeg(img, 60)
        media, name = "image/jpeg", "compressed.jpg"

    elif orig_fmt == "WEBP":
        res = q_search(save_webp, img, target_bytes)
        data = res[1] if res else save_webp(img, 60)
        media, name = "image/webp", "compressed.webp"

    elif orig_fmt == "GIF":
        try:
            img.seek(1); animated = True
        except EOFError:
            animated = False
        img.seek(0)
        if animated:
            res = q_search(save_webp, img.convert("RGB"), target_bytes)
            data = res[1] if res else save_webp(img.convert("RGB"), 65)
            media, name = "image/webp", "compressed.webp"
        else:
            has_alpha = ("A" in img.getbands())
            if has_alpha:
                data_opt = save_png_optimized(img)
                if allow_png_quantize:
                    data_q = save_png_quantized_if_useful(img)
                    if len(data_q) < len(data_opt) * 0.85:
                        data_opt = data_q
                data, media, name = data_opt, "image/png", "compressed.png"
            else:
                res = q_search(save_jpeg, img, target_bytes)
                data = res[1] if res else save_jpeg(img, 65)
                media, name = "image/jpeg", "compressed.jpg"

    else:
        has_alpha = ("A" in img.getbands())
        if has_alpha:
            data_opt = save_png_optimized(img)
            if allow_png_quantize:
                data_q = save_png_quantized_if_useful(img)
                if len(data_q) < len(data_opt) * 0.85:
                    data_opt = data_q
            data, media, name = data_opt, "image/png", "compressed.png"
        else:
            res = q_search(save_webp, img, target_bytes)
            data = res[1] if res else save_webp(img, 65)
            if len(data) > target_bytes:
                res2 = q_search(save_jpeg, img, target_bytes)
                if res2:
                    data = res2[1]
                    media, name = "image/jpeg", "compressed.jpg"
                else:
                    media, name = "image/webp", "compressed.webp"
            else:
                media, name = "image/webp", "compressed.webp"

    return data, media, name


# -------------------------
# PDF utilities (AGGRESSIVE MB->KB)
# -------------------------

def _resize_if_needed(im: Image.Image, max_dim: Optional[int]) -> Image.Image:
    if not max_dim:
        return im
    w, h = im.size
    m = max(w, h)
    if m <= max_dim:
        return im
    scale = max_dim / m
    return im.resize((max(1, int(w*scale)), max(1, int(h*scale))), Image.LANCZOS)

def _jpeg_recompress(pike_img_stream: Any, quality: int = 60, max_dim: Optional[int] = None) -> Optional[bytes]:
    try:
        with BytesIO(bytes(pike_img_stream.read_bytes())) as bio:
            im = Image.open(bio); im.load()
        im = _resize_if_needed(im, max_dim)
        buf = BytesIO()
        im.convert("RGB").save(buf, "JPEG", quality=quality,
                               subsampling="4:2:0", optimize=True, progressive=True)
        return buf.getvalue()
    except Exception:
        return None

def _flate_to_jpeg_if_beneficial(pike_img_stream: Any, quality: int = 60, max_dim: Optional[int] = None) -> Optional[bytes]:
    try:
        with BytesIO(bytes(pike_img_stream.read_bytes())) as bio:
            im = Image.open(bio); im.load()
        if "A" in im.getbands():
            return None
        im = _resize_if_needed(im, max_dim)
        jpg = save_jpeg(im, quality)
        png = save_png_optimized(im)
        return jpg if len(jpg) < len(png) * 0.9 else None
    except Exception:
        return None

def compress_pdf_bytes(pdf_bytes: bytes, image_quality: int = 60, max_dim: Optional[int] = None) -> bytes:
    """
    Rewrites embedded images (JPEG recompress; FLATE->JPEG if beneficial),
    optionally downscales images to max_dim. Keeps vector content intact.
    """
    if not HAVE_PDF:
        return pdf_bytes

    try:
        with Pdf.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                resources = page.get("/Resources", Dictionary())
                xobjects = resources.get("/XObject", Dictionary())
                for name in list(xobjects.keys()):
                    xobj = xobjects[name]
                    if not isinstance(xobj, pikepdf.Stream):
                        continue
                    if xobj.get("/Subtype", None) != pikepdf.Name("/Image"):
                        continue

                    filters = xobj.get("/Filter", None)
                    if isinstance(filters, pikepdf.Array):
                        filt_list = [str(f) for f in filters]
                    elif filters is None:
                        filt_list = []
                    else:
                        filt_list = [str(filters)]

                    try_new_stream = None
                    if "/DCTDecode" in filt_list:
                        data = _jpeg_recompress(xobj, quality=image_quality, max_dim=max_dim)
                        if data:
                            try_new_stream = data
                    elif "/FlateDecode" in filt_list or filters is None:
                        data = _flate_to_jpeg_if_beneficial(xobj, quality=image_quality, max_dim=max_dim)
                        if data:
                            try_new_stream = data

                    if try_new_stream:
                        new_stream = pdf.make_stream(try_new_stream)
                        new_stream[Name("/Type")] = Name("/XObject")
                        new_stream[Name("/Subtype")] = Name("/Image")
                        new_stream[Name("/Filter")] = Name("/DCTDecode")
                        new_stream[Name("/ColorSpace")] = xobj.get(Name("/ColorSpace"), Name("/DeviceRGB"))
                        new_stream[Name("/BitsPerComponent")] = xobj.get(Name("/BitsPerComponent"), 8)
                        xobjects[name] = new_stream

            out = BytesIO()
            pdf.save(
                out,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                linearize=True,
                qdf=False,
            )
            out_bytes = out.getvalue()
            return out_bytes if len(out_bytes) <= len(pdf_bytes) else pdf_bytes

    except pikepdf.PasswordError as e:
        raise HTTPException(status_code=423, detail="PDF is password-protected.") from e
    except pikepdf.PdfError as e:
        raise HTTPException(status_code=415, detail=f"Invalid or corrupted PDF: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process PDF: {e}") from e

def compress_pdf_mb_to_kb(pdf_bytes: bytes, target_kb: int) -> bytes:
    """
    Aggressively compress PDF from MB to KB range.
    Uses very low quality and extreme downscaling if needed.
    """
    if not HAVE_PDF:
        return pdf_bytes

    original_size_mb = len(pdf_bytes) / (1024 * 1024)
    target_bytes = target_kb * 1024

    # If already under target, just optimize
    if len(pdf_bytes) <= target_bytes:
        logger.info(f"PDF already under target ({len(pdf_bytes)} bytes <= {target_bytes} bytes)")
        return compress_pdf_bytes(pdf_bytes, image_quality=75, max_dim=None)

    logger.info(f"PDF size: {original_size_mb:.2f} MB, target: {target_kb} KB")

    # AGGRESSIVE compression strategy for MB -> KB
    # Start with extreme settings and work backwards
    strategies = [
        # (max_dim, quality_min, quality_max)
        (400, 10, 30),    # Very aggressive
        (600, 15, 35),    # Aggressive
        (800, 20, 40),    # Strong
        (1000, 25, 50),   # Moderate
        (1200, 30, 60),   # Light
        (1600, 40, 70),   # Minimal
        (2000, 50, 80),   # Very light
    ]

    smallest = None
    smallest_size = len(pdf_bytes)

    for max_dim, q_min, q_max in strategies:
        logger.info(f"Trying strategy: max_dim={max_dim}, quality={q_min}-{q_max}")

        # Binary search for quality
        lo, hi = q_min, q_max
        for iteration in range(8):
            if lo > hi:
                break

            q = (lo + hi) // 2
            result = compress_pdf_bytes(pdf_bytes, image_quality=q, max_dim=max_dim)
            result_size = len(result)

            logger.info(f"  Quality {q}: {result_size / 1024:.1f} KB")

            # Track smallest
            if result_size < smallest_size:
                smallest = result
                smallest_size = result_size

            # Check if we hit target
            if result_size <= target_bytes:
                logger.info(f"✓ Target achieved: {result_size / 1024:.1f} KB <= {target_kb} KB")
                return result

            # Adjust search
            if result_size > target_bytes:
                hi = q - 1
            else:
                lo = q + 1

    # If we couldn't reach target, return the smallest we achieved
    final_size_kb = smallest_size / 1024
    logger.warning(f"Could not reach {target_kb} KB target. Best achieved: {final_size_kb:.1f} KB")

    return smallest if smallest else pdf_bytes


# -------------------------
# DOCX utilities
# -------------------------

def compress_docx_bytes(docx_bytes: bytes, target_kb: int, allow_png_quantize: bool) -> bytes:
    in_buf = BytesIO(docx_bytes)
    out_buf = BytesIO()

    try:
        with zipfile.ZipFile(in_buf, "r") as zin, zipfile.ZipFile(
            out_buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.startswith("word/media/"):
                    try:
                        im = Image.open(BytesIO(data)); im.load()
                        im = ImageOps.exif_transpose(im)
                        has_alpha = ("A" in im.getbands())
                        target_bytes = max(1, target_kb) * 1024
                        if has_alpha:
                            opt = save_png_optimized(im)
                            if allow_png_quantize:
                                q = save_png_quantized_if_useful(im)
                                if len(q) < len(opt) * 0.85:
                                    opt = q
                            new_data = opt
                        else:
                            res = q_search(save_webp, im, target_bytes)
                            new_data = res[1] if res else save_webp(im, 70)
                            if len(new_data) > target_bytes:
                                res2 = q_search(save_jpeg, im, target_bytes)
                                if res2:
                                    new_data = res2[1]
                        data = new_data
                    except Exception:
                        pass

                zout.writestr(item, data)

        return out_buf.getvalue()

    except zipfile.BadZipFile as e:
        raise HTTPException(status_code=415, detail="Not a valid .docx file.") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process DOCX: {e}") from e


# -------------------------
# Helpers (naming)
# -------------------------

def _write_and_schedule_delete(path: Path, data: bytes, background_tasks: BackgroundTasks) -> Path:
    path = path.resolve()
    with open(path, "wb") as f:
        f.write(data)
    # ensure deletion after response is sent
    background_tasks.add_task(os.remove, str(path))
    return path


# -------------------------
# API
# -------------------------

@app.post("/compress_same")
async def compress_same(
    file: UploadFile = File(...),
    target_kb: int = Query(200, ge=10),
    max_w: int | None = Query(None, ge=32),
    max_h: int | None = Query(None, ge=32),
    allow_png_quantize: bool = Query(True),
    background_tasks: BackgroundTasks = None,
):
    """
    Compress files to target KB size:
    - Images: JPEG/PNG/WEBP/GIF/BMP/TIFF/ICO (+ HEIC if pillow-heif)
    - PDF: AGGRESSIVE MB->KB compression (if pikepdf available). Save to disk with original name, send, then delete.
    - DOCX: recompress images inside word/media/*
    """
    try:
        filename_lower = (file.filename or "").lower()
        original_name = Path(file.filename or "download.bin").name

        # PDF - AGGRESSIVE MB->KB COMPRESSION
        if filename_lower.endswith(".pdf"):
            pdf_bytes = await file.read()
            if not pdf_bytes:
                raise HTTPException(status_code=400, detail="Empty file uploaded.")

            original_size = len(pdf_bytes)
            original_size_mb = original_size / (1024 * 1024)

            if HAVE_PDF:
                logger.info(f"📄 Processing PDF: {original_size_mb:.2f} MB -> target {target_kb} KB")
                data = compress_pdf_mb_to_kb(pdf_bytes, target_kb=target_kb)
                final_size = len(data)
                final_size_kb = final_size / 1024
                compression_ratio = (1 - final_size / original_size) * 100
                logger.info(f"✓ PDF compressed: {original_size_mb:.2f} MB -> {final_size_kb:.1f} KB ({compression_ratio:.1f}% reduction)")
            else:
                logger.warning("pikepdf not available; returning original PDF unchanged.")
                data = pdf_bytes
                final_size = len(data)
                compression_ratio = 0

            # Save to disk with the SAME NAME, send back, then delete
            out_path = _write_and_schedule_delete(Path(original_name), data, background_tasks)

            headers = {
                "X-Original-Size": str(original_size),
                "X-New-Size": str(final_size),
                "X-Compression-Ratio": f"{compression_ratio:.1f}%",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            }
            return FileResponse(path=str(out_path), media_type="application/pdf", filename=original_name, headers=headers)

        # DOCX
        if filename_lower.endswith(".docx"):
            docx_bytes = await file.read()
            if not docx_bytes:
                raise HTTPException(status_code=400, detail="Empty file uploaded.")
            original_size = len(docx_bytes)
            data = compress_docx_bytes(docx_bytes, target_kb=target_kb, allow_png_quantize=allow_png_quantize)

            # Save to disk with the SAME NAME, send back, then delete
            out_path = _write_and_schedule_delete(Path(original_name), data, background_tasks)

            headers = {
                "X-Original-Size": str(original_size),
                "X-New-Size": str(len(data)),
            }
            return FileResponse(path=str(out_path), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=original_name, headers=headers)

        # Legacy .DOC not supported
        if filename_lower.endswith(".doc"):
            raise HTTPException(
                status_code=415,
                detail="Legacy .doc is not supported. Please convert to .docx first.",
            )

        # Images
        data, media, _name = compress_image(
            file=file,
            target_kb=target_kb,
            max_w=max_w,
            max_h=max_h,
            allow_png_quantize=allow_png_quantize,
        )

        # Save to disk with the SAME NAME (even if media type changed), send back, then delete
        out_path = _write_and_schedule_delete(Path(original_name), data, background_tasks)

        headers = {}
        return FileResponse(path=str(out_path), media_type=media, filename=original_name, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected failure in /compress_same")
        raise HTTPException(status_code=500, detail=f"Unexpected failure: {e}") from e
