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

1. **Exploración Proporcional:** Antes de redactar la bitácora, explorar el código existente relevante utilizando `codegraph_explore` (si está disponible) o `ripgrep`/`fd`. Conocer los archivos existentes evita duplicar modelos o inventar rutas erróneas.
2. **Cero Burocracia Innecesaria:** Si el cambio es una corrección trivial de 1 solo archivo (<50 líneas), resolverla directamente inline sin crear artefactos durables. Si implica 2 o más pasos o componentes, la creación de la bitácora es obligatoria.
3. **Respeto a la Ruta del Motor:**
   - Si el Motor es Gentle-AI: Escribir en `odd/tasks/{{FEATURE_NAME}}.md` (y sincronizar con Engram si está disponible).
   - Si el Motor es Standalone: Escribir en `q-tasks/{{FEATURE_NAME}}.md`.

---

## 2. Estructura Obligatoria de la Bitácora

El archivo generado debe instanciar fielmente [`templates/task-log-template.md`](../templates/task-log-template.md) con las siguientes secciones:

### 2.1 Perspectiva de Product Manager (Lente BMAD / Squad Path)
- **User Persona & Dolor Actual:** ¿Quién sufre el problema hoy y cuál es el impacto de no resolverlo?
- **Historias de Usuario Ágiles (`US-01`, `US-02`):**
  - Formato: *Como [rol], quiero [acción], para [beneficio].*
  - **Criterio de Aceptación Observable (`UAC-01`, `UAC-02`):** La condición exacta, verificable desde la interfaz o el protocolo HTTP, que define el éxito de la historia.

### 2.2 Alcance y Restricciones Constitucionales (Artículo ARQ-01)
- Declarar explícitamente lo que entra en el cambio (**In Scope**) y lo que se difiere deliberadamente (**Out of Scope**).
- Confirmar el cumplimiento de las cláusulas aplicables:
  - *Cláusula 1:* Diseño en **Vertical Slice** autónomo.
  - *Cláusula 3:* Consultas directas sin hidratación redundante; SQLite WAL si aplica.
  - *Cláusula 4:* Higiene estricta; vistas en archivos `.html` independientes empaquetados (`//go:embed` o templates nativos). Cero HTML en strings de código.
  - *Cláusula 5:* 100% SQL parametrizado y escape XSS activo.

### 2.3 Desglose de Tareas Atómicas (~400 líneas / slice)
- Dividir la implementación en tareas coherentes acotadas a la heurística de ~400 líneas.
- Cada tarea debe tener un identificador estable (`TASK-01`, `TASK-02`) y estar asociada directamente a un `UAC`.
- Detallar los archivos a crear o modificar (handlers, queries/storage, plantillas).

### 2.4 Terminal Evidence Gate (Vacío Inicialmente)
- Incluir la tabla de verificación donde se registrarán obligatoriamente los comandos, códigos de salida y resultados observados en P06 antes de dar cualquier tarea por completada.

---

## 3. Notificación al Usuario

Al crear la bitácora, notificar al usuario en una sola línea clara y directa:

```text
📋 Bitácora creada en `<ruta-del-archivo>` con N tareas atómicas vinculadas a los criterios UAC.
```
