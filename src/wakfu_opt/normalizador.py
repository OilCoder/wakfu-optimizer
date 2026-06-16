"""Normaliza ítems crudos del CDN a la estructura `Item` del dominio.

Lee `definition.item` (id, nivel, rareza, properties, itemTypeId) y los efectos en
`definition.equipEffects[].effect.definition.{actionId, params}`, traduciéndolos a
familias de stats con `TABLA_ACCIONES`. Los ítems sin slot optimizable (cosméticos o
itemTypeId huérfanos como 811/812) se descartan.
"""

from __future__ import annotations

import logging
from typing import Any

from wakfu_opt.datos.mapeo_acciones import ACTION_ELEM_VARIABLE, TABLA_ACCIONES
from wakfu_opt.datos.mapeo_slots import InfoTipoItem
from wakfu_opt.dominio.modelos import Item, StatsItem
from wakfu_opt.dominio.rareza import Rareza

logger = logging.getLogger(__name__)

# Flags de itemProperties.
_PROP_RELIQUIA = 8
_PROP_EPICO = 12


def normalizar_item(crudo: dict[str, Any], mapeo_slots: dict[int, InfoTipoItem]) -> Item | None:
    """Convierte un ítem crudo en `Item`, o devuelve None si no es equipable."""
    definicion = crudo["definition"]
    item = definicion["item"]
    base = item["baseParameters"]

    # ✅ Resolver el slot; si el tipo no es optimizable, descartar
    info = mapeo_slots.get(base["itemTypeId"])
    if info is None:
        return None

    propiedades = item.get("properties", [])
    stats = _extraer_stats(definicion.get("equipEffects", []))

    return Item(
        id=item["id"],
        nombre=_titulo(crudo),
        nivel=item["level"],
        slot=info.slot,
        item_type_id=base["itemTypeId"],
        rareza=Rareza(base["rarity"]),
        es_reliquia=_PROP_RELIQUIA in propiedades,
        es_epico=_PROP_EPICO in propiedades,
        bloquea_segunda_mano=info.bloquea_segunda_mano,
        set_id=base.get("itemSetId", 0),
        stats=stats,
    )


def normalizar_catalogo(
    items_crudos: list[dict[str, Any]],
    mapeo_slots: dict[int, InfoTipoItem],
) -> tuple[list[Item], int]:
    """Normaliza todo el catálogo. Devuelve (ítems válidos, nº descartados sin slot)."""
    items: list[Item] = []
    descartados = 0
    for crudo in items_crudos:
        item = normalizar_item(crudo, mapeo_slots)
        if item is None:
            descartados += 1
        else:
            items.append(item)
    logger.info("Normalizados %d ítems; descartados %d sin slot.", len(items), descartados)
    return items, descartados


# ----------------------------------------
# Helpers internos
# ----------------------------------------


def _titulo(crudo: dict[str, Any]) -> str:
    """Nombre del ítem en español, con fallback a otros idiomas."""
    titulo = crudo.get("title", {})
    return titulo.get("es") or titulo.get("fr") or titulo.get("en") or f"#{crudo}"


def _extraer_stats(equip_effects: list[dict[str, Any]]) -> StatsItem:
    """Acumula los efectos de equipo en un StatsItem (familias + otros + elem_variable_n)."""
    acum: dict[str, int] = {}
    otros: list[tuple[int, float]] = []
    elem_variable_n = 0

    for efecto in equip_effects:
        definicion = efecto["effect"]["definition"]
        action_id = definicion["actionId"]
        params = definicion.get("params", [])

        # 🔄 El 1068 (elemental variable) declara en params[2] sobre cuántos elementos aplica.
        # Si cubre 1 elemento cuenta como mono-elemento; si cubre 2+ es general.
        if action_id == ACTION_ELEM_VARIABLE:
            valor = round(params[0]) if params else 0
            n_elem = int(params[2]) if len(params) > 2 else 1
            if n_elem <= 1:
                acum["dom_mono_elemental"] = acum.get("dom_mono_elemental", 0) + valor
            else:
                acum["dom_elemental"] = acum.get("dom_elemental", 0) + valor
                elem_variable_n = max(elem_variable_n, n_elem)
            continue

        defn = TABLA_ACCIONES.get(action_id)
        if defn is None:
            otros.append((action_id, params[0] if params else 0.0))
            continue

        acum[defn.familia] = acum.get(defn.familia, 0) + round(defn.decodificar(params))

    return StatsItem(**acum, otros=tuple(otros), elem_variable_n=elem_variable_n)
