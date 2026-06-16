"""Tests de normalización de ítems contra ítems reales conocidos."""

from __future__ import annotations

from typing import Any

import pytest

from wakfu_opt.datos.mapeo_slots import InfoTipoItem, construir_mapeo
from wakfu_opt.dominio.rareza import Rareza
from wakfu_opt.dominio.slots import Slot
from wakfu_opt.normalizador import normalizar_catalogo, normalizar_item


@pytest.fixture(scope="module")
def mapeo(equipment_item_types: list[dict[str, Any]]) -> dict[int, InfoTipoItem]:
    return construir_mapeo(equipment_item_types)


def test_reliquia(items_por_id: dict[int, dict[str, Any]], mapeo: dict[int, InfoTipoItem]) -> None:
    # Gelanillo (9723): reliquia, rarity 5, slot anillo.
    item = normalizar_item(items_por_id[9723], mapeo)
    assert item is not None
    assert item.es_reliquia is True
    assert item.es_epico is False
    assert item.rareza is Rareza.RELIQUIA
    assert item.slot is Slot.ANILLO


def test_epico(items_por_id: dict[int, dict[str, Any]], mapeo: dict[int, InfoTipoItem]) -> None:
    # Cinturón fulgurante (10272): épico, rarity 7, slot cinturón.
    item = normalizar_item(items_por_id[10272], mapeo)
    assert item is not None
    assert item.es_epico is True
    assert item.rareza is Rareza.EPICO
    assert item.slot is Slot.CINTURON


def test_elem_variable_multielemento_es_general(
    items_por_id: dict[int, dict[str, Any]], mapeo: dict[int, InfoTipoItem]
) -> None:
    # Píombrero verde (2297): 1068 sobre 3 elementos -> dominio general, no mono.
    item = normalizar_item(items_por_id[2297], mapeo)
    assert item is not None
    assert item.stats.dom_elemental == 21
    assert item.stats.dom_mono_elemental == 0
    assert item.stats.elem_variable_n == 3


def test_elem_variable_monoelemento(
    items_por_id: dict[int, dict[str, Any]], mapeo: dict[int, InfoTipoItem]
) -> None:
    # Zamporona (25924): 1068 sobre 1 elemento -> cuenta como mono-elemento, no general.
    item = normalizar_item(items_por_id[25924], mapeo)
    assert item is not None
    assert item.stats.dom_mono_elemental == 160
    assert item.stats.dom_elemental == 0


def test_capa_dor_slot(
    items_por_id: dict[int, dict[str, Any]], mapeo: dict[int, InfoTipoItem]
) -> None:
    item = normalizar_item(items_por_id[16037], mapeo)
    assert item is not None
    assert item.slot is Slot.CAPA
    assert item.rareza is Rareza.MITICO  # rarity 3 = mítico


def test_deboost_pm_en_arma(
    items_por_id: dict[int, dict[str, Any]], mapeo: dict[int, InfoTipoItem]
) -> None:
    # Desencarnator (24000): espada 2 manos que da +2 PA pero -1 PM (Deboost PM, actionId 57).
    item = normalizar_item(items_por_id[24000], mapeo)
    assert item is not None
    assert item.stats.pa == 2
    assert item.stats.pm == -1  # el deboost se resta (antes se ignoraba)
    assert item.bloquea_segunda_mano is True


def test_catalogo_descarta_huerfanos(
    items: list[dict[str, Any]], mapeo: dict[int, InfoTipoItem]
) -> None:
    normalizados, descartados = normalizar_catalogo(items, mapeo)
    # Hay 8324 ítems en total; los de itemTypeId huérfano (811/812) y cosméticos se descartan.
    assert descartados > 0
    assert len(normalizados) + descartados == len(items)
    # Todos los normalizados tienen un slot válido.
    assert all(isinstance(it.slot, Slot) for it in normalizados)
