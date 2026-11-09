---
name: q:design-review
description: "Trigger: /q-design-review, /design-review, revisión de diseño, ojos frescos, goldfish, revisar diseño, design review. Revisión de un documento de diseño con ojos frescos (idea Goldfish adaptada de EGM de Google): un subagente aislado recibe SOLO el diseño + el código referenciado, sin el historial de la conversación, y lo audita con tres lentes (crítica de diseño, estructura, preparación para implementar). Hallazgos con R-IDs de Review Remembers. Enganche: Paso 3 (gate de meta-orquestación)."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "1.0.0"
  date: "2026-11-08"
  context_policy: "FULL"
  requires: ["design document (draft)"]
  produces: ["Design Review Verdict (Review Remembers)"]
---

# q:design-review v1.0 — Revisión de Diseño con Ojos Frescos (Goldfish)

> **Origen de la idea:** el modelo Elephant-Goldfish (EGM) de Google
> (Apache-2.0, https://github.com/google/elephant-goldfish-model).
> Aquí se portan **ideas**, no el plugin: la revisión con contexto limpio
> y las tres lentes de revisor, adaptadas a q-agent y a Review Remembers.
> Ver `ATTRIBUTION.md`. Lo que NO se portó: el plugin EGM completo, sus
> skills de draft/bootstrap ni su instalador.

## 1. Quick Bootstrap & Triggers
- **Propósito**: Cazar supuestos no dichos, huecos y riesgos en un diseño
  **antes** de escribir código, con un lector que no participó en
  escribirlo. El autor del diseño siempre es ciego a sus propios supuestos;
  un subagente fresco no lo es.
- **Cuándo Aplica**:
  - En Paso 3 (Gate de Meta-Orquestación), después del descubrimiento
    socrático y antes de abrir la bitácora (Fase II).
  - Cuando un diseño llega de fuera (EGM, un documento, otro equipo) y va
    a entrar como insumo a un Plan A/B.
  - Bajo demanda explícita (`/q-design-review <documento>`).
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO revisar código**: para código existe
    `q-adversarial-review` (Paso 6). Esta skill revisa **documentos**.
  - ⛔ **PROHIBIDO ejecutar en el mismo hilo**: jamás revisar en la
    sesión que escribió el diseño; requiere despacho aislado.
  - ⛔ **PROHIBIDO simular ojos frescos**: si el runtime no puede crear
    un subagente con contexto limpio, la skill **falla con mensaje claro**
    y no emite veredicto. Una revisión con el mismo contexto es teatro.
  - No usar en Plan F (Fast-Track, ≤3 archivos): el costo supera el valor.

## 2. Invariantes Operativos No Negociables
1. **Aislamiento Goldfish**: el revisor recibe únicamente: el documento de
   diseño, los archivos de código que el documento referencia
   explícitamente y el estándar contra el que se audita (ARQ-01,
   CONSTITUTION.md, criterios UAC). Nada del historial de la conversación,
   nada de lo que el autor "quiso decir".
2. **Solo lectura**: el revisor no edita el diseño ni el código. Emite
   hallazgos; el orquestador decide.
3. **Protocolo Review Remembers** (igual que `q-adversarial-review`):
   cada hallazgo recibe un ID persistente `R-01`, `R-02`, etc. En
   re-revisiones se evalúan primero los IDs previos: `[FIXED]`,
   `[NOT_FIXED]`, `[NO_LONGER_APPLIES]`. Veredicto `APPROVED` exige 100%
   de los R-IDs en `[FIXED]` o `[NO_LONGER_APPLIES]`.
4. **La revisión no reemplaza tests ni juicio humano**: un diseño
   aprobado aquí sigue pasando por TDD, compuerta dual y merge gate.

## 3. Las Tres Lentes (adaptadas de EGM)
| Lente (idea EGM) | Qué busca | Rechazo inmediato (Blocker) |
| :--- | :--- | :--- |
| **Crítica de diseño** (`design_critic`) | Supuestos sin justificar, riesgos no mitigados, cuellos de botella, costos/cuotas sin estimar. | Una afirmación sobre comportamiento, rendimiento o seguridad sin justificación ni mitigación. |
| **Estructura** (`structural`) | Secciones obligatorias presentes, jerarquía de encabezados lógica, formato y enlaces válidos. | Falta una sección obligatoria del estándar (objetivo, alcance, riesgos, plan de verificación) o la jerarquía salta niveles. |
| **Preparación para implementar** (`implementation_readiness`) | Cada paso accionable: qué archivo, qué cambio, qué test. Nada de "actualizar el servicio de auth" sin detalle. | Un paso que obliga al implementador a tomar una decisión de diseño no documentada (tipo de BD, firma de API, estrategia de errores, migración). |

## 4. Contrato de Ejecución & Despacho
- [ ] **M1 (Extracción)**: el orquestador extrae el diseño y la lista de
      archivos referenciados. Si un archivo referenciado no existe en
      disco, se registra como hallazgo (ver `tools/q-drift/`).
- [ ] **M2 (Capacidad)**: verificar que el runtime puede despachar un
      subagente con contexto fresco. Si no puede, emitir:
      `[ABORTED - no fresh-subagent support]` y parar. No veredicto.
- [ ] **M3 (Despacho)**: invocar el subagente con rol
      `"Design Review Goldfish"` y las tres lentes. Una lente por
      revisor cuando el runtime lo permita; si no, un solo revisor
      con las tres lentes en orden.
- [ ] **M4 (Veredicto)**: emitir el veredicto estructurado (sección 6).
      Con `REJECTED`, el diseño vuelve al autor con los R-IDs; el Paso 3
      no se marca `[x]`.

## 5. Completion Gate
- [ ] Todos los R-IDs previos catalogados con estado verificable.
- [ ] Veredicto declarado explícitamente:
  - `[APPROVED]` ──► autoriza abrir la bitácora (Fase II).
  - `[REJECTED]` ──► bloquea el Paso 3; devuelve R-IDs pendientes.
  - `[ABORTED - no fresh-subagent support]` ──► sin veredicto; el
    orquestador registra la limitación y decide si sigue sin esta revisión.
- [ ] Taxonomía registrada: `[COMPLETE]` o `[BLOCKED - reason]`.

## 6. Formato Estándar del Veredicto
```markdown
### 🔍 Design Review Verdict: [APPROVED | REJECTED | ABORTED]
- **Diseño:** docs/designs/<nombre>.md | **Ronda:** N
- **Lentes aplicadas:** crítica / estructura / preparación

#### 📋 Review Remembers:
| ID | Diseño:línea | Hallazgo Original | Estado | Evidencia |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | `designs/x.md:L12` | Supuesto sin justificar: "la BD soporta 10k QPS" | `[NOT_FIXED]` | Sin benchmark ni cita |

#### 🚨 Nuevos Hallazgos:
- [Blocker] **R-02** `designs/x.md:L40`: paso "migrar usuarios" sin plan de rollback.

#### 🎯 Acción Requerida:
1. Subsanar R-01 y R-02 antes de re-intentar el Paso 3.
```
