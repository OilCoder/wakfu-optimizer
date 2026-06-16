"""Descarga, caché y carga de los datos de gamedata del CDN de Ankama.

La versión activa se lee dinámicamente de `config.json` del CDN (no se hardcodea).
Los archivos se cachean en `data/{version}/` para no rebajar >15 MB en cada ejecución.
Si no hay red pero existe `data/config.json` local, se usa esa versión (modo offline).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from wakfu_opt.config import (
    ARCHIVOS_DATOS,
    CDN_BASE,
    DIR_DATOS,
    TIMEOUT_DESCARGA,
)

logger = logging.getLogger(__name__)


# ----------------------------------------
# Step 1 — Resolver la versión activa
# ----------------------------------------


def resolver_version() -> str:
    """Devuelve la versión de gamedata activa.

    Intenta leerla del CDN (`config.json`); si la red falla, recurre a la versión
    cacheada en `data/config.json`. Lanza RuntimeError si no hay ninguna disponible.
    """
    try:
        resp = requests.get(f"{CDN_BASE}/config.json", timeout=TIMEOUT_DESCARGA)
        resp.raise_for_status()
        version = str(resp.json()["version"])
        logger.info("Versión activa en el CDN: %s", version)
        return version
    except requests.RequestException as exc:
        cache = DIR_DATOS / "config.json"
        if cache.exists():
            version = str(json.loads(cache.read_text())["version"])
            logger.warning("Sin red (%s); uso versión cacheada %s", exc, version)
            return version
        raise RuntimeError(
            "No se pudo resolver la versión: sin red y sin data/config.json en caché."
        ) from exc


# ----------------------------------------
# Step 2 — Asegurar que los datos están en disco
# ----------------------------------------


def asegurar_datos(version: str | None = None, *, forzar: bool = False) -> Path:
    """Garantiza que los 5 archivos de gamedata estén cacheados en `data/{version}/`.

    Descarga los que falten (o todos si `forzar`). Devuelve el directorio de la versión.
    """
    if version is None:
        version = resolver_version()

    dir_version = DIR_DATOS / version
    dir_version.mkdir(parents=True, exist_ok=True)

    # 🔄 Descargar cada archivo que falte (o todos si se fuerza)
    for nombre in ARCHIVOS_DATOS:
        destino = dir_version / f"{nombre}.json"
        if destino.exists() and not forzar:
            continue
        _descargar_archivo(version, nombre, destino)

    # 💾 Registrar la versión activa en data/config.json
    (DIR_DATOS / "config.json").write_text(json.dumps({"version": version}, indent=2))
    return dir_version


def _descargar_archivo(version: str, nombre: str, destino: Path) -> None:
    """Descarga `{nombre}.json` de la versión dada del CDN y lo escribe en `destino`."""
    url = f"{CDN_BASE}/{version}/{nombre}.json"
    logger.info("Descargando %s ...", url)
    resp = requests.get(url, timeout=TIMEOUT_DESCARGA)
    resp.raise_for_status()
    destino.write_bytes(resp.content)


# ----------------------------------------
# Step 3 — Cargar JSON desde la caché
# ----------------------------------------


def cargar(nombre: str, dir_version: Path) -> Any:
    """Carga un archivo de gamedata cacheado (`{nombre}.json`) y devuelve su contenido."""
    if nombre not in ARCHIVOS_DATOS:
        raise ValueError(f"Archivo de datos desconocido: {nombre!r}")
    ruta = dir_version / f"{nombre}.json"
    if not ruta.exists():
        raise FileNotFoundError(f"No está cacheado {ruta}; ejecuta la descarga primero.")
    with ruta.open(encoding="utf-8") as fh:
        return json.load(fh)


def cargar_todo(dir_version: Path) -> dict[str, Any]:
    """Carga los 5 archivos de gamedata y los devuelve indexados por nombre."""
    return {nombre: cargar(nombre, dir_version) for nombre in ARCHIVOS_DATOS}


def localizar_datos(dir_datos: Path | None = None) -> Path:
    """Devuelve el directorio de datos a usar, prefiriendo la caché local (sin red).

    Si `dir_datos` se pasa explícitamente, se usa tal cual. Si no, se usa la versión
    de `data/config.json` cuando todos sus archivos están cacheados; en último caso
    se recurre a `asegurar_datos` (que sí puede descargar).
    """
    if dir_datos is not None:
        return dir_datos

    cache_cfg = DIR_DATOS / "config.json"
    if cache_cfg.exists():
        version = str(json.loads(cache_cfg.read_text())["version"])
        dir_version = DIR_DATOS / version
        if all((dir_version / f"{n}.json").exists() for n in ARCHIVOS_DATOS):
            return dir_version

    return asegurar_datos()
