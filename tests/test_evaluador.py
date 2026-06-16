"""Tests del evaluador de daño y el reordenamiento de candidatas."""

from __future__ import annotations

from wakfu_opt.dominio.modelos import BuildCandidata, PerfilBuild, StatsItem
from wakfu_opt.evaluador.formula_dano import estimar_dano
from wakfu_opt.evaluador.reordenador import evaluar


def test_maestria_100_duplica_base() -> None:
    # 100 de maestría -> factor 2.0; crit 0 -> factor_crit 1.0; sin daños finales.
    dano = estimar_dano(
        StatsItem(dom_elemental=100),
        estilo="distancia",
        peso_dom_critico=1.0,
        danos_finales_pct=0.0,
        base=100.0,
    )
    assert dano == 200.0


def test_crit_40_aplica_factor_110() -> None:
    # Solo crítico: 40% -> factor_crit 1 + 0.25*0.4 = 1.10.
    dano = estimar_dano(
        StatsItem(crit_pct=40),
        estilo="distancia",
        peso_dom_critico=1.0,
        danos_finales_pct=0.0,
        base=100.0,
    )
    assert abs(dano - 110.0) < 1e-9


def test_ultimo_instante_suma_danos_finales() -> None:
    sin = estimar_dano(
        StatsItem(dom_elemental=100),
        estilo="distancia",
        peso_dom_critico=1.0,
        danos_finales_pct=0.0,
    )
    con = estimar_dano(
        StatsItem(dom_elemental=100),
        estilo="distancia",
        peso_dom_critico=1.0,
        danos_finales_pct=30.0,
    )
    assert con > sin
    assert abs(con / sin - 1.30) < 1e-9


def test_mas_maestria_mas_dano() -> None:
    bajo = estimar_dano(
        StatsItem(dom_elemental=50), estilo="distancia", peso_dom_critico=1.0, danos_finales_pct=0.0
    )
    alto = estimar_dano(
        StatsItem(dom_elemental=200),
        estilo="distancia",
        peso_dom_critico=1.0,
        danos_finales_pct=0.0,
    )
    assert alto > bajo


def test_reordena_por_crit_a_igual_proxy() -> None:
    # Dos candidatas con igual maestría pero distinto crit: gana la de más crit.
    perfil = PerfilBuild(clase="t", franjas=(200,), sublimaciones=("desenlace",))
    baja = BuildCandidata(
        franja=200,
        items=(),
        items_fijos=(),
        valor_proxy=100.0,
        totales=StatsItem(dom_elemental=100, crit_pct=40),
    )
    alta = BuildCandidata(
        franja=200,
        items=(),
        items_fijos=(),
        valor_proxy=100.0,
        totales=StatsItem(dom_elemental=100, crit_pct=60),
    )
    resultados = evaluar([baja, alta], perfil)
    assert resultados[0].crit_final_pct == 60.0
    assert resultados[0].ranking == 1
    assert resultados[1].ranking == 2
