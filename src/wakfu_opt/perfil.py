"""Carga de un perfil de build desde un archivo TOML.

Devuelve un `PerfilBuild` y la base de stats del personaje (contribución de las
características repartidas). En v1 la base se lee de la sección `[base]` del TOML;
optimizar el reparto de características automáticamente es trabajo de una fase posterior.
"""

from __future__ import annotations

import tomllib
from dataclasses import fields
from pathlib import Path

from wakfu_opt.dominio.modelos import PerfilBuild, StatsItem
from wakfu_opt.dominio.rareza import NOMBRE_A_RAREZA, Rareza
from wakfu_opt.dominio.slots import NOMBRE_A_SLOT, Slot


def cargar_perfil(ruta: str | Path) -> tuple[PerfilBuild, StatsItem]:
    """Lee un perfil TOML y devuelve (PerfilBuild, base de características)."""
    datos = tomllib.loads(Path(ruta).read_text(encoding="utf-8"))

    perfil = PerfilBuild(
        clase=datos["clase"],
        franjas=tuple(datos["franjas"]),
        items_fijos=tuple(datos.get("items_fijos", [])),
        items_excluidos=tuple(datos.get("items_excluidos", [])),
        sublimaciones=tuple(datos.get("sublimaciones", ["desenlace"])),
        rarezas_permitidas=_rarezas(datos),
        rarezas_por_slot=_rarezas_por_slot(datos.get("rarezas_por_slot", {})),
        estilo=datos.get("estilo", "distancia"),
        elemento_principal=datos.get("elemento_principal"),
        n_elementos=datos.get("n_elementos", 2),
        crit_libera_dominio=datos.get("crit_libera_dominio", True),
        nivel_min_item=datos.get("nivel_min_item", 0),
        n_candidatas=datos.get("n_candidatas", 20),
        exportar_pdf=datos.get("pdf", False),
        agrupar_zip=datos.get("zip", False),
    )
    return perfil, _base(datos.get("base", {}))


def _rarezas(datos: dict[str, object]) -> frozenset[Rareza]:
    """Resuelve las rarezas permitidas: `solo_miticos` o una lista `rarezas`."""
    if datos.get("solo_miticos", True) and "rarezas" not in datos:
        return frozenset({Rareza.MITICO})
    nombres = datos.get("rarezas", ["mitico"])
    assert isinstance(nombres, list)
    return frozenset(NOMBRE_A_RAREZA[str(n).lower()] for n in nombres)


def _rarezas_por_slot(seccion: dict[str, object]) -> dict[Slot, frozenset[Rareza]]:
    """Parsea excepciones de rareza por slot: `{nombre_slot: [rarezas]}`."""
    resultado: dict[Slot, frozenset[Rareza]] = {}
    for nombre_slot, rarezas in seccion.items():
        slot = NOMBRE_A_SLOT[nombre_slot.lower()]
        assert isinstance(rarezas, list)
        resultado[slot] = frozenset(NOMBRE_A_RAREZA[str(r).lower()] for r in rarezas)
    return resultado


def _base(seccion: dict[str, object]) -> StatsItem:
    """Construye la base de stats a partir de la sección [base] del TOML."""
    campos_validos = {f.name for f in fields(StatsItem)} - {"otros", "elem_variable_n"}
    valores = {
        k: int(v) for k, v in seccion.items() if k in campos_validos and isinstance(v, int | float)
    }
    # Las claves ya están filtradas a campos numéricos válidos de StatsItem.
    return StatsItem(**valores)  # type: ignore[arg-type]
