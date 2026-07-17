import io

from PIL import Image

from app.errores import ErrorAPI

# Límite normativo y formatos admitidos (decisión clarify 2026-07-16, spec v10 Anexo B §5).
TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024
FORMATOS_PERMITIDOS = {"JPEG", "PNG"}
LADO_MAXIMO_PERFIL_PX = 512


def validar_y_leer_imagen(contenido: bytes) -> Image.Image:
    """Valida tamaño y tipo real del fichero (no la extensión): spec v10 EA-013.

    `UnidentifiedImageError` (formato no reconocido) es una subclase de `OSError`;
    capturamos `OSError` en general para cubrir también cabeceras válidas con cuerpo
    corrupto, que solo fallan al decodificar en `.load()`.
    """
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise ErrorAPI(413, "imagen_demasiado_grande", "La imagen supera el límite de 5 MB.")
    try:
        imagen = Image.open(io.BytesIO(contenido))
        imagen.load()
    except OSError as exc:
        raise ErrorAPI(
            400, "formato_invalido", "El fichero no es una imagen JPEG o PNG válida."
        ) from exc
    if imagen.format not in FORMATOS_PERMITIDOS:
        raise ErrorAPI(400, "formato_invalido", "Solo se admiten imágenes JPEG o PNG.")
    return imagen


def redimensionar_para_perfil(imagen: Image.Image) -> Image.Image:
    """Lado mayor a 512 px máx., preservando la relación de aspecto, sin recorte."""
    imagen = imagen.convert("RGB")
    imagen.thumbnail((LADO_MAXIMO_PERFIL_PX, LADO_MAXIMO_PERFIL_PX))
    return imagen
