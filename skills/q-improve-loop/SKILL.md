---
name: q-improve-loop
description: "Bucle iterativo de auditoría, compresión semántica y reescritura accionable de skills bajo rúbrica de calidad 1 a 5 y contratos deterministas."
triggers: "/q-improve-loop, /improve-skill, review and improve skill, auditar skill, optimizar skill, mejorar skill, refactor skill"
version: 1.2.0
license: Apache-2.0
metadata:
  author: "QuantumEdu"
  date: "2026-08-20"
  updated_at: "2026-11-08"
  context_policy: COMPACT
  requires: []
  may_call: [q-special-instruction]
  produces: [skill-audit, rewritten-skill, review-report]
---

# q-improve-loop · Iterative Skill Refactor & Quality Optimization

> **Propósito**: Auditar, comprimir y reescribir cualquier habilidad (`SKILL.md`) del sistema para maximizar su densidad de valor, eliminar la ambigüedad operativa, inyectar ejemplos concretos y garantizar una calificación $\ge 4$ bajo rúbrica estricta como condición necesaria — no suficiente — para persistir. La aprobación final la da una verificación externa (§4), nunca la propia nota.

---

## 1. Bootstrap & Scope

### Cuándo Usar
- Auditoría o refactorización de skills existentes con texto redundante, instrucciones difusas o falta de ejemplos.
- Optimización de presupuesto de contexto (reducción de tokens y eliminación de párrafos pasivos).
- Adición de contratos formales de activación (`triggers:`), pre-flight checks y Completion Gates deterministas.
- Invocación explícita mediante `/q-improve-loop` o solicitudes como *"mejora este skill"*, *"audita la habilidad"*.
- Aplicación de propuestas de `q-skill-doctor` con evidencia (el doctor mide y propone; este loop reescribe).

### Cuándo NO Usar
- Creación de skills completamente nuevos desde cero (usar `q-special-instruction`).
- Corrección de bugs en código de aplicación o pruebas rotas en repositorios (usar `q-ci-fixer`).
- Modificación de directivas globales de workspace (`AGENTS.md`) sin intención de optimizar una habilidad específica.

---

## 2. Invariantes de Calidad Operativa

Toda reescritura de un skill debe satisfacer cuatro estándares no-negociables:

1. **Accionabilidad Específica**: Cada instrucción debe ser un mandato técnico que el agente pueda ejecutar sin inferencias ambiguas ni preguntas innecesarias.
2. **Ejemplos Concretos por Directiva**: Cada sección principal debe contar con al menos un comando CLI ejecutable, plantilla de prompt o snippet de código ilustrativo.
3. **Compresión Semántica (Densidad > Volumen)**: El nuevo archivo debe eliminar prosa pasiva y redundancias explicativas. El objetivo es maximizar la señal operativa por token invertido.
4. **Aislamiento Estricto de Mutación**: No modificar archivos de dependencias ni código de aplicación fuera de la habilidad auditada (`SKILL.md`, plantillas asociadas o bitácora de revisión).

---

## 3. Flujo de Trabajo en 4 Fases

### Fase 1: Lectura y Diagnóstico de Brechas
1. Leer el archivo `SKILL.md` objetivo en su totalidad.
2. Identificar debilidades: triggers ausentes o en prosa descriptiva, instrucciones vagas, falta de delimitación de alcance (Cuándo NO usar) o ausencia de Completion Gate.

### Fase 2: Reescritura Aplicando Progressive Disclosure
1. Mantener el núcleo de enrutamiento y contratos en `SKILL.md` compacto ($\le$ 100–140 líneas).
2. Si el contenido requiere conocimiento enciclopédico o guías extensas, desacoplarlas en carpetas modulares (`references/`, `templates/`, `scripts/`).
3. Formatear la cabecera YAML con metadatos estandarizados (`name`, `description`, `triggers`, `context_policy`, `requires`, `produces`).

### Fase 3: Evaluación Bajo Rúbrica Formal (1 a 5)
Calificar la versión reescrita según la siguiente escala:
- **5 (Excepcional):** Instrucciones 100% específicas, ejemplos ejecutables en cada sección, reducción de ruido de tokens y Completion Gate con estados explícitos (`COMPLETE`, `BLOCKED`, `FAILED`).
- **4 (Sólido):** Notablemente más accionable, ejemplos claros y gate estructurado; mínimas oportunidades secundarias de pulido.
- **3 (Aceptable pero vago):** Mejoras visibles, pero persisten secciones pasivas o comandos incompletos.
- **2 (Apenas superior):** Cambios cosméticos de redacción sin beneficio operativo palpable.
- **1 (Sin mejora o regresión):** Incremento de verbosidad sin ganar claridad ni contratos.

### Fase 4: Persistencia y Cierre
- Si **Score $\ge$ 4**: el borrador pasa a verificación externa (§4). Solo si la verificación externa no regresa, se guardan los cambios en el `SKILL.md` destino y se documenta un resumen de mejoras.
- Si **Score < 4**: Aislar las secciones débiles y reescribirlas focalizadamente.
- **Registro de ablación:** cada instrucción eliminada o comprimida se registra en el reporte con su texto original, su ubicación en el archivo y el motivo de la eliminación. Ese registro es la lista de candidatas para una prueba de ablación posterior con harness2 (baseline vs podado).
- **Límite de Parada**: Detener el bucle tras un máximo de 8 turnos de iteración.

---

## 4. Puerta de Verificación Externa (obligatoria antes de persistir)

La rúbrica propia 1–5 mide calidad de redacción, no comportamiento. Un score $\ge$ 4 es necesario pero **nunca suficiente** para `COMPLETE`. Quien mide no escribe: el loop no puede auto-aprobarse con su propia nota.

1. **Baseline primero:** antes de reescribir, registrar el estado actual del skill afectado: `q-skill-doctor score` (eficiencia / calidad / cobertura) y, si el cambio toca comportamiento, el resultado del evaluador harness2 aplicable.
2. **Re-medir tras la reescritura:** correr `q-skill-doctor score` sobre el skill reescrito. La medición la hace `q-skill-doctor`, nunca este loop. El score externo no debe regresar respecto al baseline.
3. **Si el cambio toca comportamiento** (no solo prosa): correr además el evaluador harness2 aplicable (`evals/harness2/evaluator.py` como mínimo; stress / concurrencia / recovery / chaos según el skill). Debe pasar sin `tampered`.
4. **Si la verificación externa regresa, no mejora o no pudo ejecutarse:** NO persistir. El borrador se conserva como propuesta en el reporte, el estado es `[BLOCKED: external-check]` y el caso vuelve a `q-skill-doctor` con la evidencia. La nota propia $\ge$ 4 no rescata un bloqueo externo.

---

## 🏁 Completion Gate

El estado de la optimización del skill debe reportarse con una de las siguientes etiquetas:
- `[x] COMPLETE`: Calificación $\ge$ 4 obtenida, verificación externa superada, archivo `SKILL.md` persistido y validado contra los 4 estándares de calidad.
- `[BLOCKED: external-check]`: Calificación $\ge$ 4 obtenida pero la verificación externa regresó, no mejoró o no pudo ejecutarse; borrador conservado como propuesta, sin persistir.
- `[FAILED: motivo]`: Puntuación inferior a 4 tras agotar los 8 turnos máximos de iteración o incompatibilidad de diseño.

### Checklist de Validación:
- [ ] Skill objetivo auditado y debilidades diagnosticadas
- [ ] Triggers y metadatos estructurados a nivel raíz del YAML
- [ ] Directivas formuladas de forma imperativa y determinista
- [ ] Al menos un ejemplo concreto por sección operativa
- [ ] Completion Gate determinista (`COMPLETE / BLOCKED / FAILED`) incorporado
- [ ] Evaluación formal de rúbrica $\ge$ 4 documentada
- [ ] Verificación externa superada: `q-skill-doctor score` no regresa respecto al baseline y, si el cambio toca comportamiento, el evaluador harness2 aplicable pasa sin `tampered`; en caso contrario el estado es `[BLOCKED: external-check]`
- [ ] Registro de ablación: cada instrucción eliminada o comprimida documentada con texto original, ubicación y motivo
