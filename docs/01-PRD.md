# PRD — Optimizador de Builds de Wakfu

> Documento de Requisitos de Producto (versión ligera, uso personal)
> Estado: borrador · Última actualización: 2026-06-16

## 1. Resumen en una frase

Una herramienta que, dado un conjunto de restricciones (clase, nivel, breakpoints de PA/PM, rareza permitida), selecciona automáticamente la combinación de ítems que **maximiza el daño** de una build de Wakfu, con **garantía de optimalidad** dentro del modelo.

## 2. Problema

Armar una build óptima en Wakfu es un problema de optimización combinatoria que los jugadores resuelven a mano o con builders web (Zenith/Method Wakfu) que **muestran** stats pero **no optimizan**: el jugador sigue eligiendo ítem por ítem. Las dificultades reales son:

- **Restricciones cruzadas**: solo 1 reliquia y 1 épico equipables en todo el equipo, sin importar el slot. Esto rompe la independencia entre slots y es lo que hace el problema no trivial.
- **Breakpoints duros**: una build solo sirve si alcanza ciertos PA/PM (p. ej. 12/6). Por debajo, no vale nada por mucho dominio que tenga.
- **Daño no lineal**: el daño real combina dominio, % daño y crítico de forma multiplicativa; maximizar "suma de dominio" no da el óptimo exacto.
- **Sublimaciones que cambian las reglas**: p. ej. **Desenlace** convierte el dominio crítico en dominio elemental al inicio del combate si la tasa de crítico ≥ 40%, lo que altera el peso de cada stat.

## 3. Usuario

Yo (uso personal). Jugador que conoce las mecánicas y quiere una respuesta verificable a "¿cuál es el mejor equipo para esta build bajo estas condiciones?", en vez de tantear a mano.

## 4. Objetivo y métricas de éxito

- **Objetivo**: dado un perfil de build, devolver el set de ítems que maximiza el daño esperado cumpliendo todas las restricciones.
- **Éxito**: el solver devuelve una build válida (cumple slots, PA/PM, rareza) y demostrablemente óptima dentro del proxy lineal, en < pocos segundos tras filtrar el pool.
- **Verificación**: las builds candidatas se comparan con un evaluador de daño fiel; la elegida debe ganar o empatar a builds armadas a mano.

## 5. Features

### 5.1 Imprescindibles (v1)

- Cargar el catálogo de ítems desde el JSON oficial de Ankama (CDN), leyendo la versión activa dinámicamente.
- Filtrar el pool por: nivel máximo, elemento(s) relevantes, y **rareza permitida** (p. ej. solo míticos).
- Definir un perfil de build: clase/base de stats, breakpoints de PA/PM/rango, tasa de crítico mínima, sublimaciones activas (Desenlace).
- Resolver con un solver exacto (CP-SAT) que maximice el dominio efectivo respetando:
  - slots (1 casco, 2 anillos, 1 capa, etc. + bloqueos de arma a 2 manos),
  - ≤ 1 reliquia y ≤ 1 épico,
  - breakpoints como restricciones duras.
- Imprimir la build resultante con sus stats agregadas.

### 5.2 Deseables (más adelante)

- Evaluador de daño no lineal con rotación real para reordenar la lista corta de candidatas.
- Soporte de bonus de set (2/3/4+ piezas).
- Sublimaciones/runas y slots de gema como segunda fase de optimización.
- Multi-objetivo (daño vs. resistencias vs. vida).

## 6. Alcance — qué NO hace (v1)

- **No** tiene interfaz gráfica: es script/CLI. (Si luego se le añade UI, se documenta aparte.)
- **No** modela PvP ni mecánicas dependientes de posición/estado del enemigo en el solver (eso va al evaluador, no a la optimización).
- **No** scrapea precios de mercado en tiempo real (los kamas son orientativos, no una restricción del modelo en v1).
- **No** optimiza sublimaciones/runas en v1 (se asumen fijas como input).

## 7. Supuestos y restricciones

- Los datos vienen del CDN oficial de Ankama; el export de gamedata puede ir por detrás del número de parche del cliente (verificado: cliente en 1.92, gamedata en 1.91.1.54).
- El óptimo se garantiza **dentro del proxy lineal**; el daño exacto no lineal se resuelve en la fase de evaluación, no en el solver.
- Build de referencia inicial: orientada a daño a distancia, mono o multi-elemento, con Desenlace activo (tasa de crítico clavada en el umbral del 40%).

## 8. Riesgos

- **Modelo de daño impreciso** → mitigación: separar solver (proxy) de evaluador (función real).
- **Códigos de datos mal mapeados** (rareza, actionId) → mitigación: verificar empíricamente contra ítems conocidos antes de confiar en el filtro.
- **Explosión combinatoria con sets/sublis** → mitigación: dejarlo fuera de v1; abordarlo por fases.
