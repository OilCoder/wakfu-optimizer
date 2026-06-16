"""Rareza de los ítems, fijada empíricamente sobre los datos del CDN.

El campo `baseParameters.rarity` es un entero 0–7. Valores verificados:
  - 3 = mítico, 4 = legendario  → confirmado correlacionando ítems del juego (mismo ítem
    en dos rarezas: Cabellera de tejaroxor mítica = rarity 3, Hombreras-dragón legendaria
    = rarity 4) con sus stats en los datos.
  - 5 = reliquia  → todos los ítems con property 8 (`[Relique]`) son rarity 5.
  - 7 = épico     → todos los ítems con property 12 son rarity 7.
Los valores 0/1/2/6 son la mejor interpretación (no críticos para el filtro de míticos).
"""

from __future__ import annotations

from enum import IntEnum


class Rareza(IntEnum):
    """Rareza de un ítem (valor = campo `rarity` del CDN)."""

    SIN_RAREZA = 0
    COMUN = 1
    INUSUAL = 2
    MITICO = 3
    LEGENDARIO = 4
    RELIQUIA = 5
    RECUERDO = 6  # ítems de nivel 200 (Zinit y similares)
    EPICO = 7


# Nombre -> Rareza, para parsear perfiles TOML (acepta minúsculas y sin acentos).
NOMBRE_A_RAREZA: dict[str, Rareza] = {
    "sin_rareza": Rareza.SIN_RAREZA,
    "comun": Rareza.COMUN,
    "inusual": Rareza.INUSUAL,
    "mitico": Rareza.MITICO,
    "legendario": Rareza.LEGENDARIO,
    "reliquia": Rareza.RELIQUIA,
    "recuerdo": Rareza.RECUERDO,
    "epico": Rareza.EPICO,
}
