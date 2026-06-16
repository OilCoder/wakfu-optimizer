# TRD — Optimizador de Builds de Wakfu

> Documento de Requisitos Técnicos · uso personal
> Estado: borrador · Última actualización: 2026-06-16

## 1. Visión técnica

El problema es **optimización combinatoria con restricciones**, no machine learning. Se resuelve con un solver exacto (MIP/CP) que da garantía de óptimo dentro de un objetivo lineal (proxy), y un **evaluador** que aplica la función de daño real, no lineal, sobre una lista corta de candidatas.

## 2. Arquitectura en dos niveles

```
                ┌─────────────────────────────────────────┐
   Datos CDN ──►│ 1. INGESTA + PARSER                      │
   (Ankama)     │   items / actions / states / itemTypes   │
                └───────────────┬─────────────────────────┘
                                │  pool filtrado + efectos decodificados
                ┌───────────────▼─────────────────────────┐
                │ 2. SOLVER EXACTO (CP-SAT)                │  ◄── nivel "verde"
                │   maximiza proxy lineal de dominio        │      óptimo garantizado
                │   sujeto a slots, ≤1 reliquia/épico,      │      y rápido
                │   breakpoints PA/PM, crit ≥ 40%           │
                └───────────────┬─────────────────────────┘
                                │  N builds candidatas
                ┌───────────────▼─────────────────────────┐
                │ 3. EVALUADOR DE DAÑO (no lineal)         │  ◄── nivel "ámbar"
                │   aplica fórmula real + rotación          │      función real
                │   reordena y elige la mejor               │
                └───────────────┬─────────────────────────┘
                                │
                          Build óptima final
```

- **Nivel verde (solver)**: genera lo óptimo dentro del proxy, en < 1 s tras filtrar.
- **Nivel ámbar (evaluador)**: corrige la no-linealidad sobre pocas candidatas.

## 3. Stack

| Componente | Elección | Motivo |
|---|---|---|
| Lenguaje | Python 3.x | Ecosistema de datos + OR-Tools |
| Datos | JSON CDN de Ankama | Fuente oficial, sincronizada con el juego |
| HTTP/parse | `requests` + `json` | Bajar y parsear; `items.json` >20 MB → cachear en disco |
| Solver | **Google OR-Tools CP-SAT** | Maneja nativo ≤1 reliquia, ≤1 épico, slots, breakpoints; gratis |
| Alternativa solver | PuLP + CBC | MIP puro si se prefiere |
| Evaluador | Python puro | Fórmula de daño + rotación |
| (Opcional) surrogate | XGBoost | Solo si el evaluador fuera caro de llamar |

## 4. Fuentes de datos (CDN Ankama)

Patrón de URL: `https://wakfu.cdn.ankama.com/gamedata/{version}/{type}.json`

**Leer la versión dinámicamente** (no hardcodear):

```python
import requests
BASE = "https://wakfu.cdn.ankama.com/gamedata"
version = requests.get(f"{BASE}/config.json").json()["version"]   # p.ej. "1.91.1.54"
items = requests.get(f"{BASE}/{version}/items.json").json()
```

Archivos y su rol:

| Archivo | Contenido | Uso |
|---|---|---|
| `config.json` | `{"version": "..."}` | Resolver la versión activa |
| `items.json` (>20 MB) | Catálogo de ítems | Pool principal. Cada ítem: `definition.item` (id, level, baseParameters→itemTypeId, rareza), `definition.equipEffects[]` ({actionId, params}), `title` |
| `actions.json` | Diccionario de efectos | Traduce `actionId` → qué stat es y cómo leer `params` |
| `states.json` | Estados/sublimaciones/sets | Lógica de Desenlace, bonus de set |
| `itemProperties.json` | Flags especiales | `8`=reliquia, `12`=épico, `19`/`20`=slot gema reliquia/épica |
| `equipmentItemTypes.json` | Mapa itemTypeId → slot | Restricciones de slot. Ej. verificado: `132`=BACK(capa), `103`=anillo, `134`=HEAD, `136`=CHEST, `120`=NECK. Arma 2 manos (519) bloquea SECOND_WEAPON |

**Pendiente de verificar empíricamente**: el entero exacto del campo de rareza para "mítico" (abrir un ítem mítico conocido —Capa d'Or/Mekacapa— y leer su valor antes de confiar en el filtro).

**Nota i18n**: parte de los textos vienen solo en francés; cruzar con tablas de estados para traducciones.

## 5. Modelo de optimización

### 5.1 Variables

`x_i ∈ {0,1}` por ítem candidato (equipado / no).

### 5.2 Restricciones de slot

Σ por tipo: casco ≤1, amuleto ≤1, capa ≤1, coraza ≤1, cinturón ≤1, botas ≤1, hombreras ≤1, arma ≤1 (2 manos bloquea segunda mano), anillos ≤2, mascota ≤1, trofeos/emblema según slots de accesorio.

### 5.3 Restricciones globales (las que cruzan slots)

```
Σ reliquias ≤ 1
Σ épicos    ≤ 1
```

Son las que rompen la independencia entre slots: el solver decide en qué slot "gastar" el único cupo de reliquia/épico.

### 5.4 Agregación de stats y breakpoints

```
S_t = base(clase, nivel) + Σ_i x_i · stat_{i,t}      (para cada stat t)

S_PA  ≥ objetivo_PA      (p. ej. 13)
S_PM  ≥ objetivo_PM      (p. ej. 4)
S_crit ≥ 40%             (suelo de Desenlace — restricción dura)
S_resist ≥ piso          (opcional)
```

## 6. Modelo de daño (la parte fina)

Fórmula de daño en Wakfu (verificada contra fórmulas de la comunidad):

```
daño = base × (1 + maestrías/100) × (1 + daños_finales/100) × (1 − resistencia/100)
```

Puntos clave a respetar:

- **El crítico NO es un +25% de daño final.** Aumenta la **base del golpe ×1,25**, lo que multiplica todo el resto. Por eso pesa más que un 25% de daños finales.
- `maestrías` suma dominio elemental + secundarias (distancia/melé, único/zona) + dominio crítico/no-crítico **según aplique la condición**.
- El crítico entra en dos sitios: amplía la base (×1,25) **y** activa el saco de "dominio crítico".

### 6.1 Efecto de Desenlace

Desenlace convierte el **dominio crítico** en **dominio elemental** al inicio del combate si `crit ≥ 40%`. Consecuencia para los pesos:

- Sin Desenlace, el dominio crítico solo cuenta en los críticos → peso ≈ `0,40 × 1,25 / 1,10 ≈ 0,45` relativo al dominio elemental.
- **Con Desenlace**, el dominio crítico pasa a aplicarse siempre → **peso 1,0** (igual que el elemental).
- La tasa de crítico **por encima del 40%** ya no añade maestría (el dominio crítico ya se convirtió), pero sigue aplicando la base ×1,25 a más golpes → factor `(1 + 0,25·crit)`. Aporta poco (~+0,23% de daño por +1% crit con stats altas) pero no es cero.

### 6.2 Coste de oportunidad crit-rate ↔ dominio crítico

Cada punto de característica de Suerte: `+4 dominio crítico` **o** `+1% golpe crítico`. Con maestría efectiva alta (~3.941):

- `+4 dominio crítico` (peso 1,0) → `+4 / (100 + 3941) ≈ +0,099%` daño
- `+1% crit` (sobre 40%) → `0,25 / (1 + 0,25·0,40) ≈ +0,23%` daño

→ Por encima del umbral, con maestría ya alta, el **crit-rate excedente suele ganar** por punto. El equilibrio se mueve a favor del crit-rate cuanta más maestría acumulas (más se diluyen los +4 planos). **Verificar el valor real por punto en el árbol**, que puede no ser exactamente 1% por caps/coste escalado.

> Consejo de diseño: no clavar la build exactamente en 40% de crit. Un pequeño colchón evita perder Desenlace entero si el enemigo reduce 1% de crítico.

### 6.3 Función objetivo (proxy para el solver)

```
maximizar   Σ_i x_i · (dom_elem_principal_i + dom_distancia_i + dom_crítico_i)
            × (1 + daños_finales/100)
            × (1 + 0,25 · tasa_crítico)
sujeto a    crit ≥ 40%, slots, ≤1 reliquia, ≤1 épico, PA/PM objetivo, rareza permitida
```

(En el solver, el objetivo se linealiza; los factores multiplicativos `(1+daños_finales)` y `(1+0,25·crit)` se tratan como términos separados o se fijan por plantilla de stats. El cálculo no lineal exacto va al evaluador.)

## 7. Lo que complica el problema (deuda técnica conocida)

- **Bonus de set**: variables auxiliares `y_{set,k} = 1 si ≥k piezas` + restricciones de enlace. Viable en MIP, añade variables. Fuera de v1.
- **Sublimaciones/runas + slots de gema**: segunda capa combinatoria; optimizar en fase aparte.
- **Stats condicionales** (dependen de estado/posición/vida): no lineales → sacarlas del solver, meterlas solo en el evaluador.

## 8. Rendimiento

Tras filtrar por nivel/elemento/rareza quedan pocos cientos de ítems por categoría → CP-SAT resuelve en < 1 s. `items.json` se cachea en disco para no descargar 20 MB en cada ejecución.

## 9. Referencias

- JSON oficial: foro de desarrollo de Wakfu (hilo "JSON data").
- Fórmula de daño: guías de la comunidad sobre la fórmula de maestría; wikis (Fandom / wakfu.wiki.gg) para el escalado de características.
- Builders de referencia: Method Wakfu / Zenith Builder (consulta, no optimización).
- Existe un proyecto open source que ataca esto con algoritmo genético (referencia; el genético no garantiza óptimo, a diferencia de CP-SAT).
