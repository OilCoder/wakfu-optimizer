"""Construcción de `BuildCandidata` a partir de una asignación del solver."""

from __future__ import annotations

from functools import reduce

from wakfu_opt.dominio.modelos import BuildCandidata, Item, StatsItem
from wakfu_opt.solver.pesos import ESCALA


def construir_candidata(
    franja: int,
    seleccionados: list[Item],
    items_fijos: list[Item],
    base_clase: StatsItem,
    valor_proxy_escalado: int,
) -> BuildCandidata:
    """Ensambla una candidata: totales = base de clase + ítems fijos + seleccionados."""
    todos = [base_clase, *(it.stats for it in items_fijos), *(it.stats for it in seleccionados)]
    totales = reduce(lambda a, b: a + b, todos, StatsItem())
    return BuildCandidata(
        franja=franja,
        items=tuple(seleccionados),
        items_fijos=tuple(items_fijos),
        valor_proxy=valor_proxy_escalado / ESCALA,
        totales=totales,
    )
