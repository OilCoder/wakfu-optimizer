"""Tests del filtrado del pool por rareza, nivel y exclusión de ítems fijos."""

from __future__ import annotations

from typing import Any

import pytest

from wakfu_opt.datos.mapeo_slots import construir_mapeo
from wakfu_opt.dominio.modelos import PerfilBuild
from wakfu_opt.dominio.rareza import Rareza
from wakfu_opt.dominio.slots import Slot
from wakfu_opt.normalizador import normalizar_catalogo
from wakfu_opt.pool import filtrar_pool, resolver_items_fijos


@pytest.fixture(scope="module")
def catalogo(items: list[dict[str, Any]], equipment_item_types: list[dict[str, Any]]) -> list[Any]:
    mapeo = construir_mapeo(equipment_item_types)
    normalizados, _ = normalizar_catalogo(items, mapeo)
    return normalizados


def test_solo_miticos_y_franja(catalogo: list[Any]) -> None:
    perfil = PerfilBuild(clase="sram", franjas=(80,), rarezas_permitidas=frozenset({Rareza.MITICO}))
    pool = filtrar_pool(catalogo, perfil, franja=80)
    assert pool, "el pool no debería estar vacío"
    assert all(it.rareza is Rareza.MITICO for it in pool)
    assert all(it.nivel <= 80 for it in pool)


def test_excluye_items_fijos(catalogo: list[Any]) -> None:
    # Tomamos un ítem real del pool y lo fijamos: no debe volver a aparecer como candidato.
    perfil_base = PerfilBuild(clase="sram", franjas=(200,))
    pool_completo = filtrar_pool(catalogo, perfil_base, franja=200)
    fijo = pool_completo[0]
    perfil = PerfilBuild(clase="sram", franjas=(200,), items_fijos=(fijo.id,))
    pool = filtrar_pool(catalogo, perfil, franja=200)
    assert all(it.id != fijo.id for it in pool)
    assert len(pool) == len(pool_completo) - 1


def test_rareza_por_slot_permite_legendario(catalogo: list[Any]) -> None:
    # General solo mítico, pero la segunda mano admite también legendario (rarity 4).
    perfil = PerfilBuild(
        clase="sram",
        franjas=(200,),
        rarezas_permitidas=frozenset({Rareza.MITICO}),
        rarezas_por_slot={Slot.SEGUNDA_ARMA: frozenset({Rareza.MITICO, Rareza.LEGENDARIO})},
    )
    pool = filtrar_pool(catalogo, perfil, franja=200)
    segundas = [it for it in pool if it.slot is Slot.SEGUNDA_ARMA]
    otros = [it for it in pool if it.slot is not Slot.SEGUNDA_ARMA]
    # En segunda mano hay legendarios; en el resto, solo míticos.
    assert any(it.rareza is Rareza.LEGENDARIO for it in segundas)
    assert all(it.rareza is Rareza.MITICO for it in otros)


def test_excluye_items_vetados(catalogo: list[Any]) -> None:
    perfil_base = PerfilBuild(clase="sram", franjas=(200,))
    pool_completo = filtrar_pool(catalogo, perfil_base, franja=200)
    vetado = pool_completo[0]
    perfil = PerfilBuild(clase="sram", franjas=(200,), items_excluidos=(vetado.id,))
    pool = filtrar_pool(catalogo, perfil, franja=200)
    assert all(it.id != vetado.id for it in pool)


def test_resolver_items_fijos_ok(catalogo: list[Any]) -> None:
    item = catalogo[0]
    perfil = PerfilBuild(clase="sram", franjas=(200,), items_fijos=(item.id,))
    fijos = resolver_items_fijos(catalogo, perfil)
    assert len(fijos) == 1
    assert fijos[0].id == item.id


def test_resolver_items_fijos_inexistente(catalogo: list[Any]) -> None:
    perfil = PerfilBuild(clase="sram", franjas=(200,), items_fijos=(999_999_999,))
    with pytest.raises(ValueError, match="no existe"):
        resolver_items_fijos(catalogo, perfil)
