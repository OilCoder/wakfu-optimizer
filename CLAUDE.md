# Wakfu — Optimizador de Builds

Herramienta CLI en Python que, dadas restricciones (clase, nivel, breakpoints PA/PM,
rareza, sublimaciones), selecciona la combinación de ítems que **maximiza el daño** de
una build de Wakfu con **garantía de optimalidad** dentro de un proxy lineal (solver
CP-SAT), corrigiendo la no-linealidad en un evaluador de daño aparte.

> Mantener este archivo bajo 200 líneas. El detalle vive en `.claude/rules/`,
> `.claude/skills/` y los scripts de hooks.

## Documentos del proyecto (leer para orientarse)

- `docs/01-PRD.md` — qué se construye y por qué (producto, alcance v1, riesgos).
- `docs/02-TRD.md` — cómo (arquitectura en 2 niveles, stack, modelo de optimización,
  fórmula de daño, fuentes de datos del CDN de Ankama).
- `docs/03-Plan-Implementacion.md` — roadmap por fases (0→6) con "criterio de hecho".

Estado: **Fase 0 (setup)**. Aún no hay código; el plan arranca con ingesta de datos.

## Arquitectura (resumen del TRD)

```
CDN Ankama → 1. Ingesta+Parser → 2. Solver CP-SAT (proxy lineal, óptimo)
                                → 3. Evaluador de daño (no lineal) → build final
```

- **Solver (nivel verde)**: maximiza dominio efectivo con restricciones duras
  (slots, ≤1 reliquia, ≤1 épico, PA/PM, crit ≥ 40% por Desenlace). Óptimo garantizado.
- **Evaluador (nivel ámbar)**: aplica la fórmula real de daño sobre las candidatas y
  reordena.

## Stack y entorno

- Python 3.x · `ortools` (CP-SAT) · `requests` (CDN).
- Datos del CDN oficial de Ankama; versión leída dinámicamente de `config.json`.
- `items.json` (>20 MB) se cachea en `data/{version}/`.
- v1 es CLI, sin GUI.

## Convenciones

- **Idioma**: comentarios, prints, planes, docs y bitácora **en español**.
- **Nomenclatura**: `snake_case` (variables/funciones), `UPPER_SNAKE_CASE` (constantes).
- **Scripts de pipeline**: prefijo numérico `NN_<slug>.py` (ej. `01_descarga_datos.py`).
- Carpetas (`src/`, `data/`, `tests/`, `debug/`) se crean cuando su fase lo exige.

## Verificación (obligatoria antes de declarar algo hecho)

```text
test:        pytest -q
type-check:  mypy src/
lint:        ruff check
format:      ruff format
```

## Cómo trabajar aquí

Este proyecto usa la base `claude-project-base` (4 capas: reglas guían, skills
orquestan, agentes revisan/diseñan aislados, hooks fuerzan). Detalle completo en
`.claude/rules/project-guidelines.md`.

- **Reglas** (`.claude/rules/`): estilo de código, nomenclatura, logging, verificación,
  política de memoria, estilo de commits, etc. Se cargan en contexto automáticamente.
- **Skills** (`.claude/skills/`): `/checkpoint`, `/bug-fix`, `/bitacora`,
  `/plan-writing`, `/phase-executor`, `/test`, `/investigate`, `/document`,
  `/doc-enforce`, `/study`.
- **Agentes** (`.claude/agents/`): `code-reviewer`, `security-reviewer`, `architect`,
  `implementer`.

### Memoria vs bitácora

- **MEMORY.md** (Claude): manual operativo — comandos, gotchas, hechos.
- **Bitácora** (`todo/bitacora-YYYY-MM-DD.md`): diario narrativo del usuario.
- No son intercambiables. Ver `.claude/rules/memory-policy.md`.

### `documentation/` vs `docs/`

La base reserva `docs/` para GitHub Pages y `documentation/` para docs de código.
**Excepción de este proyecto**: `docs/` contiene los documentos de producto
(PRD/TRD/Plan). Si más adelante se publica una landing, decidir entonces dónde vive.

## Próximos pasos (del plan)

1. Fase 0 + Fase 1: script de descarga con versión dinámica y caché en `data/`.
2. Verificar empíricamente el código de rareza "mítico" (abrir Capa d'Or / Mekacapa).
3. Empezar el decodificador de `actionId` con los 4-5 efectos que importan para daño.
