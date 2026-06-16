"""Tests del mapeo itemTypeId -> slot contra los datos reales del CDN."""

from __future__ import annotations

from typing import Any

from wakfu_opt.datos.mapeo_slots import construir_mapeo
from wakfu_opt.dominio.slots import Slot


def test_slots_conocidos(equipment_item_types: list[dict[str, Any]]) -> None:
    mapeo = construir_mapeo(equipment_item_types)
    assert mapeo[134].slot is Slot.CASCO
    assert mapeo[120].slot is Slot.AMULETO
    assert mapeo[132].slot is Slot.CAPA
    assert mapeo[136].slot is Slot.CORAZA
    assert mapeo[103].slot is Slot.ANILLO  # LEFT_HAND/RIGHT_HAND -> ANILLO


def test_arma_dos_manos_bloquea_segunda(equipment_item_types: list[dict[str, Any]]) -> None:
    mapeo = construir_mapeo(equipment_item_types)
    # Arco (117) y arma a 2 manos genérica (519) son FIRST_WEAPON y bloquean SECOND_WEAPON.
    assert mapeo[117].slot is Slot.PRIMERA_ARMA
    assert mapeo[117].bloquea_segunda_mano is True
    assert mapeo[519].bloquea_segunda_mano is True
    # Una espada a una mano (110) no bloquea.
    assert mapeo[110].slot is Slot.PRIMERA_ARMA
    assert mapeo[110].bloquea_segunda_mano is False


def test_segunda_mano(equipment_item_types: list[dict[str, Any]]) -> None:
    mapeo = construir_mapeo(equipment_item_types)
    assert mapeo[189].slot is Slot.SEGUNDA_ARMA  # Escudo
    assert mapeo[112].slot is Slot.SEGUNDA_ARMA  # Daga


def test_cosmeticos_y_huerfanos_sin_slot(equipment_item_types: list[dict[str, Any]]) -> None:
    mapeo = construir_mapeo(equipment_item_types)
    # COSTUME (647) y montura sin posición (611) no son optimizables.
    assert 647 not in mapeo
    assert 611 not in mapeo
    # itemTypeId huérfanos (no existen en equipmentItemTypes) tampoco aparecen.
    assert 811 not in mapeo
    assert 812 not in mapeo
