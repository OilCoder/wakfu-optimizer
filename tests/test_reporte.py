"""Tests de la escritura del reporte Markdown."""

from __future__ import annotations

from pathlib import Path

from wakfu_opt.dominio.modelos import Item, PerfilBuild, ResultadoBuild, StatsItem
from wakfu_opt.dominio.rareza import Rareza
from wakfu_opt.dominio.slots import Slot
from wakfu_opt.reporte import escribir_reporte


def _item(id: int, slot: Slot, nombre: str) -> Item:
    return Item(
        id=id,
        nombre=nombre,
        nivel=200,
        slot=slot,
        item_type_id=0,
        rareza=Rareza.MITICO,
        es_reliquia=False,
        es_epico=False,
        bloquea_segunda_mano=False,
        set_id=0,
        stats=StatsItem(dom_elemental=100),
    )


def test_escribe_resumen_y_franjas(tmp_path: Path) -> None:
    perfil = PerfilBuild(clase="sram", franjas=(200,), estilo="distancia")
    resultado = ResultadoBuild(
        franja=200,
        items=(_item(1, Slot.CASCO, "Casco X"),),
        items_fijos=(_item(9723, Slot.ANILLO, "Gelanillo"),),
        dano_estimado=4979.4,
        valor_proxy=3129.0,
        crit_final_pct=64.0,
        totales=StatsItem(dom_elemental=1923, pa=8, crit_pct=64),
        ranking=1,
    )
    salida = escribir_reporte(
        {200: {"pa": resultado, "pm": resultado, "alcance": resultado, "dano": resultado}},
        perfil,
        tmp_path / "out",
    )

    assert (salida / "resumen.md").exists()
    franja = salida / "franja_200.md"
    assert franja.exists()
    texto = franja.read_text(encoding="utf-8")
    assert "Casco X" in texto
    assert "Gelanillo *" in texto  # el ítem fijo se marca con *
    assert "≤ 200" in texto
    assert "Máx PA" in texto and "Máx daño" in texto  # las estrategias aparecen
