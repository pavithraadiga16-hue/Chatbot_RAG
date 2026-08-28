from __future__ import annotations

import logging
from typing import Optional, Any
from io import BytesIO
import zipfile
import re
import os
import threading
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import http_exception_handler
from fastapi.requests import Request
from PIL import Image, ImageOps, UnidentifiedImageError

# Optional: HEIC/HEIF support if installed
try:
    import pillow_heif  # noqa: F401
    HAVE_HEIF = True
except Exception:
    HAVE_HEIF = False

# Optional: PDF handling via PyMuPDF
try:
    import fitz  # PyMuPDF
    HAVE_FITZ = True
except Exception:
    HAVE_FITZ = False

# Import TTS engine and router
import tts_engine
import tts_router

# -------------------------
# Logging
# -------------------------
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup warm-up and graceful shutdown."""
    # Warm up MeloTTS in a background thread so startup isn't blocked
    def _async_warmup():
        try:
            logger.info("Initializing MeloTTS warmup in background thread...")
            tts_engine.warmup()
        except Exception as e:
            logger.warning("TTS background warmup encountered an issue: %s", e)

    warmup_thread = threading.Thread(target=_async_warmup, daemon=True, name="TTS-Warmup")
    warmup_thread.start()
    yield


app = FastAPI(
    title="Universal Compressor & MeloTTS Voice Server",
    version="2.0.0",
    lifespan=lifespan
)

# -------------------------
# CORS Middleware
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# PDF utilities (IMAGE-ONLY COMPRESSION, TEXT UNTOUCHED)
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

def compress_pdf_images_fitz(pdf_bytes: bytes, quality: int = 60, max_dim: Optional[int] = None) -> bytes:
    """
    Robust PDF image compression using PyMuPDF (fitz):
    - Uses page.get_image_info() → only real valid images
    - Filters invalid xrefs and masks
    - Correct alpha handling (composite on white)
    - Proper CMYK/grayscale → RGB conversion
    - Uses replace_image() → text/vectors untouched
    """
    if not HAVE_FITZ:
        return pdf_bytes

    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        total_images = 0
        skipped = 0

        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            image_infos = page.get_image_info(xrefs=True)

            if not image_infos:
                continue

            logger.info(f"Page {page_index}: found {len(image_infos)} valid images to compress.")

            for info in image_infos:
                xref = info["xref"]

                if xref == 0:  # inline images or invalid
                    skipped += 1
                    continue

                if info["width"] <= 0 or info["height"] <= 0:
                    skipped += 1
                    continue

                try:
                    pix = fitz.Pixmap(doc, xref)

                    # === Handle alpha channel (composite on white) ===
                    if pix.alpha:
                        if pix.colorspace == fitz.csRGB:
                            rgba = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
                        elif pix.colorspace == fitz.csGRAY:
                            la = Image.frombytes("LA", (pix.width, pix.height), pix.samples)
                            rgba = la.convert("RGBA")
                        else:
                            rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                            img_pil = Image.frombytes("RGB", (rgb_pix.width, rgb_pix.height), rgb_pix.samples)
                            rgb_pix = None
                        white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                        img_pil = Image.alpha_composite(white_bg, rgba).convert("RGB")
                    else:
                        if pix.colorspace == fitz.csRGB and pix.n == 3:
                            img_pil = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                        elif pix.colorspace == fitz.csGRAY and pix.n == 1:
                            img_pil = Image.frombytes("L", (pix.width, pix.height), pix.samples).convert("RGB")
                        else:
                            rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                            img_pil = Image.frombytes("RGB", (rgb_pix.width, rgb_pix.height), rgb_pix.samples)
                            rgb_pix = None

                    # Optional downscaling
                    if max_dim is not None:
                        img_pil = _resize_if_needed(img_pil, max_dim=max_dim)

                    # Compress to JPEG
                    new_bytes = save_jpeg(img_pil, quality=quality)
                    page.replace_image(xref, stream=new_bytes)

                    total_images += 1
                    pix = None

                except Exception as e:
                    logger.exception(f"Failed to process valid image xref={xref} on page={page_index}")
                    if 'pix' in locals():
                        pix = None
                    continue

        logger.info(f"Compressed {total_images} images" + (f", skipped {skipped} invalid/degenerate" if skipped > 0 else ""))
        out_bytes = doc.tobytes(garbage=4, deflate=True, clean=True)
        return out_bytes if len(out_bytes) < len(pdf_bytes) else pdf_bytes

    except Exception as e:
        logger.exception("PDF compression failed completely")
        return pdf_bytes
    finally:
        if doc is not None:
            try:
                doc.close()
            except:
                pass


def compress_pdf_mb_to_kb(pdf_bytes: bytes, target_kb: int) -> bytes:
    """
    Compress PDF as much as possible by recompressing ONLY images.
    Text and vector graphics remain untouched.
    """
    original_size = len(pdf_bytes)
    original_kb = original_size / 1024.0
    original_mb = original_size / (1024.0 * 1024.0)
    logger.info(
        f"📄 PDF size: {original_mb:.2f} MB (~{original_kb:.1f} KB), "
        f"will compress images as much as possible (text stays sharp)."
    )

    if not HAVE_FITZ:
        logger.warning("PyMuPDF (fitz) not available, cannot compress PDF images.")
        return pdf_bytes

    best_bytes = pdf_bytes
    best_size = original_size

    strategies = [
        (2000, 70),   # high quality
        (1600, 60),   # good quality, mild downscale
        (1400, 55),   # stronger compression
        (1200, 50),   # stronger
        (1000, 45),   # aggressive
    ]

    for max_dim, quality in strategies:
        logger.info(f"Trying image-only strategy: max_dim={max_dim}, quality={quality}")
        candidate = compress_pdf_images_fitz(best_bytes, quality=quality, max_dim=max_dim)
        cand_size = len(candidate)
        cand_kb = cand_size / 1024.0

        logger.info(f"  -> Result size: {cand_kb:.1f} KB")

        if cand_size < best_size:
            best_bytes = candidate
            best_size = cand_size

    best_kb = best_size / 1024.0
    reduction = (1 - best_size / original_size) * 100.0
    logger.info(
        f"Final PDF size after image-only compression: {best_kb:.1f} KB "
        f"(~{reduction:.1f}% reduction)."
    )

    return best_bytes


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
                        im = Image.open(BytesIO(data))
                        im.load()
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
# Helpers (naming & cleanup)
# -------------------------

def _write_and_schedule_delete(path: Path, data: bytes, background_tasks: BackgroundTasks = None) -> Path:
    path = path.resolve()
    with open(path, "wb") as f:
        f.write(data)
    if background_tasks is not None:
        background_tasks.add_task(os.remove, str(path))
    return path


# -------------------------
# API Endpoints
# -------------------------

@app.get("/")
async def root():
    return {
        "service": "AI Parrophins Server",
        "endpoints": {
            "compression": "/compress_same",
            "tts_direct": "/tts",
            "tts_batch": "/batch/synthesize",
            "tts_result": "/batch/result/{job_id}",
            "health": "/health"
        },
        "version": "2.0.0"
    }


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
    Compress files as much as possible:
    - Images: JPEG/PNG/WEBP/GIF/BMP/TIFF/ICO (+ HEIC if pillow-heif)
    - PDF:
        * Only embedded images are recompressed (downscaled + lower JPEG quality).
        * Text and vector content remain untouched (no blurring of text).
    - DOCX: recompress images inside word/media/*
    """
    try:
        filename_lower = (file.filename or "").lower()
        original_name = Path(file.filename or "download.bin").name

        # PDF
        if filename_lower.endswith(".pdf"):
            pdf_bytes = await file.read()
            if not pdf_bytes:
                raise HTTPException(status_code=400, detail="Empty file uploaded.")

            original_size = len(pdf_bytes)
            original_size_mb = original_size / (1024 * 1024)

            logger.info(f"📄 Processing PDF: {original_size_mb:.2f} MB (image-only compression, text preserved)")

            data = compress_pdf_mb_to_kb(pdf_bytes, target_kb=target_kb)
            final_size = len(data)
            final_size_kb = final_size / 1024
            compression_ratio = (1 - final_size / original_size) * 100

            logger.info(
                f"✓ PDF compressed: {original_size_mb:.2f} MB -> "
                f"{final_size_kb:.1f} KB ({compression_ratio:.1f}% reduction)"
            )

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

            out_path = _write_and_schedule_delete(Path(original_name), data, background_tasks)

            headers = {
                "X-Original-Size": str(original_size),
                "X-New-Size": str(len(data)),
            }
            return FileResponse(
                path=str(out_path),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename=original_name,
                headers=headers,
            )

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

        out_path = _write_and_schedule_delete(Path(original_name), data, background_tasks)

        headers = {}
        return FileResponse(path=str(out_path), media_type=media, filename=original_name, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected failure in /compress_same")
        raise HTTPException(status_code=500, detail=f"Unexpected failure: {e}") from e


# -------------------------
# Mount TTS Routes
# -------------------------
app.include_router(tts_router.router)