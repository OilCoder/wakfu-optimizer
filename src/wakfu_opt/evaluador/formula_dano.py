"""Fórmula de daño no lineal (nivel "ámbar" de la arquitectura).

Implementa la fórmula de la comunidad (ver docs/02-TRD.md §6):

    daño = base · (1 + maestrías/100) · (1 + daños_finales/100) · (1 − resist/100) · (1 + 0,25·crit)

El crítico amplía la base ×1,25 (no es un +25% de daño final). Con Desenlace activo el
dominio crítico ya se convirtió en elemental, así que cuenta a peso 1,0 en las maestrías.
La `base` es un valor de referencia constante: el daño resultante es **ordinal** (sirve
para comparar builds del mismo perfil, no como número absoluto del juego).
"""

from __future__ import annotations

from wakfu_opt.dominio.modelos import Estilo, StatsItem

BASE_REFERENCIA = 100.0


def maestria_efectiva(
    totales: StatsItem,
    estilo: Estilo,
    peso_dom_critico: float,
    factor_mono_elemento: float = 1.0,
    dom_por_crit: float = 0.0,
) -> float:
    """Maestrías que aplican al golpe: elemental general + mono-elemento ponderado +
    secundaria del estilo + crítica ponderada + crítico-como-dominio (puntos de Suerte)."""
    maestria = float(totales.dom_elemental)
    maestria += factor_mono_elemento * totales.dom_mono_elemental
    if estilo in ("distancia", "mixto"):
        maestria += totales.dom_distancia
    if estilo in ("melee", "mixto"):
        maestria += totales.dom_melee
    maestria += peso_dom_critico * totales.dom_critico
    maestria += dom_por_crit * totales.crit_pct
    return maestria


def estimar_dano(
    totales: StatsItem,
    *,
    estilo: Estilo,
    peso_dom_critico: float,
    danos_finales_pct: float,
    factor_mono_elemento: float = 1.0,
    dom_por_crit: float = 0.0,
    dominio_extra: float = 0.0,
    crit_factor_pct: float | None = None,
    resist_pct: float = 0.0,
    base: float = BASE_REFERENCIA,
) -> float:
    """Daño relativo de una build según la fórmula multiplicativa de Wakfu.

    `crit_factor_pct` fija el crítico usado en el factor crítico (cuando se mantiene en el
    umbral y el exceso se convierte en dominio); si es None usa el crítico real de la build.
    `dominio_extra` suma dominio no atado a un campo de StatsItem (p. ej. encantamiento).
    """
    maestria = maestria_efectiva(
        totales, estilo, peso_dom_critico, factor_mono_elemento, dom_por_crit
    )
    maestria += dominio_extra
    crit_efectivo = totales.crit_pct if crit_factor_pct is None else crit_factor_pct
    crit_frac = min(crit_efectivo / 100.0, 1.0)

    factor_maestria = 1 + maestria / 100.0
    factor_finales = 1 + danos_finales_pct / 100.0
    factor_resist = 1 - resist_pct / 100.0
    factor_crit = 1 + 0.25 * crit_frac

    return base * factor_maestria * factor_finales * factor_resist * factor_crit
