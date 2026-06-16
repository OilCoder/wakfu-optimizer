"""Fixtures compartidas: carga los datos de gamedata una sola vez por sesión de tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from wakfu_opt.datos.cargador import cargar, localizar_datos


@pytest.fixture(scope="session")
def dir_datos() -> Path:
    """Directorio de la versión de datos cacheada (sin tocar la red si ya existe)."""
    return localizar_datos()


@pytest.fixture(scope="session")
def items(dir_datos: Path) -> list[dict[str, Any]]:
    """Catálogo completo de ítems (lista cruda de items.json)."""
    return cargar("items", dir_datos)


@pytest.fixture(scope="session")
def equipment_item_types(dir_datos: Path) -> list[dict[str, Any]]:
    """Tipos de equipo crudos (equipmentItemTypes.json)."""
    return cargar("equipmentItemTypes", dir_datos)


@pytest.fixture(scope="session")
def items_por_id(items: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Índice id -> ítem crudo para buscar ítems concretos en los tests."""
    return {it["definition"]["item"]["id"]: it for it in items}
