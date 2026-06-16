"""Tests de los efectos combinados de las sublimaciones (piedras)."""

from __future__ import annotations

import pytest

from wakfu_opt.dominio.sublimaciones import PESO_DOM_CRITICO_BASE, resolver_efectos


def test_desenlace_impone_crit_y_peso() -> None:
    efectos = resolver_efectos(["desenlace"])
    assert efectos.crit_minimo_pct == 40.0
    assert efectos.peso_dom_critico == 1.0
    assert efectos.danos_finales_pct == 0.0


def test_ultimo_instante_aporta_danos_finales() -> None:
    efectos = resolver_efectos(["ultimo_instante"])
    assert efectos.crit_minimo_pct == 0.0  # no impone suelo de crítico
    assert efectos.danos_finales_pct == 30.0


def test_ambas_piedras_combinadas() -> None:
    # Caso real del usuario: Desenlace (épica) + Último Instante (reliquia) en los anillos.
    efectos = resolver_efectos(["desenlace", "ultimo_instante"])
    assert efectos.crit_minimo_pct == 40.0  # de Desenlace
    assert efectos.peso_dom_critico == 1.0  # de Desenlace
    assert efectos.danos_finales_pct == 30.0  # de Último Instante


def test_sin_piedras_usa_peso_base() -> None:
    efectos = resolver_efectos([])
    assert efectos.peso_dom_critico == PESO_DOM_CRITICO_BASE
    assert efectos.crit_minimo_pct == 0.0


def test_sublimacion_desconocida() -> None:
    with pytest.raises(ValueError, match="desconocida"):
        resolver_efectos(["no_existe"])
