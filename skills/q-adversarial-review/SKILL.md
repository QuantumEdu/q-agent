---
name: q:adversarial-review
description: "Trigger: /q-adversarial-review, /adversarial-review, revisión adversarial, auditor adversarial, gate adversarial, revisar diff limpio. Audita de manera independiente e implacable el código recién implementado en un slice vertical o tarea atómica antes de dar por buena la compuerta P06, ejecutándose en un subagente con contexto aislado (sin sesgo de auto-confirmación ni memoria previa), evaluando el git diff contra el Artículo ARQ-01, CONSTITUTION.md y los criterios UAC."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "1.0.0"
  date: "2026-09-25"
---

# q:adversarial-review v1.0 (Compuerta de Revisión Adversarial Aislada)

## Goal
Eliminar el **sesgo de auto-confirmación** en el desarrollo asistido por IA mediante una compuerta adversarial rigurosa. Un subagente con **contexto limpio** (cero memoria del proceso de escritura) audita exclusivamente el `git diff` recién generado contra el **Artículo Constitucional ARQ-01**, las directrices de `CONSTITUTION.md` / `BLUEPRINT.md` y los criterios de aceptación (`UAC`) de la tarea, emitiendo un veredicto binario vinculante (`APPROVED` o `REJECTED`).

---

## When to Use
- **En Paso 6 (Compuerta Dual):** Inmediatamente después de verificar que el código compila y pasa tests de máquina en P06, y **antes** de marcar cualquier checkbox `[x]` en la bitácora activa (`q-tasks/*.md` u `odd/tasks/*.md`).
- **En Cierre de Slice Vertical:** Al concluir un slice de ~400 LOC para certificar que no se introdujo deuda técnica, capas pasamanos o antipatrones.
- **Bajo Demanda:** Cuando el usuario solicita `/adversarial-review` o revisar el trabajo reciente con ojos críticos e imparciales.

---

## Invariantes Operativos No Negociables

1. **Aislamiento Absoluto de Contexto (Context Isolation):**  
   El revisor adversarial **JAMÁS** debe ejecutarse en el mismo hilo de conversación donde el agente implementó el código. Debe ser despachado como un subagente independiente (`invoke_subagent` con rol `"Adversarial Architecture Reviewer"` y prompt acotado) que reciba únicamente:
   - El `git diff` del slice o tarea.
   - La tarea activa y sus criterios `UAC`.
   - `CONSTITUTION.md` y `BLUEPRINT.md` (o reglas de arquitectura del proyecto).

2. **Rol de Auditor Implacable (Zero Empathy / Zero Assumption):**  
   El auditor no sabe cuánto esfuerzo costó escribir el código ni le importan las intenciones. Evalúa **únicamente hechos observables en el diff**. Si una función no tiene tests, si un endpoint concatena HTML, o si se creó una interfaz pasamanos sin justificación, el veredicto es `REJECTED`.

3. **Veredicto Vinculante y Remediation Loop:**  
   - Si el veredicto es `REJECTED`, el agente escritor **TIENE PROHIBIDO** marcar la tarea como completada (`[x]`).
   - El agente escritor debe aplicar las correcciones mínimas requeridas.
   - El slice vuelve a pasar por P06 de máquina y luego nuevamente por la revisión adversarial hasta obtener `APPROVED`.

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
El orquestador extrae el diff y prepara el paquete de auditoría:
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
          Diff: <DIFF_CONTENT>
          Emite veredicto: APPROVED o REJECTED con lista de hallazgos exactos (archivo, línea, causa)."
)
```

### Paso 3: Evaluación del Veredicto
- **Si `APPROVED`:** El orquestador registra la aprobación en la bitácora activa y procede al cierre de la tarea.
- **Si `REJECTED`:** El orquestador reasigna el trabajo al escritor con la lista de hallazgos para subsanar los blockers.

---

## Formato Estándar del Veredicto Adversarial

Todo reporte emitido por `q:adversarial-review` debe seguir esta estructura:

```markdown
### 🛡️ Adversarial Review Verdict: [APPROVED | REJECTED]

- **Slice / Tarea:** TASK-XX (<Nombre de la tarea>)
- **Archivos auditados:** N archivos modificados (+X, -Y)

#### Hallazgos:
- [P0/Blocker] `path/to/file.ext:L45`: Violación de Higiene de Plantillas — HTML concatenado en función Go.
- [P1/Warning] `path/to/repo.go:L112`: Query SQL sin log de contexto en fallo de conexión.

#### Acción Requerida:
1. Mover el fragmento HTML a `templates/component.html`.
2. Re-ejecutar P06 de máquina y solicitar nueva revisión adversarial.
```
