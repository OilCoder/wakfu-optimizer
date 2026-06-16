"""Test de integración end-to-end con los datos reales del CDN (lento)."""

from __future__ import annotations

from typing import Any

import pytest

from wakfu_opt.datos.mapeo_slots import construir_mapeo
from wakfu_opt.dominio.modelos import PerfilBuild, StatsItem
from wakfu_opt.dominio.rareza import Rareza
from wakfu_opt.dominio.slots import Slot
from wakfu_opt.evaluador.reordenador import evaluar
from wakfu_opt.normalizador import normalizar_catalogo
from wakfu_opt.pool import filtrar_pool, resolver_items_fijos
from wakfu_opt.solver.modelo_cpsat import optimizar_franja


@pytest.mark.slow
def test_optimizacion_real_franja_200(
    items: list[dict[str, Any]], equipment_item_types: list[dict[str, Any]]
) -> None:
    mapeo = construir_mapeo(equipment_item_types)
    catalogo, _ = normalizar_catalogo(items, mapeo)

    # Caso real del usuario: anillos fijos (reliquia + épico), Desenlace + Último Instante.
    perfil = PerfilBuild(
        clase="ejemplo",
        franjas=(200,),
        items_fijos=(9723, 21692),
        sublimaciones=("desenlace", "ultimo_instante"),
        rarezas_permitidas=frozenset({Rareza.MITICO}),
        estilo="distancia",
        n_candidatas=3,
    )
    base = StatsItem(crit_pct=40)  # crítico aportado por características
    items_fijos = resolver_items_fijos(catalogo, perfil)
    pool = filtrar_pool(catalogo, perfil, 200)

    candidatas = optimizar_franja(pool, perfil, 200, base, items_fijos)
    resultados = evaluar(candidatas, perfil)
    mejor = resultados[0]

    # La build debe ser coherente con todas las restricciones:
    equipo = [*mejor.items, *mejor.items_fijos]
    # (a) no repite slots por encima de su capacidad
    anillos = sum(1 for it in equipo if it.slot is Slot.ANILLO)
    assert anillos <= 2
    # (b) lleva exactamente los dos anillos fijos
    assert {it.id for it in mejor.items_fijos} == {9723, 21692}
    # (c) ≤1 reliquia y ≤1 épico en total
    assert sum(it.es_reliquia for it in equipo) <= 1
    assert sum(it.es_epico for it in equipo) <= 1
    # (d) cumple el suelo de crítico de Desenlace
    assert mejor.crit_final_pct >= 40
    # (e) el resto del equipo (no fijo) es solo mítico
    assert all(it.rareza is Rareza.MITICO for it in mejor.items)
    # (f) ningún ítem supera la franja
    assert all(it.nivel <= 200 for it in equipo)
