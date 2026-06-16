"""Decodificador `actionId` -> familia de stat y lectura de `params`.

Tabla declarativa: cada `actionId` relevante se asocia a una familia (un campo de
`StatsItem`) y a un decodificador que extrae el valor escalar de `params`.

Para la inmensa mayoría el valor está en `params[0]`. El caso especial es 1068
(maestría elemental en un número variable de elementos): valor en `params[0]` y
número de elementos en `params[2]` — el normalizador lo trata aparte.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

# actionId de la maestría elemental variable; el normalizador lee params[2] (nº elementos).
ACTION_ELEM_VARIABLE = 1068


@dataclass(frozen=True, slots=True)
class DefAccion:
    """Define cómo interpretar un `actionId`: a qué familia suma y cómo lee el valor."""

    familia: str
    decodificar: Callable[[list[float]], float]


def _valor_p0(params: list[float]) -> float:
    """Caso general: el valor del stat es el primer parámetro."""
    return params[0] if params else 0.0


def _valor_p0_neg(params: list[float]) -> float:
    """Pérdidas/deboosts: el valor resta de su familia."""
    return -params[0] if params else 0.0


# actionId -> DefAccion. Solo los efectos que importan para el modelo de daño/recursos.
TABLA_ACCIONES: dict[int, DefAccion] = {
    # Maestrías (alimentan el proxy de daño)
    1068: DefAccion("dom_elemental", _valor_p0),  # elemental variable (ver ACTION_ELEM_VARIABLE)
    120: DefAccion("dom_elemental", _valor_p0),  # elemental general (todos los elementos)
    # Maestrías de UN elemento específico: rinden a medias en builds multi-elemento
    122: DefAccion("dom_mono_elemental", _valor_p0),  # fuego
    123: DefAccion("dom_mono_elemental", _valor_p0),  # tierra
    124: DefAccion("dom_mono_elemental", _valor_p0),  # agua
    125: DefAccion("dom_mono_elemental", _valor_p0),  # aire
    1053: DefAccion("dom_distancia", _valor_p0),
    1052: DefAccion("dom_melee", _valor_p0),
    149: DefAccion("dom_critico", _valor_p0),  # clave para Desenlace
    1055: DefAccion("dom_berserk", _valor_p0),
    180: DefAccion("dom_espalda", _valor_p0),
    26: DefAccion("dom_cura", _valor_p0),
    # Recursos / breakpoints
    31: DefAccion("pa", _valor_p0),
    41: DefAccion("pm", _valor_p0),
    191: DefAccion("pw", _valor_p0),
    160: DefAccion("alcance", _valor_p0),
    150: DefAccion("crit_pct", _valor_p0),
    # Defensiva que se reporta pero no entra al proxy
    20: DefAccion("pv", _valor_p0),
    # Pérdidas / deboosts: restan de su familia (antes se ignoraban y sobrevaloraban el ítem)
    56: DefAccion("pa", _valor_p0_neg),
    57: DefAccion("pm", _valor_p0_neg),
    161: DefAccion("alcance", _valor_p0_neg),
    168: DefAccion("crit_pct", _valor_p0_neg),
    192: DefAccion("pw", _valor_p0_neg),
    21: DefAccion("pv", _valor_p0_neg),
    130: DefAccion("dom_elemental", _valor_p0_neg),
    132: DefAccion("dom_mono_elemental", _valor_p0_neg),
    1060: DefAccion("dom_distancia", _valor_p0_neg),
    1059: DefAccion("dom_melee", _valor_p0_neg),
    1056: DefAccion("dom_critico", _valor_p0_neg),
    1061: DefAccion("dom_berserk", _valor_p0_neg),
    181: DefAccion("dom_espalda", _valor_p0_neg),
}
