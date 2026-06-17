"""Reordena las candidatas del solver aplicando la fórmula de daño real.

El solver entrega N builds óptimas en el proxy lineal (todas con el mismo PA/PM máximo).
El evaluador aplica la fórmula no lineal y las reordena por daño estimado, corrigiendo
lo que el proxy no captura (el factor crítico real y el peso del dominio crítico).
"""

from __future__ import annotations

from dataclasses import replace

from wakfu_opt.dominio.modelos import BuildCandidata, PerfilBuild, ResultadoBuild
from wakfu_opt.dominio.sublimaciones import resolver_efectos
from wakfu_opt.evaluador.formula_dano import estimar_dano
from wakfu_opt.solver.pesos import DOM_CRITICO_POR_PUNTO_SUERTE


def evaluar(candidatas: list[BuildCandidata], perfil: PerfilBuild) -> list[ResultadoBuild]:
    """Convierte candidatas en resultados ordenados por daño estimado decreciente."""
    efectos = resolver_efectos(list(perfil.sublimaciones))

    # Si el crítico se reinvierte en dominio, su exceso vale dominio y el factor crítico se
    # mantiene en el umbral de la piedra (no sube con el crítico del equipo).
    dom_por_crit = (
        DOM_CRITICO_POR_PUNTO_SUERTE * efectos.peso_dom_critico
        if perfil.crit_libera_dominio
        else 0.0
    )
    crit_factor_pct = efectos.crit_minimo_pct if perfil.crit_libera_dominio else None

    def encantamiento(c: BuildCandidata) -> float:
        return perfil.encantamiento_por_nivel * sum(it.nivel for it in (*c.items, *c.items_fijos))

    def dano_total(c: BuildCandidata) -> float:
        # Daño por golpe × PA total: el daño del turno es proporcional al PA (más golpes).
        por_golpe = estimar_dano(
            c.totales,
            estilo=perfil.estilo,
            peso_dom_critico=efectos.peso_dom_critico,
            danos_finales_pct=efectos.danos_finales_pct,
            factor_mono_elemento=perfil.factor_mono_elemento,
            dom_por_crit=dom_por_crit,
            dominio_extra=encantamiento(c),
            crit_factor_pct=crit_factor_pct,
        )
        return por_golpe * max(c.totales.pa, 1)

    resultados = [
        ResultadoBuild(
            franja=c.franja,
            items=c.items,
            items_fijos=c.items_fijos,
            dano_estimado=dano_total(c),
            valor_proxy=c.valor_proxy,
            crit_final_pct=float(c.totales.crit_pct),
            totales=c.totales,
            ranking=0,
        )
        for c in candidatas
    ]

    resultados.sort(key=lambda r: r.dano_estimado, reverse=True)
    return [replace(r, ranking=i + 1) for i, r in enumerate(resultados)]
