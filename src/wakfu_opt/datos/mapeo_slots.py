"""Mapeo `itemTypeId` -> slot y reglas de arma, derivado de `equipmentItemTypes.json`.

El mapeo se construye dinámicamente desde los datos del CDN: si Ankama añade tipos,
no hay que tocar código. Los tipos cuyas posiciones no son optimizables (cosméticos)
o que no aparecen en el JSON (huérfanos como 811/812) devuelven slot `None`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from wakfu_opt.dominio.slots import POSICION_A_SLOT, Slot

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InfoTipoItem:
    """Slot resuelto y reglas de un `itemTypeId`."""

    slot: Slot
    bloquea_segunda_mano: bool


def construir_mapeo(equipment_item_types: list[dict[str, Any]]) -> dict[int, InfoTipoItem]:
    """Devuelve `itemTypeId -> InfoTipoItem` para los tipos con slot optimizable.

    Los tipos cosméticos (COSTUME, MONTURA) o sin posición conocida se omiten del mapa:
    un `itemTypeId` ausente del resultado significa "no equipable por el optimizador".
    """
    mapeo: dict[int, InfoTipoItem] = {}
    for tipo in equipment_item_types:
        definicion = tipo["definition"]
        type_id = definicion["id"]
        posiciones = definicion.get("equipmentPositions", [])

        # ✅ Resolver el slot a partir de la primera posición reconocida
        slot = _resolver_slot(posiciones)
        if slot is None:
            continue

        bloquea = "SECOND_WEAPON" in definicion.get("equipmentDisabledPositions", [])
        mapeo[type_id] = InfoTipoItem(slot=slot, bloquea_segunda_mano=bloquea)

    return mapeo


def _resolver_slot(posiciones: list[str]) -> Slot | None:
    """Devuelve el Slot de la primera posición reconocida, o None si ninguna lo es."""
    for posicion in posiciones:
        slot = POSICION_A_SLOT.get(posicion)
        if slot is not None:
            return slot
    return None
