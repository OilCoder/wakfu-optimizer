"""Tests de carga de perfiles TOML."""

from __future__ import annotations

from pathlib import Path

from wakfu_opt.dominio.rareza import Rareza
from wakfu_opt.perfil import cargar_perfil

PERFIL_EJEMPLO = Path(__file__).resolve().parents[1] / "perfiles" / "ejemplo_distancia.toml"


def test_carga_perfil_ejemplo() -> None:
    perfil, base = cargar_perfil(PERFIL_EJEMPLO)
    assert perfil.clase == "ejemplo"
    assert perfil.estilo == "distancia"
    assert perfil.items_fijos == (9723, 21692)
    assert perfil.sublimaciones == ("desenlace", "ultimo_instante")
    assert perfil.rarezas_permitidas == frozenset({Rareza.MITICO})
    assert perfil.franjas == (65, 80, 95, 110, 125, 140, 155, 170, 185, 200)
    assert base.crit_pct == 40


def test_base_vacia_por_defecto(tmp_path: Path) -> None:
    toml = tmp_path / "p.toml"
    toml.write_text('clase = "x"\nfranjas = [200]\n', encoding="utf-8")
    perfil, base = cargar_perfil(toml)
    assert perfil.rarezas_permitidas == frozenset({Rareza.MITICO})  # solo_miticos por defecto
    assert base.crit_pct == 0
