# Context Budgeting & AST Skeleton Protocol

En proyectos medianos y grandes (Brownfield con >10k líneas de código), inyectar archivos de código completos en la ventana de contexto del LLM es un anti-patrón de arquitectura que:
1. **Diluye la atención del modelo** (efecto *needle in a haystack*).
2. **Desperdicia tokens de alta gama** en cuerpos de métodos y detalles de implementación irrelevantes.
3. **Aumenta la latencia** y el costo por inferencia.

El **Protocolo de Poda de Contexto y Esqueletos AST** de `q-agent` define cómo los agentes deben explorar, razonar y diseñar antes de recurrir a la lectura completa de archivos.

---

## 1. La Regla 80/20 del Contexto de Código

- El **80% de la comprensión arquitectónica** proviene de:
  - Nombres de clases, tipos y estructuras de datos.
  - Firmas de métodos y funciones (argumentos, tipos, valores de retorno).
  - Docstrings y contratos de interfaz.
  - Grafo de importaciones y dependencias.
- El **20% restante** es el cuerpo de implementación interna de funciones, que **solo se necesita al momento exacto de editar o depurar un archivo específico**.

---

## 2. Niveles de Inyección de Código

| Nivel | Tipo de Inspección | Cuándo se usa | Herramientas / Métodos |
|---|---|---|---|
| **Nivel 0: Topología** | Estructura de carpetas y listado de módulos | P01 (Descubrimiento), P02 (Contexto) | `tree`, `find`, `list_dir` |
| **Nivel 1: Esqueleto AST** | Firmas de funciones, clases, tipos y docstrings sin cuerpos | P01, P03 (Evolución), P05 (Spec), P06 (Design) | `codegraph explore`, `ast-grep`, extractor AST |
| **Nivel 2: Grafo de Dependencias** | Quién llama a quién, blast radius e impacto de cambios | P04 (Propose), P06 (Design) | `codegraph callers`, `codegraph callees`, `grep` |
| **Nivel 3: Implementación Completa** | Archivo completo con cuerpos de funciones | P08 (Apply/Verify), Fast-Track quirúrgico | `view_file` (limitado a archivos en target) |

---

## 3. Ejemplo de Esqueleto AST vs Archivo Completo

### ❌ Inyección Pesada (Archivo Completo — 120 líneas / ~1,200 tokens):
```python
class SQLiteMeetingRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        # 40 líneas de SQL CREATE TABLE y manejo de excepciones...
        ...

    def get_by_code(self, code: str) -> Optional[Meeting]:
        # 25 líneas de query, mapeo de tuplas a dataclass, joins de asistentes...
        ...
```

### ✅ Inyección Eficiente (Esqueleto AST — 12 líneas / ~150 tokens):
```python
class SQLiteMeetingRepository:
    """Implementación SQLite del puerto MeetingRepository."""
    db_path: str
    def __init__(self, db_path: str) -> None: ...
    def get_by_code(self, code: str) -> Optional[Meeting]: ...
    def save(self, meeting: Meeting) -> None: ...
    def list_all(self) -> List[Meeting]: ...
```
*Ahorro del 87.5% de tokens manteniendo el 100% de la información arquitectónica requerida para deliberar, diseñar y especificar.*

---

## 4. Protocolo de Ejecución del Agente

1. **Antes de P04 / P06:**
   - Si `codegraph` está disponible, utilizar `codegraph_explore` para extraer únicamente los símbolos y dependencias relevantes.
   - Si no está disponible, utilizar búsquedas precisas de definiciones (`grep_search` con patrones `def `, `class `, `interface `) en lugar de leer archivos enteros.
2. **Prohibición de Volcados Ciegos:**
   - Queda estrictamente prohibido leer más de 3 archivos completos simultáneos durante las fases de diseño o propuesta.
3. **Registro en Flight Recorder:**
   - Cuando se realice un análisis basado en poda de contexto, registrar:
     `[STEP_ID] [AST_INDEX] [EXTRACTED] Skeletons parsed for <module_name> (reduced context footprint)`

---

## 5. Modos de Inclusión Condicional (Steering Inclusion Modes)

Para evitar inyectar directivas completas en cada turno de conversación, los archivos de directivas y reglas secundarias pueden declarar frontmatter YAML de inclusión condicional:

### 1. Inclusión Universal (`always` — por defecto):
```yaml
---
inclusion: always
---
```
Se inyecta en cada interacción del agente. Reservado para `CONSTITUTION.md` y reglas no negociables de arquitectura.

### 2. Inclusión Condicional por Patrón (`fileMatch`):
```yaml
---
inclusion: fileMatch
fileMatchPattern: ["**/*.html", "tools/q-cockpit/ui/**", "**/*.tsx"]
---
```
Se inyecta **únicamente cuando la tarea activa o los archivos abiertos coinciden con el patrón**. Si el agente trabaja en migraciones SQL o backend, las reglas de UI/CSS se omiten automáticamente, ahorrando tokens de inferencia y evitando el efecto *Lost in the Middle*.

Patrones comunes recomendados:
- `["**/storage/**", "**/db/**", "**/*.sql"]` $\to$ Reglas de persistencia, WAL mode y pooling.
- `["**/api/**", "**/handlers/**", "**/controllers/**"]` $\to$ Contratos REST/gRPC y códigos HTTP.
- `["**/*test*"]` $\to$ Reglas de TDD, aserciones y no uso de mocks permanentes.

### 3. Inclusión Manual (`manual`):
```yaml
---
inclusion: manual
---
```
Solo se carga cuando se referencia explícitamente mediante `#include <ruta>` o por invocación directa en el prompt.
