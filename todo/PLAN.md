# Optimizador de Builds de Wakfu

## Goal
Dado un perfil (clase, franjas de nivel, piedras, anillos fijos), devolver el mejor set de
ítems míticos por franja que maximiza PA→PM→daño, con garantía de óptimo en el proxy lineal.

## Stack
| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.12 (venv en `.venv`) |
| Solver | OR-Tools CP-SAT (`ortools`) |
| Datos | JSON del CDN de Ankama (`requests`) |
| Perfil | TOML (`tomllib`) |
| Tests/calidad | `pytest`, `ruff`, `mypy` |

## Structure
```
src/wakfu_opt/
├── cli.py                 # subcomandos: optimizar, descargar, listar-slots, inspeccionar-item, buscar-piedra
├── config.py              # rutas + CDN
├── perfil.py              # carga perfil TOML -> PerfilBuild + base de características
├── normalizador.py        # ítem crudo -> Item
├── pool.py                # filtrado por franja/rareza + ítems fijos
├── reporte.py             # Markdown: resumen.md + franja_NNN.md
├── datos/{cargador,mapeo_slots,mapeo_acciones,catalogo_piedras}.py
├── dominio/{modelos,rareza,slots,sublimaciones,bases_clase}.py
├── solver/{pesos,modelo_cpsat,solucion}.py
└── evaluador/{formula_dano,reordenador}.py
data/{version}/            # caché JSON del CDN (gitignored)
perfiles/*.toml            # perfiles de build
salidas/<clase>_<estilo>/  # reportes Markdown por franja (gitignored)
```

## Phases

### Phase 0 — Andamiaje (COMPLETED)
- [x] Paquete `src/wakfu_opt/`, pyproject, venv, CLI con `--help` (2026-06-16)

### Phase 1 — Carga y mapeos (COMPLETED)
- [x] `datos/cargador.py`: descarga CDN versión dinámica + caché + offline (2026-06-16)
- [x] `datos/mapeo_slots.py`: itemTypeId→slot + bloqueo 2 manos (2026-06-16)
- [x] `datos/mapeo_acciones.py`: actionId→stat, 1068 elemental variable (2026-06-16)

### Phase 2 — Normalización y dominio (COMPLETED)
- [x] `dominio/{modelos,rareza,slots,sublimaciones,bases_clase}.py` (2026-06-16)
- [x] `normalizador.py`: ítem crudo→Item, descarta huérfanos (2026-06-16)

### Phase 3 — Pool y filtros (COMPLETED)
- [x] `pool.py`: filtra por rareza/nivel/franja, excluye ítems fijos (2026-06-16)

### Phase 4 — Solver CP-SAT (COMPLETED)
- [x] `solver/{pesos,modelo_cpsat,solucion}.py`: lexicográfico PA→PM→dominio,
      crit≥40 (Desenlace), ≤1 reliquia/épico, bloqueo 2 manos, N candidatas (2026-06-16)

### Phase 5 — Evaluador de daño (COMPLETED)
- [x] `evaluador/{formula_dano,reordenador}.py`: fórmula no lineal + reordenamiento (2026-06-16)

### Phase 6 — CLI, reporte y perfil (COMPLETED)
- [x] `perfil.py`, `reporte.py`, `cli.py optimizar`, `perfiles/ejemplo_distancia.toml` (2026-06-16)
- [x] Catálogo de sublimaciones + comando `buscar-piedra` (2026-06-16)
- [x] Cuatro estrategias por franja (máx PA / máx PM / máx alcance / máx daño) en informe comparativo (2026-06-16)
- [x] Manejo de deboosts/pérdidas (restan); dominio mono-elemento ×1/n; crítico→dominio;
      alcance como recurso prioritario; rareza corregida (mítico=3) (2026-06-16)

### Phase 7 — Optimización de características (PENDIENTE)
- [ ] Modelar el sistema de características de Wakfu (puntos por rama según nivel, costes,
      qué stat da cada rama: Agilidad→distancia, Fortuna→crit/dom crítico, Mayor→PA/PM/rango)
- [ ] Integrar el reparto de puntos como variables del solver (no como base fija del perfil),
      siguiendo la estrategia: maximizar dominio distancia, crit a 40 (umbral Desenlace), resto dom crítico
- [ ] Validar contra los números del juego para una franja conocida

### Phase 8 — Extensiones (futuro)
- [ ] Bonus de set (variables auxiliares y_{set,k}) — BLOQUEADO: los bonus no están en el CDN
      (210 sets vía itemSetId, pero sin valores). Requiere fuente externa o captura por set usado.
- [ ] Gemas/sublimaciones normales de color (slots de engarce)
- [x] Distinguir dominio elemental general vs mono-elemento; ponderar mono por 1/n_elementos
      para builds multi-elemento (2026-06-16)
- [ ] Refinar aún más: elegir los 2 elementos óptimos que maximizan el aprovechamiento de las
      maestrías mono-elemento de los ítems (hoy se asume reparto uniforme)

### Nota — datos que el CDN NO incluye (todos requieren fuente externa)
Efecto numérico de sublimaciones (resuelto a mano: Desenlace, Último Instante), bonus de set,
y el sistema de características (puntos por rama/nivel). El CDN solo da los stats de cada ítem.

## Conventions
- Comentarios/identificadores en español, snake_case.
- Verificar siempre antes de cerrar fase: `pytest -q`, `ruff check`, `mypy src/`.
- Efectos de piedras: codificados a mano en `dominio/sublimaciones.py` (NO están en el CDN),
  vinculados por `state_id` al catálogo de datos.
