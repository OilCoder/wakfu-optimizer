"""Interfaz de línea de comandos del optimizador.

Subcomandos:
  optimizar          resuelve la mejor build para un perfil TOML
  descargar          fuerza la descarga/caché de los datos del CDN
  listar-slots       muestra el mapeo itemTypeId -> slot (depuración)
  inspeccionar-item  muestra los stats normalizados de un ítem por id (depuración)

Los handlers importan los módulos pesados de forma perezosa para que `--help` sea
instantáneo y no dependa de que todas las fases estén implementadas.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wakfu_opt.dominio.modelos import BuildCandidata, Item, PerfilBuild, StatsItem


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wakfu-opt",
        description="Optimizador de builds de Wakfu (solver CP-SAT + evaluador de daño).",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    # Subcomando: optimizar
    p_opt = sub.add_parser(
        "optimizar", help="resuelve la mejor build por franja para un perfil TOML"
    )
    p_opt.add_argument("--perfil", required=True, help="ruta al perfil de build (.toml)")
    p_opt.add_argument(
        "--salida", default=None, help="carpeta de salida (def. salidas/<nombre_perfil>)"
    )
    p_opt.add_argument("--datos", default=None, help="directorio de datos (def. autodetecta)")
    p_opt.add_argument("--pdf", action="store_true", help="exportar también los informes a PDF")
    p_opt.set_defaults(func=_cmd_optimizar)

    # Subcomando: descargar
    p_dl = sub.add_parser("descargar", help="descarga y cachea los datos del CDN de Ankama")
    p_dl.add_argument("--forzar", action="store_true", help="redescarga aunque exista la caché")
    p_dl.set_defaults(func=_cmd_descargar)

    # Subcomando: listar-slots
    p_slots = sub.add_parser("listar-slots", help="muestra el mapeo itemTypeId -> slot")
    p_slots.set_defaults(func=_cmd_listar_slots)

    # Subcomando: inspeccionar-item
    p_insp = sub.add_parser("inspeccionar-item", help="muestra los stats normalizados de un ítem")
    p_insp.add_argument("id", type=int, help="id del ítem a inspeccionar")
    p_insp.set_defaults(func=_cmd_inspeccionar_item)

    # Subcomando: buscar-piedra
    p_piedra = sub.add_parser("buscar-piedra", help="busca sublimaciones por nombre en el catálogo")
    p_piedra.add_argument("texto", nargs="?", default="", help="texto a buscar en el nombre")
    p_piedra.add_argument(
        "--categoria",
        choices=("epica", "reliquia", "gema", "mejora"),
        default=None,
        help="filtra por categoría de sublimación",
    )
    p_piedra.set_defaults(func=_cmd_buscar_piedra)

    return parser


# ----------------------------------------
# Handlers (import perezoso de módulos pesados)
# ----------------------------------------


def _cmd_descargar(args: argparse.Namespace) -> int:
    from wakfu_opt.datos.cargador import asegurar_datos

    dir_version = asegurar_datos(forzar=args.forzar)
    print(f"Datos disponibles en: {dir_version}")
    return 0


def _cmd_listar_slots(args: argparse.Namespace) -> int:
    from wakfu_opt.datos.cargador import cargar, localizar_datos
    from wakfu_opt.datos.mapeo_slots import construir_mapeo

    dir_version = localizar_datos()
    mapeo = construir_mapeo(cargar("equipmentItemTypes", dir_version))
    print(f"{'itemTypeId':>10}  {'slot':<14}  bloquea_2da_mano")
    for type_id in sorted(mapeo):
        info = mapeo[type_id]
        print(f"{type_id:>10}  {info.slot.value:<14}  {info.bloquea_segunda_mano}")
    print(f"\n{len(mapeo)} tipos con slot optimizable.")
    return 0


def _cmd_inspeccionar_item(args: argparse.Namespace) -> int:
    from dataclasses import fields

    from wakfu_opt.datos.cargador import cargar, localizar_datos
    from wakfu_opt.datos.mapeo_slots import construir_mapeo
    from wakfu_opt.normalizador import normalizar_item

    dir_version = localizar_datos()
    mapeo = construir_mapeo(cargar("equipmentItemTypes", dir_version))
    crudos = {it["definition"]["item"]["id"]: it for it in cargar("items", dir_version)}

    crudo = crudos.get(args.id)
    if crudo is None:
        print(f"No existe el ítem con id {args.id}.")
        return 1

    item = normalizar_item(crudo, mapeo)
    if item is None:
        print(f"El ítem {args.id} no tiene slot optimizable (cosmético o tipo huérfano).")
        return 1

    print(f"[{item.id}] {item.nombre}  (nivel {item.nivel})")
    print(f"  slot={item.slot.value}  rareza={item.rareza.name}")
    print(f"  reliquia={item.es_reliquia}  epico={item.es_epico}  set_id={item.set_id}")
    print("  stats:")
    for campo in fields(item.stats):
        valor = getattr(item.stats, campo.name)
        if valor:
            print(f"    {campo.name} = {valor}")
    return 0


def _cmd_buscar_piedra(args: argparse.Namespace) -> int:
    from wakfu_opt.datos.cargador import cargar, localizar_datos
    from wakfu_opt.datos.catalogo_piedras import buscar, construir_catalogo

    dir_version = localizar_datos()
    titulos = {
        s["definition"]["id"]: s.get("title", {}).get("es", "")
        for s in cargar("states", dir_version)
    }
    catalogo = construir_catalogo(cargar("items", dir_version), titulos)

    resultados = buscar(catalogo, args.texto, categoria=args.categoria)
    resultados.sort(key=lambda e: (e.categoria, e.nombre))
    for e in resultados:
        estado = f"state {e.state_id} ({e.nombre_estado})" if e.state_id else "—"
        print(f"  [{e.id:>5}] {e.categoria:<9} {e.nombre:<32} {estado}")
    print(f"\n{len(resultados)} sublimaciones encontradas.")
    return 0


def _cmd_optimizar(args: argparse.Namespace) -> int:
    from dataclasses import replace
    from pathlib import Path

    from wakfu_opt.datos.cargador import cargar, localizar_datos
    from wakfu_opt.datos.mapeo_slots import construir_mapeo
    from wakfu_opt.evaluador.reordenador import evaluar
    from wakfu_opt.normalizador import normalizar_catalogo
    from wakfu_opt.perfil import cargar_perfil
    from wakfu_opt.pool import filtrar_pool, resolver_items_fijos
    from wakfu_opt.reporte import escribir_reporte
    from wakfu_opt.solver.modelo_cpsat import BuildInfactible, optimizar_franja

    perfil, base = cargar_perfil(args.perfil)

    dir_version = localizar_datos(Path(args.datos) if args.datos else None)
    mapeo = construir_mapeo(cargar("equipmentItemTypes", dir_version))
    catalogo, _ = normalizar_catalogo(cargar("items", dir_version), mapeo)
    items_fijos = resolver_items_fijos(catalogo, perfil)

    modos = ("optimo", "recursos", "pa", "pm", "alcance", "pw", "dano")
    print(f"Optimizando {perfil.clase} ({perfil.estilo}) — franjas {list(perfil.franjas)}")
    resultados: dict[int, dict[str, object]] = {}
    for franja in perfil.franjas:
        # Los ítems fijos solo aplican si su nivel cabe en la franja. Si falta alguno (p. ej.
        # los anillos con las piedras a nivel bajo), esa franja va sin sublimaciones: las piedras
        # viven en esos ítems, así que sus restricciones (crit≥40 de Desenlace) no aplican.
        fijos_franja = [it for it in items_fijos if it.nivel <= franja]
        perfil_franja = perfil
        if len(fijos_franja) < len(items_fijos):
            perfil_franja = replace(perfil, sublimaciones=())

        pool = filtrar_pool(catalogo, perfil_franja, franja)
        por_modo: dict[str, object] = {}
        for modo in modos:
            try:
                if modo == "optimo":
                    candidatas = _optimizar_optimo(pool, perfil_franja, franja, base, fijos_franja)
                else:
                    candidatas = optimizar_franja(
                        pool, perfil_franja, franja, base, fijos_franja, modo
                    )
            except BuildInfactible:
                candidatas = []
            por_modo[modo] = evaluar(candidatas, perfil_franja)[0] if candidatas else None
        resultados[franja] = por_modo
        sin_piedra = " (sin piedras)" if perfil_franja is not perfil else ""
        danos = " · ".join(
            f"{m}={(r.dano_estimado):.0f}" if (r := por_modo[m]) else f"{m}=—"  # type: ignore[attr-defined]
            for m in modos
        )
        print(f"  franja ≤{franja}{sin_piedra}: daño {danos}")

    if all(r is None for por_modo in resultados.values() for r in por_modo.values()):
        print("Ninguna franja produjo una build factible. Revisa breakpoints/crit/pool.")
        return 1

    # Una carpeta por perfil: usa el nombre del archivo .toml (único por perfil)
    nombre_perfil = Path(args.perfil).stem
    dir_salida = Path(args.salida) if args.salida else Path("salidas") / nombre_perfil
    escribir_reporte(resultados, perfil, dir_salida)  # type: ignore[arg-type]
    print(f"\nInforme escrito en: {dir_salida}/  ({len(modos)} estrategias por franja)")

    # PDF si lo pide la línea de comandos o el perfil; ZIP solo si lo pide el perfil
    if args.pdf or perfil.exportar_pdf:
        from wakfu_opt.exportar_pdf import agrupar_zip, exportar_carpeta

        n = exportar_carpeta(dir_salida)
        if perfil.agrupar_zip:
            ruta_zip = agrupar_zip(dir_salida)
            print(f"{n} PDFs agrupados en: {ruta_zip} (sin PDFs sueltos)")
        else:
            print(f"Exportados {n} PDF en {dir_salida}/")
    return 0


def _optimizar_optimo(
    pool: list[Item],
    perfil: PerfilBuild,
    franja: int,
    base: StatsItem,
    fijos: list[Item],
) -> list[BuildCandidata]:
    """Selección óptima: maximiza el daño TOTAL (dominio × PA), no solo el dominio.

    Itera el valor de 1 PA (≈ maestría/PA) porque la linealización de un único punto no
    da el máximo del producto. Prueba varios valores y se queda con la build de más daño
    total real (que el evaluador calcula ya como daño_por_golpe × PA).
    """
    from wakfu_opt.evaluador.reordenador import evaluar
    from wakfu_opt.solver.modelo_cpsat import BuildInfactible, optimizar_franja

    candidatas: list[list[BuildCandidata]] = []

    def probar(valor_pa: float) -> list[BuildCandidata]:
        try:
            return optimizar_franja(
                pool, perfil, franja, base, fijos, modo="dano", valor_pa=valor_pa
            )
        except BuildInfactible:
            return []

    # Extremos: máx daño puro (valor_pa=0) y máx PA. El óptimo no será peor que ninguno.
    candidatas.append(probar(0.0))
    try:
        candidatas.append(optimizar_franja(pool, perfil, franja, base, fijos, modo="pa"))
    except BuildInfactible:
        pass

    # Iterar el valor de 1 PA (≈ maestría/PA) buscando el balance PA↔dominio que más daño da.
    valor_pa = 0.0
    for _ in range(5):
        cand = probar(valor_pa)
        if not cand:
            break
        candidatas.append(cand)
        t = evaluar(cand, perfil)[0].totales
        maestria = t.dom_elemental + 0.5 * t.dom_mono_elemental + t.dom_distancia + t.dom_critico
        nuevo = maestria / max(t.pa, 1)
        if abs(nuevo - valor_pa) < 0.5:
            break
        valor_pa = nuevo

    candidatas = [c for c in candidatas if c]
    if not candidatas:
        return []
    # Quedarse con la candidata de mayor daño total real (daño_por_golpe × PA)
    return max(candidatas, key=lambda c: evaluar(c, perfil)[0].dano_estimado)


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la CLI. Devuelve el código de salida del proceso."""
    parser = _construir_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
