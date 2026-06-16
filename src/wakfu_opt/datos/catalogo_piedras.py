"""Catálogo de sublimaciones ("piedras"/pergaminos) extraído de los datos del CDN.

En el juego todo se llama "sublimación". Se distinguen cuatro categorías:

  - `epica`    : se engarza SOLO en ítems épicos (oficio ebanista). Aplica un estado.
  - `reliquia` : se engarza SOLO en ítems reliquia (oficio ebanista). Aplica un estado.
  - `gema`     : sublimación normal de slot de color (drop de monstruos, cualquier ítem).
  - `mejora`   : mejora de dominio base (itemTypeId 811: dominio elemental/distancia/…).

IMPORTANTE: el CDN da el *catálogo* (nombre, categoría, qué `state_id` aplica) pero
NO el efecto numérico de las épicas/reliquia. Ese efecto se codifica a mano en
`dominio/sublimaciones.py`, vinculado por `state_id`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ITEMTYPE_SUBLIMACION = 812  # épicas, reliquia y gemas de color
ITEMTYPE_MEJORA = 811  # mejoras de dominio base
ACTION_APLICA_ESTADO = 304  # equipEffect que aplica un estado; params[0] = state_id


@dataclass(frozen=True, slots=True)
class EntradaSublimacion:
    """Una sublimación del catálogo (no su efecto numérico, solo su identidad)."""

    id: int  # id del ítem-pergamino
    nombre: str
    categoria: str  # "epica" | "reliquia" | "gema" | "mejora"
    solo_relic_epic: bool  # True para épicas/reliquia (ebanista)
    state_id: int | None  # estado que aplica (None si no usa actionId 304)
    nombre_estado: str | None


def construir_catalogo(
    items_crudos: list[dict[str, Any]],
    titulos_estado: dict[int, str],
) -> list[EntradaSublimacion]:
    """Extrae todas las sublimaciones y mejoras del catálogo de ítems crudos."""
    catalogo: list[EntradaSublimacion] = []
    for crudo in items_crudos:
        item = crudo["definition"]["item"]
        type_id = item["baseParameters"]["itemTypeId"]
        if type_id not in (ITEMTYPE_SUBLIMACION, ITEMTYPE_MEJORA):
            continue

        categoria = _clasificar(type_id, item.get("sublimationParameters"))
        state_id = _state_aplicado(crudo["definition"].get("equipEffects", []))
        catalogo.append(
            EntradaSublimacion(
                id=item["id"],
                nombre=_titulo(crudo),
                categoria=categoria,
                solo_relic_epic=categoria in ("epica", "reliquia"),
                state_id=state_id,
                nombre_estado=titulos_estado.get(state_id) if state_id else None,
            )
        )
    return catalogo


def buscar(
    catalogo: list[EntradaSublimacion],
    texto: str = "",
    categoria: str | None = None,
) -> list[EntradaSublimacion]:
    """Filtra el catálogo por substring del nombre (sin distinguir mayúsculas) y categoría."""
    aguja = texto.lower()
    return [
        e
        for e in catalogo
        if (categoria is None or e.categoria == categoria) and aguja in e.nombre.lower()
    ]


def indexar_por_estado(catalogo: list[EntradaSublimacion]) -> dict[int, EntradaSublimacion]:
    """Devuelve `state_id -> entrada` para las sublimaciones que aplican un estado."""
    return {e.state_id: e for e in catalogo if e.state_id is not None}


# ----------------------------------------
# Helpers internos
# ----------------------------------------


def _clasificar(type_id: int, sublimation_params: dict[str, Any] | None) -> str:
    """Determina la categoría de la sublimación a partir de sus parámetros."""
    if type_id == ITEMTYPE_MEJORA:
        return "mejora"
    params = sublimation_params or {}
    if params.get("isEpic"):
        return "epica"
    if params.get("isRelic"):
        return "reliquia"
    return "gema"


def _state_aplicado(equip_effects: list[dict[str, Any]]) -> int | None:
    """Devuelve el state_id del primer equipEffect que aplica un estado (actionId 304)."""
    for efecto in equip_effects:
        definicion = efecto["effect"]["definition"]
        if definicion["actionId"] == ACTION_APLICA_ESTADO and definicion.get("params"):
            return int(definicion["params"][0])
    return None


def _titulo(crudo: dict[str, Any]) -> str:
    titulo = crudo.get("title", {})
    return titulo.get("es") or titulo.get("fr") or titulo.get("en") or f"#{crudo}"
