"""Generación del informe Markdown: una carpeta por perfil, un archivo por franja.

Cada franja compara las tres estrategias de optimización (recursos / breakpoint / daño),
con sus totales y el equipo de cada una. `resumen.md` tabula las tres por franja.
"""

from __future__ import annotations

from pathlib import Path

from wakfu_opt.dominio.modelos import PerfilBuild, ResultadoBuild
from wakfu_opt.dominio.slots import Slot

_ORDEN_SLOTS = list(Slot)

# Modo interno -> etiqueta legible en el informe
ETIQUETA_MODO = {
    "optimo": "Óptimo (PA valorado en daño)",
    "recursos": "Máx recursos (PA→PM→alcance→daño)",
    "pa": "Máx PA (luego daño)",
    "pm": "Máx PM (luego daño)",
    "alcance": "Máx alcance (luego daño)",
    "pw": "Máx PW (luego daño)",
    "dano": "Máx daño",
}

# resultados[franja][modo] = ResultadoBuild (o None si infactible)
ResultadosPorFranja = dict[int, dict[str, ResultadoBuild | None]]


def escribir_reporte(
    resultados: ResultadosPorFranja,
    perfil: PerfilBuild,
    dir_salida: Path,
) -> Path:
    """Escribe resumen.md y un franja_NNN.md por franja. Devuelve la carpeta de salida."""
    dir_salida.mkdir(parents=True, exist_ok=True)
    for franja, por_modo in sorted(resultados.items()):
        (dir_salida / f"franja_{franja:03d}.md").write_text(
            _md_franja(franja, por_modo, perfil), encoding="utf-8"
        )
    (dir_salida / "resumen.md").write_text(_md_resumen(resultados, perfil), encoding="utf-8")
    return dir_salida


def _md_resumen(resultados: ResultadosPorFranja, perfil: PerfilBuild) -> str:
    piedras = ", ".join(perfil.sublimaciones) or "ninguna"
    lineas = [
        f"# Builds {perfil.clase} ({perfil.estilo}) — comparativa por franja y estrategia",
        "",
        f"Piedras: {piedras} · rarezas: {sorted(x.name for x in perfil.rarezas_permitidas)}",
        f"Anillos fijos: {list(perfil.items_fijos)} · n_elementos: {perfil.n_elementos}",
        "",
        "| Franja | Estrategia | PA | PM | Alc | PW | %Crít | Dom efectivo | Daño est. |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for franja, por_modo in sorted(resultados.items()):
        for modo, etiqueta in ETIQUETA_MODO.items():
            r = por_modo.get(modo)
            if r is None:
                lineas.append(f"| ≤{franja} | {etiqueta} | — | — | — | — | — | — | infactible |")
            else:
                t = r.totales
                lineas.append(
                    f"| ≤{franja} | {etiqueta} | {t.pa} | {t.pm} | {t.alcance} | {t.pw} | "
                    f"{r.crit_final_pct:.0f}% | {_dom_efectivo(r):.0f} | {r.dano_estimado:.0f} |"
                )
    lineas += ["", "Detalle del equipo de cada estrategia en `franja_NNN.md`."]
    return "\n".join(lineas) + "\n"


def _md_franja(franja: int, por_modo: dict[str, ResultadoBuild | None], perfil: PerfilBuild) -> str:
    piedras = ", ".join(perfil.sublimaciones) or "ninguna"
    lineas = [
        f"# Franja nivel ≤ {franja} — {perfil.clase} ({perfil.estilo})",
        "",
        f"Piedras: {piedras}",
        "",
    ]
    for modo, etiqueta in ETIQUETA_MODO.items():
        lineas.append(f"## {etiqueta}")
        r = por_modo.get(modo)
        if r is None:
            lineas += ["", "_Sin solución factible para esta estrategia._", ""]
            continue
        lineas += _bloque_build(r)
    return "\n".join(lineas) + "\n"


def _bloque_build(r: ResultadoBuild) -> list[str]:
    t = r.totales
    lineas = [
        "",
        f"PA {t.pa} · PM {t.pm} · Alcance {t.alcance} · PW {t.pw} · Crít {r.crit_final_pct:.0f}% · "
        f"Dom efectivo {_dom_efectivo(r):.0f} · **Daño {r.dano_estimado:.0f}**",
        "",
        "| Slot | Ítem | id | Nv | Rareza | Elem | Mono | Dist | Crít | PA | PM | Alc | PW | %Cr |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    fijos_ids = {it.id for it in r.items_fijos}
    equipo = sorted(
        [*r.items_fijos, *r.items], key=lambda it: (_ORDEN_SLOTS.index(it.slot), it.nombre)
    )
    for it in equipo:
        marca = " *" if it.id in fijos_ids else ""
        s = it.stats
        nums = [
            s.dom_elemental,
            s.dom_mono_elemental,
            s.dom_distancia,
            s.dom_critico,
            s.pa,
            s.pm,
            s.alcance,
            s.pw,
            s.crit_pct,
        ]
        cols = " | ".join(str(n) for n in nums)
        lineas.append(
            f"| {it.slot.value} | {it.nombre}{marca} | {it.id} | {it.nivel} | "
            f"{it.rareza.name.lower()} | {cols} |"
        )
    lineas += ["", "* = ítem fijo (lleva la piedra).", ""]
    return lineas


def _dom_efectivo(r: ResultadoBuild) -> float:
    """Dominio efectivo aproximado para comparar (elem + dist + crít + mono/2)."""
    t = r.totales
    return t.dom_elemental + 0.5 * t.dom_mono_elemental + t.dom_distancia + t.dom_critico
