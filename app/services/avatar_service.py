"""Servicio de avatar — validación, procesamiento y almacenamiento de imágenes.

Gestiona el flujo completo de subida de avatar con protecciones OWASP A03:
1. Validación de tamaño (máx 5 MB) y extensión (JPG, PNG, GIF, WebP).
2. Verificación estructural con Pillow (detecta archivos no-imagen).
3. Re-encodeo de la imagen para eliminar metadatos EXIF y contenido malicioso.
4. Redimensionado si excede 2048px en cualquier dimensión.
5. Renombrado aleatorio (UUID) para prevenir path traversal.
6. Eliminación del avatar anterior del sistema de archivos.

La extensión final se fuerza al formato real guardado (.png para RGBA, .jpg para RGB)
independientemente de la extensión del archivo original.
"""

import io
import logging
import os
import uuid as uuid_lib

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

# Directorio donde se almacenan los avatares (servido como estático por FastAPI)
AVATAR_DIR = "app/static/avatars"
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB máximo
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_DIM = 2048  # dimensión máxima en píxeles (ancho o alto)


def process_avatar(contents: bytes, filename: str, old_avatar_url: str | None = None) -> str:
    """Valida, re-encodea y guarda una imagen de avatar. Devuelve la URL pública.

    Implementa las protecciones OWASP A03 (Injection) para subida de archivos:
    - Re-encodeo con Pillow elimina EXIF, metadatos y posibles payloads.
    - Nombre de archivo aleatorio (UUID) previene path traversal.
    - Extensión forzada al formato real guardado, no a la original.

    Args:
        contents: Bytes crudos del archivo subido.
        filename: Nombre original del archivo (solo se usa para validar extensión).
        old_avatar_url: URL del avatar anterior a eliminar, o None si no existe.

    Returns:
        URL pública del avatar guardado (ej: "/static/avatars/a1b2c3d4.jpg").

    Raises:
        ValueError: Si el archivo está vacío, es demasiado grande, tiene extensión
                    no permitida o no es una imagen válida.
    """
    # Validar tamaño
    if len(contents) == 0:
        raise ValueError("Archivo vacío")
    if len(contents) > MAX_AVATAR_SIZE:
        raise ValueError("Archivo demasiado grande (máx 5MB)")

    # Validar extensión (solo extensiones de imagen permitidas)
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Formato no permitido: {ext}. Usá JPG, PNG, GIF o WebP.")

    # Verificación estructural: ¿es realmente una imagen?
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()  # verificación rápida de integridad
    except UnidentifiedImageError:
        raise ValueError("El archivo no es una imagen válida")
    except Exception as e:
        logger.error("Error al verificar imagen: %s", e)
        raise ValueError("El archivo no es una imagen válida")

    # Re-abrir tras verify() — verify() consume el stream
    img = Image.open(io.BytesIO(contents))

    # Convertir a RGB o RGBA según el modo original (elimina metadatos EXIF)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # Redimensionar si es demasiado grande (mantiene proporción)
    if img.width > MAX_DIM or img.height > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)

    # Asegurar que el directorio de avatares existe
    os.makedirs(AVATAR_DIR, exist_ok=True)

    # Guardar imagen re-encodeada con nombre aleatorio (UUID) para evitar colisiones
    # y path traversal. La extensión se fuerza al formato real.
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

    # Eliminar el avatar anterior del sistema de archivos si existía
    if old_avatar_url:
        old_path = os.path.join("app", old_avatar_url.lstrip("/"))
        if os.path.exists(old_path):
            os.remove(old_path)

    return avatar_url
