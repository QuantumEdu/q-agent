---
name: q:adversarial-review
description: "Trigger: /q-adversarial-review, /adversarial-review, revisión adversarial, auditor adversarial, gate adversarial, revisar diff limpio. Audita de manera independiente e implacable el código recién implementado en un slice vertical o tarea atómica antes de dar por buena la compuerta P06, ejecutándose en un subagente con contexto aislado (sin sesgo de auto-confirmación ni memoria previa), evaluando el git diff contra el Artículo ARQ-01, CONSTITUTION.md y los criterios UAC con memoria de hallazgos persistentes (Review Remembers)."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "2.1.0"
  date: "2026-10-10"
  context_policy: "FULL"
  requires: ["CONSTITUTION.md"]
  produces: ["Adversarial Review Verdict (Review Remembers)"]
---

# q:adversarial-review v2.1 — Compuerta Adversarial con Review Remembers

## 1. Quick Bootstrap & Triggers
- **Propósito**: Eliminar el sesgo de auto-confirmación en código generado. Un subagente con **contexto limpio** audita exclusivamente el `git diff` recién generado contra el **Artículo Constitucional ARQ-01**, `CONSTITUTION.md`, `BLUEPRINT.md` y criterios `UAC`.
- **Cuándo Aplica**:
  - En Paso 6 (Compuerta Dual), tras compilar y pasar tests de máquina en P06, antes de tachar `[x]`.
  - En cierre de Slice Vertical (~400 LOC) para certificar cero deuda técnica o capas pasamanos.
  - En re-revisión tras corrección de un slice rechazado previo.
  - Bajo demanda explícita del usuario (`/adversarial-review`).
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO escribir o editar código**: El auditor es estrictamente de solo lectura; no implementa fixes.
  - ⛔ **PROHIBIDO correr en el mismo hilo**: Jamás ejecutar en la sesión del agente escritor; requiere despacho aislado (`invoke_subagent`).
  - No usar si no hay `git diff` o código modificado para auditar.
- **Política de Contexto**: `FULL`. El auditor debe leer y evaluar los 5 ejes y la matriz de `R-IDs` completos antes de dictaminar.

## 2. Invariantes Operativos No Negociables
1. **Aislamiento Absoluto de Contexto (Context Isolation)**: Despachar vía `invoke_subagent` con rol `"Adversarial Architecture Reviewer"` inyectando únicamente: diff, criterios UAC, reglas constitucionales y reporte previo (si existe).
2. **Cero Empatía / Cero Supuestos**: Evaluar solo hechos observables en el diff. Sin tests reales, con HTML en backend o interfaces pasamanos = `REJECTED`.
3. **Protocolo Review Remembers**:
   - Cada objeción recibe un ID persistente: `R-01`, `R-02`, etc.
   - En re-revisiones, evaluar primero los IDs previos: `[FIXED]`, `[NOT_FIXED]`, `[NO_LONGER_APPLIES]`.
   - Veredicto `APPROVED` requiere 100% de los `R-IDs` en `[FIXED]` o `[NO_LONGER_APPLIES]`.
4. **Bloqueo Vinculante de Tarea**: Con `REJECTED`, el escritor tiene **prohibido** marcar la tarea como completada (`[x]`).

## 3. Matriz de Verificación Adversarial (6 Ejes Críticos)

| Eje | Qué busca el Auditor | Criterio de Rechazo Inmediato (REJECTED) |
| :--- | :--- | :--- |
| **1. Mínima Indirección (ARQ-01)** | Interfaces pasamanos, adaptadores 1-a-1, DTOs idénticos a modelos. | Interfaces redundantes o capas que solo reenvían llamadas sin lógica. |
| **2. Higiene de Plantillas** | Vistas en archivos `.html` empaquetados (`//go:embed`, Jinja2, templates). | HTML embebido o concatenado en archivos de backend/servidor. |
| **3. Ciberseguridad, BD & Tiempo** | 100% queries SQL parametrizadas. WAL mode y timeout configurados (`busy_timeout >= 10000`, `timeout=15.0`). Invariante UTC en fechas. Compare-and-Swap atómico en transiciones. | Concatenación en SQL; SQLite sin timeout; datetimes naive (`datetime.now()`); o transiciones de estado con `SELECT` previo en vez de CAS atómico. |
| **4. Anti-Mocking & Tests** | Aserciones reales sobre comportamiento de dominio o endpoints. | Mocks hardcodeados, tests vacíos o aserciones triviales tipo `assert True`. |
| **5. Manejo de Errores** | Errores manejados explícitamente y propagados con contexto. | Errores silenciados con `_ = err`, `except: pass` o fallbacks silenciosos. |
| **6. Manifiesto & Grounding Empírico** | Todos los entregables especificados creados en disco (`test -s`). Afirmaciones de compatibilidad/negocio contrastadas contra DB o logs reales. | Entregables referenciados en texto pero no creados físicamente; suposiciones heurísticas sin evidencia de consulta a la base de datos o logs. |

## 4. Contrato de Ejecución & Despacho
- [ ] **M1 (Extracción)**: El orquestador extrae el diff (`git diff origin/main..HEAD` o `git diff HEAD~1..HEAD`) y carga reporte previo si existe.
- [ ] **M2 (Despacho)**: Invocar `invoke_subagent(role="Adversarial Architecture Reviewer", prompt="...")`.
- [ ] **M3 (Evaluación Remembers)**: El subagente evalúa los `R-IDs` previos y escanea los 5 ejes contra regresiones.
- [ ] **M4 (Emisión de Reporte)**: Emitir veredicto estructurado con tabla de hallazgos.

## 5. Completion Gate
Antes de que el orquestador acepte el veredicto:
- [ ] Todos los `R-IDs` previos están catalogados con estado verificable en `file:line`.
- [ ] Veredicto final declarado explícitamente como:
  - `[APPROVED]` ──► Autoriza marcar `[x]` en la bitácora activa y registrar evidencia.
  - `[REJECTED]` ──► Bloquea cierre; devuelve lista de `R-IDs` pendientes al implementador.
- [ ] Taxonomía de gate registrada: `[COMPLETE]` (si Approved), `[BLOCKED - reason]` (si Rejected).

## 6. Formato Estándar del Veredicto
```markdown
### 🛡️ Adversarial Review Verdict: [APPROVED | REJECTED]
- **Slice / Tarea:** TASK-XX (<Nombre>) | **Ronda:** N
- **Archivos auditados:** N modificados (+X, -Y)

#### 📋 Review Remembers:
| ID | Archivo:Línea | Hallazgo Original | Estado | Evidencia |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | `internal/view/user.go:L45` | HTML en backend | `[FIXED]` | Movido a `templates/user.html` |
| **R-02** | `internal/repo/db.go:L88` | SQL interpolado | `[NOT_FIXED]` | Persiste `fmt.Sprintf` en L92 |

#### 🚨 Nuevos Hallazgos / Bloqueos:
- [P0/Blocker] **R-03** `internal/handler/auth.go:L34`: Error silenciado con `_ = err`.

#### 🎯 Acción Requerida:
1. Subsanar R-02 y R-03 antes de re-intentar P06.
```
