"""Modelo CP-SAT: selecciona el equipo óptimo de una franja.

Maximización lexicográfica (PA -> PM -> dominio por defecto), con restricciones duras:
slots (descontando los ítems fijos), ≤1 reliquia y ≤1 épico (contando los fijos),
bloqueo de arma a dos manos, y el suelo de crítico que imponga la piedra (Desenlace: 40%).

Los ítems fijos no son variables: sus stats entran en la base y sus slots reducen la
capacidad disponible. El objetivo de dominio usa el proxy lineal escalado de `pesos.py`.

Las expresiones y variables de OR-Tools se anotan como `Any`: sus stubs mezclan
LinearExpr/IntVar/numpy y tiparlas con precisión no aporta nada al resto del modelo.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from ortools.sat.python import cp_model

from wakfu_opt.dominio.modelos import BuildCandidata, Item, PerfilBuild, StatsItem
from wakfu_opt.dominio.slots import CAPACIDAD_SLOT, Slot
from wakfu_opt.dominio.sublimaciones import resolver_efectos
from wakfu_opt.solver.pesos import DOM_CRITICO_POR_PUNTO_SUERTE, peso_proxy
from wakfu_opt.solver.solucion import construir_candidata


class BuildInfactible(Exception):
    """No existe ninguna build que cumpla las restricciones (breakpoints/crit/slots)."""


def optimizar_franja(
    pool: list[Item],
    perfil: PerfilBuild,
    franja: int,
    base_clase: StatsItem,
    items_fijos: list[Item],
    modo: str = "dano",
) -> list[BuildCandidata]:
    """Devuelve hasta `perfil.n_candidatas` builds, ordenadas por dominio decreciente.

    Según `modo`:
      - "pa" / "pm" / "alcance": maximiza ese recurso, lo fija, y luego maximiza el daño.
      - "dano": maximiza solo el daño (con crit≥40 si la piedra lo exige).
    Lanza BuildInfactible si no hay solución.
    """
    efectos = resolver_efectos(list(perfil.sublimaciones))
    base = _sumar([base_clase, *(it.stats for it in items_fijos)])

    # Valor en dominio de cada % de crítico del equipo (puntos de Suerte liberados -> dom crítico
    # -> elemental con Desenlace). 0 si la estrategia no reinvierte el crítico.
    dom_por_crit = (
        DOM_CRITICO_POR_PUNTO_SUERTE * efectos.peso_dom_critico
        if perfil.crit_libera_dominio
        else 0.0
    )

    modelo = cp_model.CpModel()
    x: list[Any] = [modelo.new_bool_var(f"x_{i}") for i in range(len(pool))]
    _añadir_restricciones(modelo, x, pool, items_fijos, base, efectos.crit_minimo_pct)

    pa_expr = base.pa + sum(x[i] * pool[i].stats.pa for i in range(len(pool)))
    pm_expr = base.pm + sum(x[i] * pool[i].stats.pm for i in range(len(pool)))
    alcance_expr = base.alcance + sum(x[i] * pool[i].stats.alcance for i in range(len(pool)))
    pw_expr = base.pw + sum(x[i] * pool[i].stats.pw for i in range(len(pool)))
    proxy_expr = sum(
        x[i]
        * peso_proxy(
            pool[i].stats,
            perfil.estilo,
            efectos.peso_dom_critico,
            perfil.factor_mono_elemento,
            dom_por_crit,
        )
        for i in range(len(pool))
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0

    # Cada modo "max recurso" maximiza ese recurso, lo fija, y luego maximiza el daño.
    # El modo "dano" maximiza el daño directamente. Así el usuario ve cada extremo y decide
    # cómo invertir sus puntos Mayor (PA/PM/alcance) según el equipo que elija.
    recurso_expr = {
        "pa": pa_expr,
        "pm": pm_expr,
        "alcance": alcance_expr,
        "pw": pw_expr,
    }.get(modo)
    if recurso_expr is not None:
        optimo = _maximizar(modelo, solver, recurso_expr)
        modelo.add(recurso_expr == optimo)

    return _enumerar_candidatas(
        modelo, solver, x, proxy_expr, pool, items_fijos, base_clase, franja, perfil.n_candidatas
    )


# ----------------------------------------
# Restricciones
# ----------------------------------------


def _añadir_restricciones(
    modelo: cp_model.CpModel,
    x: list[Any],
    pool: list[Item],
    items_fijos: list[Item],
    base: StatsItem,
    crit_minimo_pct: float,
) -> None:
    indices = range(len(pool))
    ocupados = Counter(it.slot for it in items_fijos)

    # Slots: capacidad menos lo que ocupan los ítems fijos
    for slot in Slot:
        disponible = CAPACIDAD_SLOT[slot] - ocupados.get(slot, 0)
        if disponible < 0:
            raise BuildInfactible(f"Hay más ítems fijos en {slot.value} que su capacidad.")
        idx = [i for i in indices if pool[i].slot is slot]
        if idx:
            modelo.add(sum(x[i] for i in idx) <= disponible)

    # Arma a dos manos: si se equipa, ninguna segunda mano
    segunda = [i for i in indices if pool[i].slot is Slot.SEGUNDA_ARMA]
    for i in indices:
        if pool[i].bloquea_segunda_mano and segunda:
            modelo.add(x[i] + sum(x[j] for j in segunda) <= 1)

    # ≤1 reliquia y ≤1 épico en total (los fijos ya consumen su cupo)
    fijos_reliquia = sum(it.es_reliquia for it in items_fijos)
    fijos_epico = sum(it.es_epico for it in items_fijos)
    reliquias = [i for i in indices if pool[i].es_reliquia]
    epicos = [i for i in indices if pool[i].es_epico]
    if reliquias:
        modelo.add(sum(x[i] for i in reliquias) <= 1 - fijos_reliquia)
    if epicos:
        modelo.add(sum(x[i] for i in epicos) <= 1 - fijos_epico)

    # Suelo de crítico (condición de Desenlace)
    if crit_minimo_pct > 0:
        objetivo_crit = math.ceil(crit_minimo_pct)
        modelo.add(
            base.crit_pct + sum(x[i] * pool[i].stats.crit_pct for i in indices) >= objetivo_crit
        )


# ----------------------------------------
# Maximización
# ----------------------------------------


def _maximizar(modelo: cp_model.CpModel, solver: cp_model.CpSolver, expr: Any) -> int:
    """Maximiza `expr` y devuelve su óptimo entero. Lanza BuildInfactible si no hay solución."""
    modelo.maximize(expr)
    estado = solver.solve(modelo)
    if estado not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise BuildInfactible("No hay equipo que cumpla las restricciones (PA/PM/crit/slots).")
    return int(round(solver.objective_value))


def _enumerar_candidatas(
    modelo: cp_model.CpModel,
    solver: cp_model.CpSolver,
    x: list[Any],
    proxy_expr: Any,
    pool: list[Item],
    items_fijos: list[Item],
    base_clase: StatsItem,
    franja: int,
    n: int,
) -> list[BuildCandidata]:
    """Enumera las N mejores builds por proxy con PA/PM ya fijados (no-good cuts)."""
    modelo.maximize(proxy_expr)
    candidatas: list[BuildCandidata] = []
    for iteracion in range(n):
        estado = solver.solve(modelo)
        if estado not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            # Infactible en el primer intento = no hay build posible (crit/slots).
            if iteracion == 0:
                raise BuildInfactible("No hay equipo que cumpla las restricciones (crit/slots).")
            break
        elegidos = [i for i in range(len(pool)) if solver.value(x[i])]
        if not elegidos:
            break
        candidatas.append(
            construir_candidata(
                franja,
                [pool[i] for i in elegidos],
                items_fijos,
                base_clase,
                int(round(solver.objective_value)),
            )
        )
        # No-good cut: la siguiente solución debe diferir en al menos un ítem
        modelo.add(sum(x[i] for i in elegidos) <= len(elegidos) - 1)
    return candidatas


def _sumar(stats: list[StatsItem]) -> StatsItem:
    total = StatsItem()
    for s in stats:
        total = total + s
    return total
