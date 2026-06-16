"""Sublimaciones (piedras): el punto de partida de la optimización.

Cada piedra aporta hasta tres cosas que el resto del modelo consume:
  - una **condición de activación** -> restricción dura del solver (p. ej. crit ≥ 40%),
  - un **efecto sobre el proxy** -> modifica los pesos del dominio (p. ej. dom_crítico a peso 1.0),
  - un **efecto sobre el evaluador** -> daños finales constantes (p. ej. +30% daños infligidos).

v1 implementa Desenlace y Último Instante. La tabla `CATALOGO_SUBLIMACIONES` es extensible:
añadir una piedra es añadir una entrada con su condición y sus efectos.
"""

from __future__ import annotations

from dataclasses import dataclass

# Sin Desenlace, el dominio crítico solo cuenta en los críticos: peso ≈ 0.45 del elemental.
PESO_DOM_CRITICO_BASE = 0.45


@dataclass(frozen=True, slots=True)
class Sublimacion:
    """Una piedra: su condición de activación y su efecto sobre los pesos del daño.

    `state_id` vincula esta entrada con el catálogo extraído de los datos
    (`datos/catalogo_piedras.py`). El efecto numérico NO está en el CDN: se fija aquí.
    """

    slug: str
    nombre: str
    state_id: int  # estado que aplica la piedra (cruza con el catálogo de datos)
    crit_minimo_pct: float | None  # condición dura sobre el crítico; None si no aplica
    peso_dom_critico: float  # peso del dom_crítico en el proxy cuando la piedra está activa
    bonus_danos_finales_pct: float = 0.0  # daños infligidos constantes (factor del evaluador)


CATALOGO_SUBLIMACIONES: dict[str, Sublimacion] = {
    # Desenlace (épica, ítem 24132, state 5077): convierte el 100% del dominio crítico en
    # dominio elemental al inicio del combate si el portador tiene >= 40% de golpe crítico
    # -> el peso del dom_crítico pasa de ~0.45 a 1.0. (Verificado en el tooltip del juego.)
    "desenlace": Sublimacion(
        slug="desenlace",
        nombre="Desenlace",
        state_id=5077,
        crit_minimo_pct=40.0,
        peso_dom_critico=1.0,
    ),
    # Último Instante (reliquia, ítem 31600, state 8366): al lanzar un hechizo que cueste
    # >= 1 PW, +5% daños infligidos para ese hechizo, acumulable hasta 30%. (Tooltip del juego.)
    # No toca PA/PM/crit ni el proxy: se modela como +30% daños finales (máximo) en el evaluador.
    "ultimo_instante": Sublimacion(
        slug="ultimo_instante",
        nombre="Último Instante",
        state_id=8366,
        crit_minimo_pct=None,
        peso_dom_critico=PESO_DOM_CRITICO_BASE,
        bonus_danos_finales_pct=30.0,
    ),
}


@dataclass(frozen=True, slots=True)
class EfectosSublimacion:
    """Efectos combinados de las piedras activas, listos para el solver y el evaluador."""

    crit_minimo_pct: float  # suelo de crítico exigido (0 si ninguna piedra lo impone)
    peso_dom_critico: float  # peso del dom_crítico en el proxy
    danos_finales_pct: float  # daños infligidos constantes acumulados (factor del evaluador)


def resolver_efectos(slugs: list[str]) -> EfectosSublimacion:
    """Combina las piedras activas en sus efectos sobre restricciones, proxy y evaluador.

    El suelo de crítico es el más restrictivo entre las piedras; el peso del dom_crítico
    es el máximo que imponga alguna piedra (o el base 0.45 si ninguna lo eleva); los daños
    finales se suman (varias piedras de daño infligido son aditivas).
    """
    crit_minimo = 0.0
    peso_critico = PESO_DOM_CRITICO_BASE
    danos_finales = 0.0
    for slug in slugs:
        if slug not in CATALOGO_SUBLIMACIONES:
            raise ValueError(f"Sublimación desconocida: {slug!r}")
        sub = CATALOGO_SUBLIMACIONES[slug]
        if sub.crit_minimo_pct is not None:
            crit_minimo = max(crit_minimo, sub.crit_minimo_pct)
        peso_critico = max(peso_critico, sub.peso_dom_critico)
        danos_finales += sub.bonus_danos_finales_pct
    return EfectosSublimacion(
        crit_minimo_pct=crit_minimo,
        peso_dom_critico=peso_critico,
        danos_finales_pct=danos_finales,
    )
