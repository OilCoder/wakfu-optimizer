"""Tests del decodificador actionId -> stat."""

from __future__ import annotations

from wakfu_opt.datos.mapeo_acciones import (
    ACTION_ELEM_VARIABLE,
    TABLA_ACCIONES,
)


def test_accion_simple_lee_params0() -> None:
    # actionId 120 (maestría elemental fija): valor en params[0].
    defn = TABLA_ACCIONES[120]
    assert defn.familia == "dom_elemental"
    assert defn.decodificar([9.0, 0.0]) == 9.0


def test_familias_recursos() -> None:
    assert TABLA_ACCIONES[31].familia == "pa"
    assert TABLA_ACCIONES[41].familia == "pm"
    assert TABLA_ACCIONES[150].familia == "crit_pct"
    assert TABLA_ACCIONES[149].familia == "dom_critico"


def test_elem_variable_usa_params0_para_valor() -> None:
    # 1068: valor en params[0]; el nº de elementos (params[2]) lo trata el normalizador.
    defn = TABLA_ACCIONES[ACTION_ELEM_VARIABLE]
    assert defn.familia == "dom_elemental"
    assert defn.decodificar([21.0, 0.0, 3.0, 0.0]) == 21.0


def test_decodificar_vacio_no_revienta() -> None:
    assert TABLA_ACCIONES[31].decodificar([]) == 0.0


def test_deboost_resta() -> None:
    # 57 = Deboost PM, 161 = Perte Portée, 168 = Perte crítico: restan de su familia.
    assert TABLA_ACCIONES[57].familia == "pm"
    assert TABLA_ACCIONES[57].decodificar([1.0, 0.0]) == -1.0
    assert TABLA_ACCIONES[161].familia == "alcance"
    assert TABLA_ACCIONES[161].decodificar([1.0]) == -1.0
    assert TABLA_ACCIONES[168].familia == "crit_pct"
    assert TABLA_ACCIONES[168].decodificar([3.0]) == -3.0
