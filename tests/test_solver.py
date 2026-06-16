"""Tests del solver CP-SAT con pools sintéticos pequeños y controlados."""

from __future__ import annotations

import pytest

from wakfu_opt.dominio.modelos import Item, PerfilBuild, StatsItem
from wakfu_opt.dominio.rareza import Rareza
from wakfu_opt.dominio.slots import Slot
from wakfu_opt.solver.modelo_cpsat import BuildInfactible, optimizar_franja


def hacer_item(
    id: int,
    slot: Slot,
    *,
    pa: int = 0,
    pm: int = 0,
    crit: int = 0,
    elem: int = 0,
    dist: int = 0,
    alcance: int = 0,
    reliquia: bool = False,
    epico: bool = False,
    dosmanos: bool = False,
) -> Item:
    return Item(
        id=id,
        nombre=f"item{id}",
        nivel=1,
        slot=slot,
        item_type_id=0,
        rareza=Rareza.MITICO,
        es_reliquia=reliquia,
        es_epico=epico,
        bloquea_segunda_mano=dosmanos,
        set_id=0,
        stats=StatsItem(
            dom_elemental=elem, dom_distancia=dist, pa=pa, pm=pm, crit_pct=crit, alcance=alcance
        ),
    )


def _perfil(**kw: object) -> PerfilBuild:
    # Sin piedras por defecto en los tests, para aislar cada restricción.
    base = {"clase": "test", "franjas": (200,), "sublimaciones": ()}
    base.update(kw)
    return PerfilBuild(**base)  # type: ignore[arg-type]


def _ids(candidata: object) -> set[int]:
    return {it.id for it in candidata.items}  # type: ignore[attr-defined]


def test_respeta_capacidad_de_anillos() -> None:
    pool = [hacer_item(i, Slot.ANILLO, elem=10) for i in range(4)]
    [mejor] = optimizar_franja(pool, _perfil(n_candidatas=1), 200, StatsItem(), [])
    assert len(mejor.items) == 2  # ANILLO admite 2


def test_un_solo_casco() -> None:
    pool = [hacer_item(1, Slot.CASCO, elem=10), hacer_item(2, Slot.CASCO, elem=20)]
    [mejor] = optimizar_franja(pool, _perfil(n_candidatas=1), 200, StatsItem(), [])
    assert _ids(mejor) == {2}  # el de más dominio


def test_modo_max_pa_prioriza_pa_sobre_dominio() -> None:
    # Un casco da más PA pero menos dominio; en modo "pa" debe ganar el de más PA.
    pool = [hacer_item(1, Slot.CASCO, pa=2, elem=0), hacer_item(2, Slot.CASCO, pa=0, elem=100)]
    [mejor] = optimizar_franja(pool, _perfil(n_candidatas=1), 200, StatsItem(), [], modo="pa")
    assert _ids(mejor) == {1}
    assert mejor.totales.pa == 2


def test_modo_recursos_cascada_pa_pm_alcance() -> None:
    # Cascada PA→PM→alcance→daño: con PA máximo fijo, desempata por PM, luego alcance.
    pool = [
        hacer_item(1, Slot.CASCO, pa=1, pm=0),
        hacer_item(2, Slot.CASCO, pa=1, pm=1),  # mismo PA, más PM -> gana
    ]
    [mejor] = optimizar_franja(pool, _perfil(n_candidatas=1), 200, StatsItem(), [], modo="recursos")
    assert _ids(mejor) == {2}
    assert mejor.totales.pa == 1 and mejor.totales.pm == 1


def test_modo_dano_prioriza_dominio_sobre_pa() -> None:
    # Los mismos cascos: en modo "dano" gana el de más dominio aunque dé menos PA.
    pool = [hacer_item(1, Slot.CASCO, pa=2, elem=0), hacer_item(2, Slot.CASCO, pa=0, elem=100)]
    [mejor] = optimizar_franja(pool, _perfil(n_candidatas=1), 200, StatsItem(), [], modo="dano")
    assert _ids(mejor) == {2}


def test_max_una_reliquia() -> None:
    pool = [hacer_item(i, Slot.ANILLO, elem=10, reliquia=True) for i in range(3)]
    [mejor] = optimizar_franja(pool, _perfil(n_candidatas=1), 200, StatsItem(), [])
    assert sum(it.es_reliquia for it in mejor.items) <= 1


def test_arma_dos_manos_bloquea_segunda() -> None:
    pool = [
        hacer_item(1, Slot.PRIMERA_ARMA, elem=10, dosmanos=True),
        hacer_item(2, Slot.SEGUNDA_ARMA, elem=10),
    ]
    [mejor] = optimizar_franja(pool, _perfil(n_candidatas=1), 200, StatsItem(), [])
    tiene_2m = any(it.bloquea_segunda_mano for it in mejor.items)
    tiene_segunda = any(it.slot is Slot.SEGUNDA_ARMA for it in mejor.items)
    assert not (tiene_2m and tiene_segunda)


def test_crit_infactible_con_desenlace() -> None:
    # Desenlace exige crit >= 40; sin fuentes de crit, no hay build posible.
    pool = [hacer_item(1, Slot.CASCO, elem=10)]
    with pytest.raises(BuildInfactible):
        optimizar_franja(pool, _perfil(sublimaciones=("desenlace",)), 200, StatsItem(), [])


def test_crit_factible_con_desenlace() -> None:
    pool = [hacer_item(1, Slot.CASCO, elem=10, crit=40), hacer_item(2, Slot.AMULETO, elem=5)]
    cands = optimizar_franja(pool, _perfil(sublimaciones=("desenlace",)), 200, StatsItem(), [])
    assert cands
    assert cands[0].totales.crit_pct >= 40


def test_items_fijos_consumen_slots_y_cupos() -> None:
    # Dos anillos fijos (1 reliquia + 1 épico): sin slot de anillo libre ni cupo de reliquia/épico.
    fijos = [
        hacer_item(100, Slot.ANILLO, reliquia=True, elem=5),
        hacer_item(101, Slot.ANILLO, epico=True, elem=5),
    ]
    pool = [
        hacer_item(1, Slot.ANILLO, elem=99),  # tentador pero no hay slot de anillo libre
        hacer_item(2, Slot.CASCO, elem=10),
    ]
    [mejor] = optimizar_franja(pool, _perfil(n_candidatas=1), 200, StatsItem(), fijos)
    assert all(it.slot is not Slot.ANILLO for it in mejor.items)
    # La base incluye los fijos: dom_elemental total = 5+5 (fijos) + 10 (casco)
    assert mejor.totales.dom_elemental == 20


def test_crit_libera_dominio_prefiere_item_con_critico() -> None:
    # A: 46 dominio. B: 35 dom + 8 dist + 2% crit (caso Captavius vs susurrona).
    # Con crit_libera_dominio, el 2% crit vale +8 dom (Desenlace): B (43+8=51) supera a A (46).
    pool = [
        hacer_item(1, Slot.CASCO, elem=46),
        hacer_item(2, Slot.CASCO, elem=35, dist=8, crit=2),
    ]
    perfil = _perfil(sublimaciones=("desenlace",), crit_libera_dominio=True, n_candidatas=1)
    # crit base 40 para cumplir el umbral de Desenlace sin depender del equipo
    [mejor] = optimizar_franja(pool, perfil, 200, StatsItem(crit_pct=40), [])
    assert _ids(mejor) == {2}  # el casco con crítico gana

    # Sin la regla, gana el de más dominio puro (A)
    perfil2 = _perfil(sublimaciones=("desenlace",), crit_libera_dominio=False, n_candidatas=1)
    [mejor2] = optimizar_franja(pool, perfil2, 200, StatsItem(crit_pct=40), [])
    assert _ids(mejor2) == {1}


def test_alcance_prioritario_sobre_dominio() -> None:
    # Dos cascos con igual PA/PM: A da más dominio, B da menos dominio pero +1 alcance.
    # El alcance es recurso prioritario -> gana B (caso Corona susurrona vs Bandana).
    pool = [
        hacer_item(1, Slot.CASCO, elem=67),
        hacer_item(2, Slot.CASCO, elem=55, alcance=1),
    ]
    [mejor] = optimizar_franja(pool, _perfil(n_candidatas=1), 200, StatsItem(), [], modo="alcance")
    assert _ids(mejor) == {2}
    assert mejor.totales.alcance == 1


def test_enumera_varias_candidatas_distintas() -> None:
    pool = [hacer_item(i, Slot.CASCO, elem=10 + i) for i in range(5)]
    cands = optimizar_franja(pool, _perfil(n_candidatas=3), 200, StatsItem(), [])
    assert len(cands) == 3
    # Todas distintas y ordenadas por proxy decreciente
    conjuntos = [_ids(c) for c in cands]
    assert len(set(map(frozenset, conjuntos))) == 3
    assert [c.valor_proxy for c in cands] == sorted((c.valor_proxy for c in cands), reverse=True)
