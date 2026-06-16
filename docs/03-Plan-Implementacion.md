# Plan de Implementación — Optimizador de Builds de Wakfu

> Roadmap por fases · uso personal
> Estado: borrador · Última actualización: 2026-06-16

La idea: construir de abajo arriba, validando cada capa antes de la siguiente. No pasar de fase sin un "criterio de hecho" cumplido.

## Fase 0 — Setup

- Crear repo / carpeta de proyecto con `data/` (caché de JSON), `src/`, `docs/`.
- Entorno Python con `requests` y `ortools`.
- **Hecho cuando**: `import ortools` y `import requests` funcionan.

## Fase 1 — Ingesta de datos

- Script que lee `config.json` → versión activa → descarga `items.json`, `actions.json`, `states.json`, `itemProperties.json`, `equipmentItemTypes.json`.
- Cachear en `data/{version}/` para no rebajar 20 MB cada vez.
- **Verificación clave**: abrir un ítem mítico conocido (Capa d'Or / Mekacapa) e imprimir su campo de **rareza** y un `equipEffect` crudo. Fijar así el entero de "mítico" empíricamente.
- **Hecho cuando**: tengo el código de rareza mítica confirmado y los archivos cacheados.

## Fase 2 — Parser / modelo de dominio

- Construir un decodificador `actionId → (stat, cómo leer params)` usando `actions.json`.
- Mapear `itemTypeId → slot` con `equipmentItemTypes.json` (incluyendo bloqueo de arma a 2 manos).
- Marcar reliquia/épico con `itemProperties.json` (flags 8 y 12).
- Normalizar cada ítem a una estructura limpia: `{id, nombre, slot, rareza, es_reliquia, es_epico, stats:{elem, distancia, crit_dominio, PA, PM, crit_rate, daños_finales, ...}}`.
- **Hecho cuando**: puedo imprimir la Capa d'Or ya decodificada con sus stats legibles (cruzando con lo que muestra el juego).

## Fase 3 — Solver (núcleo, CP-SAT)

- Variables binarias `x_i` por ítem del pool filtrado (nivel, elemento, rareza).
- Restricciones: slots, ≤1 reliquia, ≤1 épico, breakpoints PA/PM, `crit ≥ 40%`.
- Objetivo: proxy lineal `Σ (elem_principal + distancia + dom_crítico)` con dom_crítico a peso 1,0 (Desenlace activo).
- **Hecho cuando**: dado "solo míticos, PA 13 / PM 4, crit ≥ 40%", devuelve una build válida y demostrablemente óptima en el proxy, en < pocos segundos.

## Fase 4 — Evaluador de daño

- Implementar la fórmula real: `base × (1+maestrías/100) × (1+daños_finales/100) × (1−resist/100)`, con el crítico amplificando la base ×1,25 y la conversión de Desenlace.
- Pasar la lista corta de candidatas del solver por el evaluador y reordenar.
- **Hecho cuando**: para un caso conocido, el evaluador reproduce números coherentes con los del juego y la build elegida iguala o supera a una armada a mano.

## Fase 5 — Interfaz mínima (CLI)

- Definir el perfil de build por archivo de config o flags: clase, nivel, elemento(s), breakpoints, rareza permitida, sublimaciones activas.
- Salida legible: lista de ítems + stats agregadas + daño estimado.
- **Hecho cuando**: puedo lanzar una optimización completa desde una sola línea de comando.

## Fase 6 — Extensiones (cuando v1 funcione)

En orden de valor:

1. **Bonus de set** (variables auxiliares `y_{set,k}` + enlaces).
2. **Sublimaciones/runas y slots de gema** como segunda fase de optimización.
3. **Multi-objetivo** (daño vs. resistencias/vida).
4. **Surrogate XGBoost** solo si el evaluador con rotación completa se vuelve caro de llamar.
5. UI gráfica (entonces se crean los docs de UI/UX, AppFlow y Esquema BackEnd).

## Orden de dependencias

```
Fase 0 ─► Fase 1 ─► Fase 2 ─► Fase 3 ─► Fase 4 ─► Fase 5 ─► Fase 6
                         (Fase 3 y 4 son el corazón del sistema)
```

## Primeros pasos concretos (siguiente sesión)

1. Montar Fase 0 + Fase 1: script de descarga con versión dinámica y caché.
2. Verificar el código de rareza mítica con la Capa d'Or.
3. Empezar el decodificador de `actionId` con los 4-5 efectos que importan para daño.
