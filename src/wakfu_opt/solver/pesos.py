"""Pesos del proxy lineal de daño para el solver.

El proxy aproxima el daño con una suma lineal de maestrías. CP-SAT exige coeficientes
enteros, así que todos los pesos se escalan ×100 (ESCALA) en un único sitio. Los pesos
dependen del estilo (distancia/melé) y de las piedras activas (Desenlace eleva el peso
del dominio crítico de 0.45 a 1.0).
"""

from __future__ import annotations

from wakfu_opt.dominio.modelos import Estilo, StatsItem

ESCALA = 100  # factor para convertir pesos fraccionarios en enteros

# En la rama de Suerte, 1 punto de característica da +4 dominio crítico (o +1% de crítico).
# Por eso cada 1% de crítico que aporta un ítem libera ~1 punto que se reinvierte en dominio
# crítico: el % de crítico del ítem "vale" 4 de dominio crítico (coste de oportunidad, TRD §6.2).
DOM_CRITICO_POR_PUNTO_SUERTE = 4


def peso_proxy(
    stats: StatsItem,
    estilo: Estilo,
    peso_dom_critico: float,
    factor_mono_elemento: float = 1.0,
    dom_por_crit: float = 0.0,
) -> int:
    """Devuelve el valor proxy entero (×100) de un conjunto de stats.

    Suma dominio elemental general + dominio secundario según estilo + dominio crítico
    ponderado + dominio mono-elemento ponderado por `factor_mono_elemento` (1/n_elementos).
    `dom_por_crit` valora cada punto de % de crítico del ítem como dominio elemental
    (puntos de Suerte liberados → dominio crítico → elemental con Desenlace); 0 lo desactiva.
    """
    w_dist = ESCALA if estilo in ("distancia", "mixto") else 0
    w_mel = ESCALA if estilo in ("melee", "mixto") else 0
    w_crit = round(ESCALA * peso_dom_critico)
    w_mono = round(ESCALA * factor_mono_elemento)
    w_crit_liberado = round(ESCALA * dom_por_crit)

    return (
        ESCALA * stats.dom_elemental
        + w_mono * stats.dom_mono_elemental
        + w_dist * stats.dom_distancia
        + w_mel * stats.dom_melee
        + w_crit * stats.dom_critico
        + w_crit_liberado * stats.crit_pct
    )
