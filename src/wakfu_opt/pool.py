"""Filtrado del pool de ítems candidatos para una franja de nivel.

Dada la lista de ítems normalizados y un perfil, deja solo los ítems que el solver
puede elegir en una franja concreta: rareza permitida, dentro del rango de nivel, con
slot optimizable, y **excluyendo los ítems fijos** (que el solver no decide).
"""

from __future__ import annotations

from wakfu_opt.dominio.modelos import Item, PerfilBuild


def filtrar_pool(items: list[Item], perfil: PerfilBuild, franja: int) -> list[Item]:
    """Devuelve los ítems candidatos para la franja `franja` (nivel tope).

    Un ítem entra si: su rareza está permitida, su nivel está en `[nivel_min_item, franja]`,
    y no es un ítem fijo ni un ítem excluido del perfil (no disponibles en el juego).
    """
    fuera = set(perfil.items_fijos) | set(perfil.items_excluidos)
    return [
        item
        for item in items
        if item.id not in fuera
        and item.rareza in perfil.rarezas_de_slot(item.slot)
        and perfil.nivel_min_item <= item.nivel <= franja
    ]


def resolver_items_fijos(items: list[Item], perfil: PerfilBuild) -> list[Item]:
    """Devuelve los `Item` normalizados correspondientes a `perfil.items_fijos`.

    Lanza ValueError si algún id fijo no existe o no es equipable, para fallar pronto
    en vez de optimizar con una base incompleta.
    """
    por_id = {item.id: item for item in items}
    resueltos: list[Item] = []
    for id_fijo in perfil.items_fijos:
        item = por_id.get(id_fijo)
        if item is None:
            raise ValueError(f"Ítem fijo {id_fijo} no existe o no es equipable.")
        resueltos.append(item)
    return resueltos
