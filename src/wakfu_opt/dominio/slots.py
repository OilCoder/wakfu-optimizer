"""Slots de equipo y su capacidad.

Mapea las `equipmentPositions` del CDN de Ankama a los slots que el optimizador
considera. Los cosméticos (COSTUME, MONTURA) quedan fuera: no aportan al daño en v1.
"""

from __future__ import annotations

from enum import Enum


class Slot(Enum):
    """Slot de equipo optimizable."""

    CASCO = "CASCO"
    AMULETO = "AMULETO"
    CAPA = "CAPA"
    CORAZA = "CORAZA"
    CINTURON = "CINTURON"
    BOTAS = "BOTAS"
    HOMBRERAS = "HOMBRERAS"
    PRIMERA_ARMA = "PRIMERA_ARMA"
    SEGUNDA_ARMA = "SEGUNDA_ARMA"
    ANILLO = "ANILLO"
    MASCOTA = "MASCOTA"
    ACCESORIO = "ACCESORIO"


# Posición del CDN -> Slot del optimizador. Las no listadas (COSTUME, MOUNT) se ignoran.
POSICION_A_SLOT: dict[str, Slot] = {
    "HEAD": Slot.CASCO,
    "NECK": Slot.AMULETO,
    "BACK": Slot.CAPA,
    "CHEST": Slot.CORAZA,
    "BELT": Slot.CINTURON,
    "LEGS": Slot.BOTAS,
    "SHOULDERS": Slot.HOMBRERAS,
    "FIRST_WEAPON": Slot.PRIMERA_ARMA,
    "SECOND_WEAPON": Slot.SEGUNDA_ARMA,
    "LEFT_HAND": Slot.ANILLO,
    "RIGHT_HAND": Slot.ANILLO,
    "PET": Slot.MASCOTA,
    "ACCESSORY": Slot.ACCESORIO,
}

# Cuántas piezas caben por slot. Solo el anillo admite 2.
CAPACIDAD_SLOT: dict[Slot, int] = {slot: 1 for slot in Slot}
CAPACIDAD_SLOT[Slot.ANILLO] = 2

# Nombre (minúsculas) -> Slot, para parsear perfiles TOML.
NOMBRE_A_SLOT: dict[str, Slot] = {slot.value.lower(): slot for slot in Slot}
