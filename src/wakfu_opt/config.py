"""Configuración global: rutas del proyecto, CDN de Ankama y nombres de archivos de datos."""

from __future__ import annotations

from pathlib import Path

# ----------------------------------------
# Step 1 — Rutas del proyecto
# ----------------------------------------

# El paquete vive en <raíz>/src/wakfu_opt/; la raíz está 3 niveles por encima.
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
DIR_DATOS = RAIZ_PROYECTO / "data"

# ----------------------------------------
# Step 2 — Fuente de datos (CDN oficial de Ankama)
# ----------------------------------------

CDN_BASE = "https://wakfu.cdn.ankama.com/gamedata"

# Archivos de gamedata que el optimizador necesita y su rol.
ARCHIVOS_DATOS = (
    "items",  # catálogo de ítems (>15 MB)
    "actions",  # diccionario actionId -> efecto
    "states",  # estados/sublimaciones/sets (para fases futuras)
    "itemProperties",  # flags: 8=reliquia, 12=épico, 19/20=slots de gema
    "equipmentItemTypes",  # itemTypeId -> slot + bloqueos
)

# Timeout de descarga en segundos (items.json es grande).
TIMEOUT_DESCARGA = 120
