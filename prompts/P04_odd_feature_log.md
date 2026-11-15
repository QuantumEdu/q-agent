---
id: P4_ODD_FEATURE_LOG
titulo: "Apertura de Bitácora Única ODD — Fusión de Lente BMAD, Trazabilidad y Tareas Atómicas"
cuando_usar: "Al iniciar cualquier cambio o nueva funcionalidad autorizada por el usuario."
prerequisitos: "Gate P03 aprobado (motor seleccionado), CONSTITUTION.md vigente."
entregables: "Bitácora única en `q-tasks/{{FEATURE_NAME}}.md` o `odd/tasks/{{FEATURE_NAME}}.md`"
posicion_en_pipeline: "Paso 4 — Bitácora Viva Unificada"
proyecto: "{{PROYECTO_NOMBRE}}"
fecha: "{{YYYY-MM-DD}}"
---

# P4 — Apertura de Bitácora Única ODD (Organic Feature Log)

> **Misión:** Eliminar el desperdicio de tokens y la burocracia documental de los antiguos pasos de propuesta, especificación y tareas independientes. Se crea un **único documento vivo** basado en `templates/task-log-template.md` que unifica el rigor de negocio (Historias de Usuario BMAD) con la trazabilidad técnica y el checklist de implementación.

---

## 1. Reglas Operativas Previas a la Escritura

Aplicar el [contrato de comunicación](../references/communication-contract.md) y la
[guía canónica](../docs/communication-policy.md). La bitácora activa es autoridad
de alcance, estado de tareas, aceptación y decisiones. Los informes enlazan evidencia,
no mantienen estados competidores. Reutilizar decisiones y autoridad ya establecidas.

1. **Exploración con CodeGraph e Impact Gate:** Antes de redactar la bitácora, verificar el índice del repositorio con `test -d .codegraph || codegraph init -y`. Explorar los símbolos existentes vía MCP `codegraph_explore` o CLI (`codegraph explore -p <root> "<query>"`). Evaluar el blast radius del cambio con `codegraph impact <symbol>` para asegurar que el alcance se mantenga como Vertical Slice cohesiva sin efectos colaterales no mapeados. Cero adivinación de rutas o firmas.
2. **Criterio de Sizing (Resume Test):** Si el cambio es una corrección o adición entendida dentro del presupuesto de evidencia inline (≤3 llamadas / ~10k tokens), con riesgo acotado (sin DDL, dinero ni auth compleja) y que un desarrollador podría terminar únicamente viendo el pedido y el `git diff` si la sesión se corta, resolverla directamente inline vía Fast-Track (Plan F) sin crear bitácora. La bitácora viva es obligatoria solo para tareas GRANDES que fallan el Resume Test.
3. **Respeto a la Ruta del Motor:**
   - Si el Motor es Gentle-AI: Escribir en `odd/tasks/{{FEATURE_NAME}}.md`; un espejo externo requiere autorización independiente, no solo disponibilidad.
   - Si el Motor es Standalone: Escribir en `q-tasks/{{FEATURE_NAME}}.md`.

---

## 2. Estructura Obligatoria de la Bitácora

El archivo generado debe instanciar fielmente [`templates/task-log-template.md`](../templates/task-log-template.md) con las siguientes secciones:

### 2.1 Especificaciones Constitucionales (S# — Mandato Spec by Reference)
- Transcribir de forma textual y numerada (`S-01`, `S-02`) los requerimientos, strings exactos y códigos de error del usuario sin parafrasear.
- Al delegar a subagentes o worktrees aislados, el handoff cita esta fuente directa (`Spec: q-tasks/{{FEATURE_NAME}}.md, TASK-XX, S-01`).
- Los subagentes leen la bitácora directamente hasta `## Log`, eliminando el sesgo de reinterpretación.

### 2.2 Perspectiva de Product Manager (Lente BMAD / Squad Path)
- **User Persona & Dolor Actual:** ¿Quién sufre el problema hoy y cuál es el impacto de no resolverlo?
- **Historias de Usuario Ágiles (`US-01`, `US-02`):**
  - Formato: *Como [rol], quiero [acción], para [beneficio].*
  - **Criterio de Aceptación Observable (`UAC-01`, `UAC-02`):** La condición exacta, verificable desde la interfaz o el protocolo HTTP, que define el éxito de la historia (vinculada a `S#`).

### 2.3 Alcance y Restricciones Constitucionales (Artículo ARQ-01)
- Declarar explícitamente lo que entra en el cambio (**In Scope**) y lo que se difiere deliberadamente (**Out of Scope**).
- Confirmar el cumplimiento de las cláusulas aplicables:
  - *Cláusula 1:* Diseño en **Vertical Slice** autónomo.
  - *Cláusula 3:* Consultas directas sin hidratación redundante; SQLite WAL si aplica.
  - *Cláusula 4:* Higiene estricta; vistas en archivos `.html` independientes empaquetados (`//go:embed` o templates nativos). Cero HTML en strings de código.
  - *Cláusula 5:* 100% SQL parametrizado y escape XSS activo.

### 2.4 Desglose de Tareas Atómicas en Oleadas (~400 líneas / slice)
- Dividir la implementación en tareas coherentes acotadas a la heurística de ~400 líneas, organizadas en **Oleadas (Waves)**:
  - **Wave 1 (Sin dependencias):** Esquemas, contratos, entidades de dominio y tests en rojo (`RED_FAIL`).
  - **Wave 2 (Dependientes de W1):** Casos de uso, servicios de aplicación y adaptadores.
  - **Wave 3 (Dependientes de W2):** Controladores HTTP, endpoints, vistas `.html` empaquetadas e integración UI.
- Cada tarea debe tener un identificador estable (`TASK-01`), estar asociada a `S#` y `UAC`, declarar su Wave y **declarar su Ruta de ejecución**:
  - `Ruta: inline` (ejecutada en hilo principal por el orquestador).
  - `Ruta: delegated` (aislada en `.q-worktrees/task-XX` justificada por paralelismo de superficies disjuntas o backstop de sesión).
- Al ser completada y verificada, cada tarea se sella vinculando su commit convencional atómico: `- [x] TASK-01 (Commit: <sha>) ...`.

### 2.5 Terminal Evidence Gate & Spec-Derived Probes (Vacío Inicialmente)
- Incluir la tabla de verificación (con columna `Wave`) donde se registrarán obligatoriamente los comandos, códigos de salida y resultados observados en P06 antes de dar cualquier tarea por completada.
- Exigir **Spec-Derived Probes**: formulación de pruebas independientes basadas en `S#` ejecutadas en aislamiento para comprobar casos frontera e invariantes de estado.

### 2.6 Log de Cambios y Correcciones (L#)
- Sección final que registra el requerimiento inicial del usuario de forma textual (`L1`).
- Cualquier ajuste, corrección o aclaración del usuario durante el ciclo se anexa como `L2...`, actualizando solo el `S#` afectado sin destruir el documento.

---

## 3. Registro y Atención Condicional

Always record log creation and its path using the existing log/event mechanism.
Chat only for `actionable_result`, `blocking_decision`, `hard_stop`, or a user status
request. Routine creation alone is not a notification. If scope/UAC need a decision,
ask one focused unresolved question then STOP; do not reopen settled approvals.
For a warranted message use the contract's actor/time prefix with this content:

```text
📋 Bitácora creada en `<ruta-del-archivo>` con N tareas atómicas vinculadas a los criterios UAC.
```
