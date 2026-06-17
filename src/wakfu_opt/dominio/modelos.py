"""Estructuras de datos del dominio: stats, ítem normalizado, perfil y resultados."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from wakfu_opt.dominio.rareza import Rareza
from wakfu_opt.dominio.slots import Slot

Estilo = Literal["distancia", "melee", "mixto"]
# Modo de optimización: cascada de recursos, maximizar un recurso, o maximizar daño puro.
Modo = Literal["recursos", "pa", "pm", "alcance", "pw", "dano"]


@dataclass(frozen=True, slots=True)
class StatsItem:
    """Stats agregables de un ítem (o de la base), sumables entre sí."""

    # Maestrías (alimentan el proxy de daño)
    dom_elemental: int = 0  # maestría elemental general (aplica a todos tus elementos)
    dom_mono_elemental: int = 0  # maestría en 1 solo elemento (rinde a medias en bi-elemento)
    dom_distancia: int = 0
    dom_melee: int = 0
    dom_critico: int = 0
    dom_berserk: int = 0
    dom_espalda: int = 0
    dom_cura: int = 0
    # Recursos / breakpoints
    pa: int = 0
    pm: int = 0
    pw: int = 0
    alcance: int = 0
    crit_pct: int = 0
    # Defensiva (se reporta, no entra al proxy)
    pv: int = 0
    # Efectos sin familia mapeada: (actionId, valor)
    otros: tuple[tuple[int, float], ...] = ()
    # Metadato del 1068 dominante: nº de elementos de la maestría variable
    elem_variable_n: int = 0

    _FAMILIAS_NUMERICAS = (
        "dom_elemental",
        "dom_mono_elemental",
        "dom_distancia",
        "dom_melee",
        "dom_critico",
        "dom_berserk",
        "dom_espalda",
        "dom_cura",
        "pa",
        "pm",
        "pw",
        "alcance",
        "crit_pct",
        "pv",
    )

    @property
    def solo_mono_elemental(self) -> bool:
        """True si su único dominio es mono-elemento (inútil en builds multi-elemento)."""
        otros_dom = (
            self.dom_elemental
            + self.dom_distancia
            + self.dom_melee
            + self.dom_critico
            + self.dom_berserk
            + self.dom_espalda
            + self.dom_cura
        )
        return self.dom_mono_elemental > 0 and otros_dom == 0

    def __add__(self, otro: StatsItem) -> StatsItem:
        """Suma campo a campo; concatena `otros` y toma el mayor `elem_variable_n`."""
        sumados = {f: getattr(self, f) + getattr(otro, f) for f in self._FAMILIAS_NUMERICAS}
        return StatsItem(
            **sumados,
            otros=self.otros + otro.otros,
            elem_variable_n=max(self.elem_variable_n, otro.elem_variable_n),
        )


@dataclass(frozen=True, slots=True)
class Item:
    """Ítem normalizado y listo para el optimizador."""

    id: int
    nombre: str
    nivel: int
    slot: Slot
    item_type_id: int
    rareza: Rareza
    es_reliquia: bool
    es_epico: bool
    bloquea_segunda_mano: bool
    set_id: int
    stats: StatsItem


@dataclass(frozen=True, slots=True)
class PerfilBuild:
    """Entrada del usuario: describe la build a optimizar."""

    clase: str
    franjas: tuple[int, ...]  # niveles tope; se optimiza un set por franja
    items_fijos: tuple[int, ...] = ()  # ids de ítems pineados (p. ej. anillos con la piedra)
    items_excluidos: tuple[int, ...] = ()  # ids vetados (no disponibles en el juego)
    sublimaciones: tuple[str, ...] = ("desenlace",)  # piedras activas (slugs)
    rarezas_permitidas: frozenset[Rareza] = field(
        default_factory=lambda: frozenset({Rareza.MITICO})
    )
    # Excepciones de rareza por slot (p. ej. segunda mano y emblema también legendarios)
    rarezas_por_slot: dict[Slot, frozenset[Rareza]] = field(default_factory=dict)
    estilo: Estilo = "distancia"
    elemento_principal: str | None = None
    n_elementos: int = 2  # nº de elementos de la build; pondera el dominio mono-elemento (1/n)
    crit_libera_dominio: bool = (
        True  # valorar el % crítico de ítems como dominio (puntos de Suerte)
    )
    nivel_min_item: int = 0
    n_candidatas: int = 20
    # Opciones de salida
    exportar_pdf: bool = False
    agrupar_zip: bool = False

    @property
    def factor_mono_elemento(self) -> float:
        """Peso del dominio mono-elemento: 1/n (en bi-elemento, 0.5)."""
        return 1.0 / self.n_elementos if self.n_elementos > 0 else 1.0

    def rarezas_de_slot(self, slot: Slot) -> frozenset[Rareza]:
        """Rarezas permitidas en un slot: su excepción si la hay, o las generales."""
        return self.rarezas_por_slot.get(slot, self.rarezas_permitidas)


@dataclass(frozen=True, slots=True)
class BuildCandidata:
    """Salida del solver para una franja, antes de evaluar el daño real."""

    franja: int
    items: tuple[Item, ...]
    items_fijos: tuple[Item, ...]
    valor_proxy: float
    totales: StatsItem  # stats sumados incluyendo base de clase y fijos


@dataclass(frozen=True, slots=True)
class ResultadoBuild:
    """Salida final tras el evaluador, para una franja."""

    franja: int
    items: tuple[Item, ...]
    items_fijos: tuple[Item, ...]
    dano_estimado: float
    valor_proxy: float
    crit_final_pct: float
    totales: StatsItem
    ranking: int


def stats_vacios() -> StatsItem:
    """Devuelve un StatsItem neutro (todo a cero), útil como acumulador inicial."""
    return StatsItem()
