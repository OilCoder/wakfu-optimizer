"""Tests del catálogo de sublimaciones contra los datos reales."""

from __future__ import annotations

from typing import Any

import pytest

from wakfu_opt.datos.catalogo_piedras import (
    buscar,
    construir_catalogo,
    indexar_por_estado,
)


@pytest.fixture(scope="module")
def titulos_estado(dir_datos: Any) -> dict[int, str]:
    from wakfu_opt.datos.cargador import cargar

    return {
        s["definition"]["id"]: s.get("title", {}).get("es", "") for s in cargar("states", dir_datos)
    }


@pytest.fixture(scope="module")
def catalogo(items: list[dict[str, Any]], titulos_estado: dict[int, str]) -> list[Any]:
    return construir_catalogo(items, titulos_estado)


def test_desenlace_es_epica(catalogo: list[Any]) -> None:
    # Desenlace: ítem 24132, épica, aplica el estado 5077.
    entrada = next(e for e in catalogo if e.id == 24132)
    assert entrada.categoria == "epica"
    assert entrada.solo_relic_epic is True
    assert entrada.state_id == 5077
    assert entrada.nombre_estado == "Desenlace"


def test_ultimo_instante_es_reliquia(catalogo: list[Any]) -> None:
    # Último instante: ítem 31600, reliquia, aplica el estado 8366.
    entrada = next(e for e in catalogo if e.id == 31600)
    assert entrada.categoria == "reliquia"
    assert entrada.solo_relic_epic is True
    assert entrada.state_id == 8366


def test_categorias_presentes(catalogo: list[Any]) -> None:
    categorias = {e.categoria for e in catalogo}
    assert {"epica", "reliquia", "gema", "mejora"} <= categorias


def test_buscar_por_nombre(catalogo: list[Any]) -> None:
    res = buscar(catalogo, "desenlace")
    assert any(e.id == 24132 for e in res)


def test_buscar_filtra_categoria(catalogo: list[Any]) -> None:
    epicas = buscar(catalogo, categoria="epica")
    assert epicas
    assert all(e.categoria == "epica" for e in epicas)


def test_indexar_por_estado(catalogo: list[Any]) -> None:
    indice = indexar_por_estado(catalogo)
    assert indice[5077].nombre_estado == "Desenlace"
    assert indice[8366].id == 31600
