"""Bases de stats por clase y nivel (PA/PM/crit/dominios innatos).

Esta base no está en los datos del CDN: depende de la clase y de cómo el jugador
reparte sus puntos de característica. Por eso vive en una tabla en código que se
puebla con los datos que aporta el usuario.

Estructura: `clase -> (nivel_tope -> StatsItem base)`. `obtener_base` elige la entrada
de mayor nivel que no supere la franja consultada.
"""

from __future__ import annotations

import logging

from wakfu_opt.dominio.modelos import StatsItem

logger = logging.getLogger(__name__)

# clase (en minúsculas) -> {nivel_tope: base}. Se rellena con datos reales del usuario.
TABLA_BASES: dict[str, dict[int, StatsItem]] = {}


def obtener_base(clase: str, nivel: int) -> StatsItem:
    """Devuelve la base de stats de `clase` aplicable hasta `nivel`.

    Si no hay datos para la clase, devuelve una base neutra (ceros) y avisa por log:
    el optimizador funciona, pero los breakpoints de PA/PM serán los del equipo solo.
    """
    por_nivel = TABLA_BASES.get(clase.lower())
    if not por_nivel:
        logger.warning("Sin base registrada para la clase %r; uso base neutra (ceros).", clase)
        return StatsItem()

    niveles_validos = [n for n in por_nivel if n <= nivel]
    if not niveles_validos:
        logger.warning("Sin base de %r para nivel ≤ %d; uso base neutra.", clase, nivel)
        return StatsItem()

    return por_nivel[max(niveles_validos)]
