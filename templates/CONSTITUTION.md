# CONSTITUTION.md
Proyecto: [nombre]
Versión: [N]
Creado: [fecha P1 inicial]
Última sync: [fecha P1.5 más reciente]
Hash base sync: [git hash]

---

## 1. IDENTIDAD ARQUITECTÓNICA Y ARTÍCULO ARQ-01

- **Patrón principal:** [Vertical Slice Architecture / Hexagonal Condicional / Clean Architecture]
- **Patrones complementarios:** [lista]
- **Stack core:** [tecnologías + versiones]
- **Paradigma:** [Modular / Event-driven / CQRS / etc.]

### ⚖️ ARTÍCULO ARQ-01: POLÍTICA SUPREMA DE ARQUITECTURA Y CONSTRUCCIÓN DE SOFTWARE

> **Mandato Constitucional:** Toda decisión de diseño, estructura de carpetas, código fuente y auditoría en este proyecto está subordinada al cumplimiento estricto de las siguientes 6 cláusulas.

#### Cláusula 1: Vertical Slices por Defecto (Mínima Indirección)
Toda funcionalidad estándar (CRUD, listados, formularios, reportes, integraciones) debe implementarse como un **Slice Vertical Autónomo** que contenga su modelo de almacenamiento, lógica operativa, endpoint/handler y presentación en un único módulo cohesivo. Quedan terminantemente prohibidas las capas intermedias artificiales (servicios de pasamano, interfaces de una sola implementación o DTOs redundantes) en operaciones directas.

#### Cláusula 2: Umbral de Dominio Rico (Hexagonal Condicional)
Solo se autoriza la creación de capas de dominio aisladas (`domain/`, `ports/`, `usecases/`) cuando el módulo supere el **Umbral de Alta Complejidad**:
- Más de 15 reglas de negocio interdependientes.
- Máquinas de estado multifase con transiciones complejas.
- Motores de cálculo financiero, actuarial o algorítmico sensible.
*Si el módulo no supera este umbral, aplicar Cláusula 1.*

#### Cláusula 3: Persistencia Pragmática y Resiliencia
- Las lecturas, proyecciones y agregaciones para la interfaz de usuario se consultan directamente contra el motor de almacenamiento optimizado, sin forzar la hidratación de modelos de dominio intermediarios.
- **Invariante SQLite y Concurrencia (si aplica):** Toda conexión SQLite debe operar obligatoriamente con `_journal_mode=WAL`, `_busy_timeout=10000` (o `timeout=15.0`), `_synchronous=NORMAL` y un pool de conexiones controlado (1 writer para prevenir `database is locked`). Para transiciones o reclamo de registros concurrentes, usar transacciones atómicas compare-and-swap (`UPDATE ... WHERE id = ? AND status = '...'` verificando `cursor.rowcount == 1`), nunca comprobaciones previas tipo `SELECT` seguidas de `UPDATE`.
- **Invariante Temporal UTC:** Toda manipulación, almacenamiento o comparación de timestamps debe realizarse de forma estricta en tiempo universal coordinado consciente de zona horaria (`datetime.now(timezone.utc)` en Python o ISO 8601 con sufijo `+00:00`/`Z`), quedando terminantemente prohibido el uso de fechas ingenuas (naive) que originen excepciones de comparación.

#### Cláusula 4: Higiene de Plantillas y Separación de Presentación
Queda estrictamente prohibido construir interfaces o fragmentos HTML/CSS mediante concatenación de cadenas en archivos de código fuente.
- Toda vista debe residir en archivos `.html` independientes y legibles.
- Los archivos de vista deben ser empaquetados o gestionados nativamente por el stack (`//go:embed` en Go, motores de plantillas como Jinja2 en Python, o componentes TSX/JSX en TypeScript/Node).

#### Cláusula 5: Ciberseguridad Mandatoria & Zero Trust
- **100% de consultas SQL parametrizadas:** Prohibida la interpolación de cadenas (`fmt.Sprintf`, f-strings, template literals) en consultas a bases de datos.
- **Prevención de XSS:** Todo renderizado de datos dinámicos en HTML debe utilizar escape contextual automático.
- **Zero Secrets:** Prohibido el almacenamiento de credenciales, API keys o tokens en el código fuente.

#### Cláusula 6: Criterio de Auditoría Arquitectónica, Anti-Mocking y Evidencia de Entidades
Las auditorías de calidad (P01, P09, `q-audit-readonly`):
- Auditarán el estricto cumplimiento de las Cláusulas 1 a 5 y los Criterios de Aceptación (UAC).
- **Prohibido penalizar la ausencia de capas horizontales vacías.**
- **Tolerancia Cero a Fake Completions:** Todo checkbox marcado (`[x]`) debe estar respaldado por evidencia observable en terminal (código de salida 0, tests verdes, HTTP status). Mocks estáticos que simulen persistencia sin autorización explícita constituyen una falla crítica (`❌ Gap P0`).
- **Regla de Citación Estricta de Claves Primarias (Strict Primary Key & Citation Grounding Invariant):** Al auditar o referenciar bases de datos, incidentes, configuraciones, contratos o evidencia forense, es mandatorio citar explícitamente el identificador de fila, clave primaria o ancla unívoca (`<tabla>.<pk> = <id>`, `config_id`, `ticket_id`, `clause_number`, `cve_id`, o timestamp exacto) junto con los valores semánticos; omitir el ID formal invalida la trazabilidad y la validez empírica de la evidencia.
- **Manifiesto Estricto de Entregables (Anti-Truncamiento):** Si una tarea o especificación requiere múltiples artefactos (código, migraciones, scripts, reportes, diagramas), queda terminantemente prohibido marcar la tarea como concluida o referenciar entregables no generados. Todos y cada uno de los artefactos solicitados deben existir físicamente en disco y no estar vacíos (`test -s <archivo>`).
- **Validación Estructural de Entregables No-Código (Structured Deliverable Verification):** Para entregables de ofimática o formatos compuestos no planos (`.docx`, `.xlsx`, `.pptx`), no basta con comprobar la mera existencia de archivo. El artefacto debe ser verificado estructuralmente (mediante `tools/q-inspect/q_inspect.py` o inspección zero-dep): confirmando que el archivo es un contenedor ZIP íntegro, que su estructura interna XML (`word/document.xml`) es válida, que contiene el cuerpo textual mínimo esperado y que carece de marcadores de posición sin rellenar (`TODO`, `NaN`, `undefined`, `[Insert]`, etc.).
- **Empirical Grounding First & Jerarquía de Verdad:** Toda aseveración técnica, cálculo de compatibilidad, regla de negocio o diagnóstico debe contrastarse directamente contra las fuentes de datos empíricas provistas. Ante cualquier discrepancia, rige la **Jerarquía Estricta de Verdad**:
  $$\text{Bases de Datos y Logs Locales} > \text{Archivos de Configuración del Repo} > \text{Documentación Provista} > \text{Conocimiento Previo del LLM}$$
  Queda prohibido asumir datos o compatibilidades apoyándose en heurísticas previas del modelo si contradicen o no fueron verificadas en los registros empíricos.
- **Anclaje Explícito de Taxonomías y Estándares:** En reportes de seguridad, cumplimiento normativo y auditorías forenses, es obligatorio fijar y citar la versión exacta del estándar utilizado (ej. MITRE ATT&CK Enterprise v14, OWASP Top 10 2021, NIST CSF 2.0), prohibiendo clasificaciones ambiguas o el uso de versiones obsoletas sin equivalencia explícita.
- **Andamio Modular de Habilidades On-Demand (On-Demand Skill Elicitation Pattern):** Queda prohibido saturar el contexto raíz del agente o del orquestador inyectando extensos bloques procedimentales de dominio (>30-50 líneas) directamente en los prompts de sistema o tareas primarias. Cuando una tarea requiera una metodología de dominio especializada (ej. revisión contractual multifase, análisis de markup, ingeniería inversa forense, o auditoría estricta de cumplimiento), debe estructurarse o aislarse como una habilidad modular bajo demanda (`skills/<dominio>/SKILL.md` o directiva acotada en disco), invocándose únicamente mediante un disparador explícito y conciso. El contexto raíz preserva únicamente el objetivo, las restricciones cardinales y el disparador de la habilidad.
- **Higiene de Almacenamiento Sandbox CLI (`.scratch/` vs. `/tmp`):** Todo script efímero de inspección, binario compilado temporal, extracción intermedia o volcado de datos generado durante la ejecución autónoma de una tarea debe alojarse obligatoriamente dentro del directorio local del workspace `.scratch/` (o `.tmp/` del repositorio, debidamente ignorado en `.gitignore`), quedando terminantemente prohibido escribir en rutas globales del sistema como `/tmp`, `/var/tmp` o directorios absolutos no confinados que puedan ser bloqueados por el sandbox o eliminados arbitrariamente por el sistema operativo.

---

## 2. BOUNDED CONTEXTS Y SLICES VERTICALES

### Mapa de dominios / módulos

| Context / Slice | Owns (entidades / tablas) | No toca | Estado |
|---|---|---|---|
| Auth | User, Session, Permission | Entidades operativas de negocio | [VIGENTE] |
| Reuniones (Ejemplo) | Meeting, Participant, Minute | User interno, Facturación | [VIGENTE] |
| Acuerdos (Ejemplo) | Agreement, FollowUp, Improvement | Catálogos globales | [VIGENTE] |

### Contratos entre Contexts / Slices

Cada contrato es un acuerdo explícito. Cambiar un contrato requiere un ADR nuevo y actualización de los slices afectados.

[Context A] ──► [Context B]
- Contrato: `NombreEventoOCall(params)`
- Dirección: Context A emite, Context B consume
- Mecanismo: [In-process Call / Event / Interfaz pública del slice]
- Estado: [VIGENTE]

### Regla de violación de frontera

> Ningún Context o Slice accede directamente a detalles privados internos de otro Context. Solo se comunican a través de contratos públicos declarados arriba.

---

## 3. DECISIONES ARQUITECTÓNICAS ACTIVAS (ADRs)

| ADR | Decisión | Cláusula ARQ-01 | Estado | Fecha |
|---|---|---|---|---|
| ADR-001 | Adopción de Vertical Slice Architecture para módulos CRUD | Cláusula 1 | [VIGENTE] | 2026-09 |
| ADR-002 | Concurrencia SQLite WAL con 1 writer pool | Cláusula 3 | [VIGENTE] | 2026-09 |
| ADR-003 | Higiene de plantillas empaquetadas vía //go:embed | Cláusula 4 | [VIGENTE] | 2026-09 |

---

## 4. NFRs DECLARADAS

| NFR | Mecanismo | Cómo se verifica | Estado |
|---|---|---|---|
| Tiempo de respuesta p95 < 200ms | Queries optimizadas / SQLite WAL | Benchmark en CI / Terminal | [VIGENTE] |
| Cero inyecciones SQL | Sentencias preparadas mandatorias | Linter / Auditoría estática | [VIGENTE] |
| Cero vulnerabilidades XSS | Template engine con auto-escape | Auditoría / Tests E2E | [VIGENTE] |
| Zero secrets en código | Pre-commit hook / grep de tokens | CI gate | [VIGENTE] |

---

## 5. CONVENCIONES DE CÓDIGO Y NOMENCLATURA

- Nomenclatura de Slices: `features/<nombre-slice>/` (handler, storage, views).
- Nombres de archivos de vistas: `<entidad>_<accion>.html` (ej. `reunion_list.html`).
- Tests atómicos: Todo slice debe tener un test de integración o contrato observable.

---

## 6. SYNC LOG

[Generado automáticamente por P1.5 / P07 — no editar manualmente]
