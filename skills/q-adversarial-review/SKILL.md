---
name: q:adversarial-review
description: "Trigger: /q-adversarial-review, /adversarial-review, revisión adversarial, auditor adversarial, gate adversarial, revisar diff limpio. Audita de manera independiente e implacable el código recién implementado en un slice vertical o tarea atómica antes de dar por buena la compuerta P06, ejecutándose en un subagente con contexto aislado (sin sesgo de auto-confirmación ni memoria previa), evaluando el git diff contra el Artículo ARQ-01, CONSTITUTION.md y los criterios UAC con memoria de hallazgos persistentes (Review Remembers)."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "2.0.0"
  date: "2026-10-07"
---

# q:adversarial-review v2.0 (Compuerta de Revisión Adversarial con Review Remembers)

## Goal
Eliminar el **sesgo de auto-confirmación** en el desarrollo asistido por IA mediante una compuerta adversarial rigurosa. Un subagente con **contexto limpio** (cero memoria del proceso de escritura) audita exclusivamente el `git diff` recién generado contra el **Artículo Constitucional ARQ-01**, las directrices de `CONSTITUTION.md` / `BLUEPRINT.md` y los criterios de aceptación (`UAC`) de la tarea, emitiendo un veredicto binario vinculante (`APPROVED` o `REJECTED`) con trazabilidad estricta de hallazgos en rondas sucesivas (**Review Remembers**).

---

## When to Use
- **En Paso 6 (Compuerta Dual):** Inmediatamente después de verificar que el código compila y pasa tests de máquina en P06, y **antes** de marcar cualquier checkbox `[x]` en la bitácora activa (`q-tasks/*.md` u `odd/tasks/*.md`).
- **En Cierre de Slice Vertical:** Al concluir un slice de ~400 LOC para certificar que no se introdujo deuda técnica, capas pasamanos o antipatrones.
- **En Re-Revisión tras Rebote:** Cuando un slice fue corregido y vuelve a revisión, evaluando qué hallazgos previos fueron realmente resueltos.
- **Bajo Demanda:** Cuando el usuario solicita `/adversarial-review` o revisar el trabajo reciente con ojos críticos e imparciales.

---

## Invariantes Operativos No Negociables

1. **Aislamiento Absoluto de Contexto (Context Isolation):**  
   El revisor adversarial **JAMÁS** debe ejecutarse en el mismo hilo de conversación donde el agente implementó el código. Debe ser despachado como un subagente independiente (`invoke_subagent` con rol `"Adversarial Architecture Reviewer"` y prompt acotado) que reciba únicamente:
   - El `git diff` del slice o tarea.
   - La tarea activa y sus criterios `UAC`.
   - `CONSTITUTION.md` y `BLUEPRINT.md` (o reglas de arquitectura del proyecto).
   - El reporte previo de revisión (si existe una ronda anterior).

2. **Rol de Auditor Implacable (Zero Empathy / Zero Assumption):**  
   El auditor no sabe cuánto esfuerzo costó escribir el código ni le importan las intenciones. Evalúa **únicamente hechos observables en el diff**. Si una función no tiene tests, si un endpoint concatena HTML, o si se creó una interfaz pasamanos sin justificación, el veredicto es `REJECTED`.

3. **Protocolo "Review Remembers" (Memoria de Hallazgos con IDs Estables):**  
   - En una primera revisión, cada objeción recibe un ID persistente: `R-01`, `R-02`, etc.
   - En rondas subsiguientes de re-revisión, el auditor **evalúa primero el estado de los IDs previos** antes de buscar nuevos defectos:
     * `[FIXED]`: Resuelto con evidencia verificable en `file:line`.
     * `[NOT_FIXED]`: No resuelto; mantiene el veredicto en `REJECTED`.
     * `[NO_LONGER_APPLIES]`: La arquitectura o código cambió y la objeción ya no aplica.
   - Si el nuevo diff introduce fallos adicionales, se agregan nuevos IDs (`R-03`, `R-04`).
   - El slice **SOLO** puede alcanzar `APPROVED` cuando el 100% de los `R-ids` previos están en `[FIXED]` o `[NO_LONGER_APPLIES]` y no existen nuevos blockers.

4. **Veredicto Vinculante y Bloqueo de Tarea:**  
   - Si el veredicto es `REJECTED`, el agente escritor **TIENE ESTRICTAMENTE PROHIBIDO** marcar la tarea como completada (`[x]`).
   - El agente escritor debe aplicar las correcciones mínimas requeridas.
   - El slice vuelve a pasar por P06 de máquina y luego nuevamente por la revisión adversarial con memoria hasta obtener `APPROVED`.

---

## Matriz de Verificación Adversarial (5 Ejes Críticos)

El auditor adversarial escanea el `git diff` bajo 5 ejes estrictos:

| Eje | Qué busca el Auditor | Criterio de Rechazo Inmediato (REJECTED) |
| :--- | :--- | :--- |
| **1. Mínima Indirección (ARQ-01)** | Interfaces pasamanos, adaptadores de una sola implementación, DTOs idénticos a modelos de dominio sin valor de transformación. | Creación de interfaces redundantes o capas intermedias que solo reenvían llamadas sin lógica. |
| **2. Higiene de Plantillas y Vistas** | Vistas web desacopladas en archivos `.html` empaquetados (`//go:embed`, Jinja2, templates limpios). | Strings con HTML embebido/concatenado directamente en archivos de backend/servidor. |
| **3. Ciberseguridad y Persistencia** | 100% de consultas a BD con placeholders preparados. WAL mode y busy_timeout configurados. | Concatenación o interpolación de strings (`fmt.Sprintf`, `f-strings`) dentro de queries SQL. |
| **4. Anti-Mocking & Integridad de Tests** | Tests con aserciones reales sobre comportamiento de dominio o endpoints. | Mocks estáticos hardcodeados en producción para engañar tests, aserciones vacías o `assert True`. |
| **5. Manejo de Errores y Robustez** | Errores manejados explícitamente y propagados con contexto. | Errores silenciados con `_ = err`, bloques `except: pass` sin log o fallbacks silenciosos. |

---

## Protocolo de Despacho e Invocación

### Paso 1: Extracción del Contexto Acotado (Agente Orquestador)
El orquestador extrae el diff y carga el reporte adversarial anterior (si existe):
```bash
git diff HEAD~1..HEAD  # o git diff origin/main..HEAD
```

### Paso 2: Despacho del Subagente Limpio
El orquestador invoca al subagente:
```text
invoke_subagent(
  role="Adversarial Architecture Reviewer",
  prompt="Actúa como Auditor Adversarial implacable bajo el Artículo ARQ-01.
          Audita el siguiente diff contra CONSTITUTION.md y los UAC de TASK-XX.
          Reporte previo (si existe): <PREVIOUS_REPORT>
          Diff: <DIFF_CONTENT>
          Emite veredicto: APPROVED o REJECTED con tabla Review Remembers (R-IDs) y hallazgos exactos."
)
```

### Paso 3: Evaluación del Veredicto
- **Si `APPROVED`:** El orquestador registra la aprobación en la bitácora activa y procede al cierre de la tarea.
- **Si `REJECTED`:** El orquestador reasigna el trabajo al escritor con la lista de hallazgos `R-XX` para subsanar los blockers.

---

## Formato Estándar del Veredicto Adversarial (con Review Remembers)

Todo reporte emitido por `q:adversarial-review` debe seguir esta estructura:

```markdown
### 🛡️ Adversarial Review Verdict: [APPROVED | REJECTED]

- **Slice / Tarea:** TASK-XX (<Nombre de la tarea>)
- **Ronda:** 2 (Re-Revisión)
- **Archivos auditados:** N archivos modificados (+X, -Y)

#### 📋 Review Remembers (Auditoría de Hallazgos Previos):
| ID | Archivo y Línea | Hallazgo Original | Estado | Evidencia |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | `internal/view/user.go:L45` | HTML concatenado en backend | `[FIXED]` | Movido a `templates/user.html` (L12) |
| **R-02** | `internal/repo/db.go:L88` | Query SQL con interpolación de strings | `[NOT_FIXED]` | Persiste `fmt.Sprintf` en L92 |

#### 🚨 Nuevos Hallazgos (Regresiones):
- [P0/Blocker] **R-03** `internal/handler/auth.go:L34`: Error de login silenciado con `_ = err`.

#### 🎯 Acción Requerida:
1. Subsanar **R-02** usando placeholders `?` o `$1` en la query SQL.
2. Subsanar **R-03** propagando el error con contexto HTTP 401.
3. Re-ejecutar P06 de máquina y solicitar nueva revisión adversarial.
```
