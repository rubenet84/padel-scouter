"""Avatar service — image validation, processing, and storage."""

import io
import logging
import os
import uuid as uuid_lib

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

AVATAR_DIR = "app/static/avatars"
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_DIM = 2048


def process_avatar(contents: bytes, filename: str, old_avatar_url: str | None = None) -> str:
    """
    Validate, re-encode, and save an avatar image. Returns the public URL.

    OWASP A03 protections: re-encode strips EXIF/metadata, extension forced
    to match actual format saved, random filename prevents path traversal.
    """
    # Validate size
    if len(contents) == 0:
        raise ValueError("Archivo vacío")
    if len(contents) > MAX_AVATAR_SIZE:
        raise ValueError("Archivo demasiado grande (máx 5MB)")

    # Validate extension
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Formato no permitido: {ext}. Usá JPG, PNG, GIF o WebP.")

    # Structural validation with Pillow
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
    except UnidentifiedImageError:
        raise ValueError("El archivo no es una imagen válida")
    except Exception as e:
        logger.error("Error al verificar imagen: %s", e)
        raise ValueError("El archivo no es una imagen válida")

    # Re-open after verify (verify consumes the file)
    img = Image.open(io.BytesIO(contents))

    # Convert to RGB (strip EXIF, alpha, etc.)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # Resize if too large
    if img.width > MAX_DIM or img.height > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)

    # Ensure avatar directory exists
    os.makedirs(AVATAR_DIR, exist_ok=True)

    # Save re-encoded image (strips all EXIF/metadata)
    if img.mode == "RGBA":
        ext = ".png"
        out_name = f"{uuid_lib.uuid4().hex}{ext}"
        out_path = os.path.join(AVATAR_DIR, out_name)
        img.save(out_path, "PNG")
    else:
        ext = ".jpg"
        out_name = f"{uuid_lib.uuid4().hex}{ext}"
        out_path = os.path.join(AVATAR_DIR, out_name)
        img.save(out_path, "JPEG", quality=85)

    avatar_url = f"/static/avatars/{out_name}"

    # Remove old avatar if exists
    if old_avatar_url:
        old_path = os.path.join("app", old_avatar_url.lstrip("/"))
        if os.path.exists(old_path):
            os.remove(old_path)

    return avatar_url
